"""
smtp_pool_manager.py - Central orchestrator for the multi-SMTP account pool.

Responsibilities:
- Load and filter active SMTP accounts
- Apply sending strategies (round_robin, random, least_used, weighted)
- Enforce daily/hourly rate limits
- Handle warm-up schedules
- Track sending statistics
- Auto-block accounts after consecutive failures
"""

import random
from datetime import datetime, date, timedelta
from typing import Optional, List

from sqlmodel import Session, select

from app.models.smtp_account import SMTPAccount
from app.core.settings import settings
from app.core.constants import (
    SMTP_AUTO_BLOCK_THRESHOLD,
    SMTP_STRATEGIES,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SMTPPoolManager:
    """
    Manages the pool of SMTP accounts and selects the best one for sending.
    Supports pluggable strategies: round_robin, random, least_used, weighted.
    """

    def __init__(self):
        self._round_robin_index = 0

    def reset_counters(self, session: Session) -> None:
        """
        Reset daily and hourly counters for all accounts where the reset period has elapsed.
        Called before every account selection to ensure counters are fresh.
        """
        now = datetime.utcnow()
        today = now.date()
        current_hour_start = now.replace(minute=0, second=0, microsecond=0)

        accounts = session.exec(
            select(SMTPAccount).where(SMTPAccount.status.in_(["active", "paused"]))
        ).all()

        for account in accounts:
            updated = False

            # Reset daily counter if the date has changed
            if account.last_reset_date is None or account.last_reset_date < today:
                if account.sent_today > 0:
                    logger.info(
                        f"Resetting daily counter for SMTP account '{account.name}' "
                        f"(was {account.sent_today})"
                    )
                account.sent_today = 0
                account.last_reset_date = today
                updated = True

            # Reset hourly counter if the hour has changed
            if (
                account.last_hour_reset is None
                or account.last_hour_reset < current_hour_start
            ):
                if account.sent_this_hour > 0:
                    logger.debug(
                        f"Resetting hourly counter for SMTP account '{account.name}' "
                        f"(was {account.sent_this_hour})"
                    )
                account.sent_this_hour = 0
                account.last_hour_reset = current_hour_start
                updated = True

            if updated:
                session.add(account)

        session.commit()

    def get_warmup_limit(self, account: SMTPAccount) -> int:
        """
        Calculate the effective daily limit for an account in warm-up mode.

        Warm-up ramp:
            Day 1 -> warmup_daily_increment (e.g. 20)
            Day 2 -> 2 * warmup_daily_increment (e.g. 40)
            Day 3 -> 3 * warmup_daily_increment (e.g. 60)
            ...until daily_limit is reached, then warm-up is complete.
        """
        if not account.warmup_enabled or not account.warmup_start_date:
            return account.daily_limit

        days_since_start = (date.today() - account.warmup_start_date).days + 1
        warmup_limit = days_since_start * account.warmup_daily_increment

        if warmup_limit >= account.daily_limit:
            # Warm-up complete
            return account.daily_limit

        return warmup_limit

    def _get_eligible_accounts(self, session: Session) -> List[SMTPAccount]:
        """
        Load active accounts and filter out those that have exceeded their limits.
        """
        # Step 1: Reset stale counters
        self.reset_counters(session)

        # Step 2: Load all active accounts
        accounts = session.exec(
            select(SMTPAccount).where(SMTPAccount.status == "active")
        ).all()

        if not accounts:
            return []

        # Step 3: Filter by rate limits and warm-up ceilings
        eligible = []
        for account in accounts:
            effective_daily_limit = self.get_warmup_limit(account)

            if account.sent_today >= effective_daily_limit:
                logger.debug(
                    f"SMTP '{account.name}' skipped: daily limit reached "
                    f"({account.sent_today}/{effective_daily_limit})"
                )
                continue

            if account.sent_this_hour >= account.hourly_limit:
                logger.debug(
                    f"SMTP '{account.name}' skipped: hourly limit reached "
                    f"({account.sent_this_hour}/{account.hourly_limit})"
                )
                continue

            eligible.append(account)

        return eligible

    def get_available_account(
        self,
        session: Session,
        strategy: Optional[str] = None,
        exclude_ids: Optional[List[int]] = None,
    ) -> Optional[SMTPAccount]:
        """
        Select the best SMTP account based on the configured strategy.

        Args:
            session: Database session
            strategy: Override the default strategy (from settings)
            exclude_ids: Account IDs to skip (used during failover retries)

        Returns:
            The selected SMTPAccount, or None if no eligible accounts exist.
        """
        strategy = strategy or settings.SMTP_STRATEGY

        if strategy not in SMTP_STRATEGIES:
            logger.warning(f"Unknown SMTP strategy '{strategy}', falling back to 'least_used'")
            strategy = "least_used"

        eligible = self._get_eligible_accounts(session)

        # Filter out excluded accounts (used during retries)
        if exclude_ids:
            eligible = [a for a in eligible if a.id not in exclude_ids]

        if not eligible:
            logger.warning("No eligible SMTP accounts available in the pool.")
            return None

        # Apply strategy
        if strategy == "round_robin":
            return self._round_robin(eligible)
        elif strategy == "random":
            return self._random(eligible)
        elif strategy == "least_used":
            return self._least_used(eligible)
        elif strategy == "weighted":
            return self._weighted(eligible)
        else:
            return self._least_used(eligible)

    def _round_robin(self, accounts: List[SMTPAccount]) -> SMTPAccount:
        """Cycle through accounts in order of last_sent_at (least recent first)."""
        sorted_accounts = sorted(
            accounts,
            key=lambda a: a.last_sent_at or datetime.min,
        )
        return sorted_accounts[0]

    def _random(self, accounts: List[SMTPAccount]) -> SMTPAccount:
        """Randomly select from eligible accounts."""
        return random.choice(accounts)

    def _least_used(self, accounts: List[SMTPAccount]) -> SMTPAccount:
        """Select the account with the lowest sent_today count."""
        return min(accounts, key=lambda a: a.sent_today)

    def _weighted(self, accounts: List[SMTPAccount]) -> SMTPAccount:
        """
        Weighted random selection using priority as weight.
        Higher priority = more likely to be selected.
        """
        weights = [max(a.priority, 1) for a in accounts]
        return random.choices(accounts, weights=weights, k=1)[0]

    def mark_sent(self, session: Session, account_id: int) -> None:
        """
        Record a successful send for the given SMTP account.
        Resets failure_count on success.
        """
        account = session.get(SMTPAccount, account_id)
        if not account:
            logger.warning(f"mark_sent: SMTP account {account_id} not found.")
            return

        account.sent_today += 1
        account.sent_this_hour += 1
        account.total_sent += 1
        account.failure_count = 0
        account.last_sent_at = datetime.utcnow()
        account.updated_at = datetime.utcnow()

        session.add(account)
        session.commit()

        logger.debug(
            f"SMTP '{account.name}' send recorded. "
            f"Today: {account.sent_today}/{self.get_warmup_limit(account)}, "
            f"Hour: {account.sent_this_hour}/{account.hourly_limit}"
        )

    def mark_failed(
        self,
        session: Session,
        account_id: int,
        error: Optional[str] = None,
    ) -> None:
        """
        Record a failed send attempt.
        Auto-blocks the account after SMTP_AUTO_BLOCK_THRESHOLD consecutive failures.
        """
        account = session.get(SMTPAccount, account_id)
        if not account:
            logger.warning(f"mark_failed: SMTP account {account_id} not found.")
            return

        account.failure_count += 1
        account.total_failed += 1
        account.updated_at = datetime.utcnow()

        if account.failure_count >= SMTP_AUTO_BLOCK_THRESHOLD:
            account.status = "blocked"
            logger.error(
                f"SMTP '{account.name}' AUTO-BLOCKED after {account.failure_count} "
                f"consecutive failures. Last error: {error}"
            )
        else:
            logger.warning(
                f"SMTP '{account.name}' failure #{account.failure_count}. "
                f"Error: {error}"
            )

        session.add(account)
        session.commit()

    def get_pool_stats(self, session: Session) -> dict:
        """Get aggregate statistics for the entire SMTP pool."""
        all_accounts = session.exec(select(SMTPAccount)).all()

        if not all_accounts:
            return {
                "total_accounts": 0,
                "active_accounts": 0,
                "paused_accounts": 0,
                "blocked_accounts": 0,
                "disabled_accounts": 0,
                "total_sent_today": 0,
                "total_remaining_today": 0,
                "total_daily_capacity": 0,
                "accounts_at_limit": 0,
            }

        active = [a for a in all_accounts if a.status == "active"]
        total_sent_today = sum(a.sent_today for a in all_accounts)
        total_daily_capacity = sum(self.get_warmup_limit(a) for a in active)

        return {
            "total_accounts": len(all_accounts),
            "active_accounts": len(active),
            "paused_accounts": len([a for a in all_accounts if a.status == "paused"]),
            "blocked_accounts": len([a for a in all_accounts if a.status == "blocked"]),
            "disabled_accounts": len([a for a in all_accounts if a.status == "disabled"]),
            "total_sent_today": total_sent_today,
            "total_remaining_today": max(0, total_daily_capacity - total_sent_today),
            "total_daily_capacity": total_daily_capacity,
            "accounts_at_limit": len(
                [a for a in active if a.sent_today >= self.get_warmup_limit(a)]
            ),
        }


# Export singleton instance
smtp_pool = SMTPPoolManager()
