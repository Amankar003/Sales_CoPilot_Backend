"""
campaign_pipeline.py - Orchestrates the automated background campaign workflow.
"""

import httpx
import re
import asyncio
from datetime import datetime
from sqlmodel import Session, select

from app.database.db import engine
from app.models.campaign import Campaign
from app.models.business import Business
from app.models.audit import Audit
from app.models.report import Report
from app.models.outreach import Outreach
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def run_campaign_pipeline(campaign_id: int, request_data: dict):
    """
    Background worker function that executes the full campaign discovery and automation pipeline.
    """
    logger.info(f"Starting pipeline task for Campaign {campaign_id}")
    
    # 1. Reset campaign status and counters
    with Session(engine) as session:
        campaign = session.get(Campaign, campaign_id)
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found in database. Aborting pipeline.")
            return
            
        campaign.status = "discovering"
        campaign.pipeline_error = None
        campaign.leads_count = 0
        campaign.enriched_count = 0
        campaign.audited_count = 0
        campaign.reports_count = 0
        campaign.outreach_count = 0
        campaign.updated_at = datetime.utcnow()
        session.add(campaign)
        session.commit()
        session.refresh(campaign)

    # Extract pipeline options
    auto_enrich = request_data.get("auto_enrich", True)
    auto_audit = request_data.get("auto_audit", True)
    auto_generate_reports = request_data.get("auto_generate_reports", True)
    auto_generate_outreach = request_data.get("auto_generate_outreach", True)
    max_runtime_seconds = request_data.get("max_runtime_seconds", 120)

    has_pipeline_errors = False

    # --- STEP 1: DISCOVER LEADS ---
    try:
        from app.services.discovery.business_collector import discover_businesses
        
        with Session(engine) as session:
            new_leads = await discover_businesses(
                sector=campaign.sector,
                location=campaign.location,
                campaign_id=campaign.id,
                max_runtime_seconds=max_runtime_seconds,
                session=session,
            )
            
            # Refresh campaign instance
            campaign = session.get(Campaign, campaign_id)
            campaign.leads_count = len(new_leads)
            
            if len(new_leads) == 0:
                campaign.status = "completed"
                session.add(campaign)
                session.commit()
                logger.info(f"Campaign {campaign_id} found 0 leads. Pipeline complete.")
                return
                
            session.add(campaign)
            session.commit()
            
    except Exception as e:
        error_msg = f"Discovery step failed: {repr(e)}"
        logger.error(f"[Campaign {campaign_id}] {error_msg}")
        with Session(engine) as session:
            campaign = session.get(Campaign, campaign_id)
            if campaign:
                campaign.status = "failed"
                campaign.pipeline_error = error_msg
                session.add(campaign)
                session.commit()
        return

    # Fetch all business IDs created for this campaign
    with Session(engine) as session:
        businesses = session.exec(
            select(Business).where(Business.campaign_id == campaign_id)
        ).all()
        business_ids = [b.id for b in businesses]

    # --- STEP 2: BUSINESS ENRICHMENT ---
    if auto_enrich and business_ids:
        logger.info(f"[Campaign {campaign_id}] Starting business enrichment step...")
        with Session(engine) as session:
            campaign = session.get(Campaign, campaign_id)
            campaign.status = "enriching"
            campaign.updated_at = datetime.utcnow()
            session.add(campaign)
            session.commit()

        from app.services.enrichment.website_finder import find_website
        from app.services.enrichment.social_finder import find_social_profiles

        for bid in business_ids:
            try:
                with Session(engine) as session:
                    business = session.get(Business, bid)
                    if not business:
                        continue

                    # Find website if missing
                    if not business.website:
                        found_web = await find_website(business.name, business.location)
                        if found_web:
                            business.website = found_web
                            session.add(business)
                            session.commit()
                            session.refresh(business)

                    # Extract emails and social links from homepage
                    if business.website:
                        try:
                            async with httpx.AsyncClient(
                                follow_redirects=True,
                                timeout=10.0,
                                verify=False,
                            ) as client:
                                resp = await client.get(business.website)
                                if resp.status_code == 200:
                                    html = resp.text
                                    
                                    # Extract email addresses via regex
                                    raw_emails = re.findall(
                                        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}', html
                                    )
                                    extracted_emails = []
                                    for email in raw_emails:
                                        email_lower = email.strip().lower()
                                        if not any(
                                            ext in email_lower
                                            for ext in [
                                                ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
                                                "w3.org", "sentry.io", "google.com", "example.com",
                                                "yourdomain.com", "bootstrap", "font", "css"
                                            ]
                                        ):
                                            extracted_emails.append(email_lower)

                                    if extracted_emails and not business.email:
                                        business.email = extracted_emails[0]

                                    # Extract socials
                                    socials = await find_social_profiles(
                                        business.name, business.location, html
                                    )
                                    if socials.get("instagram") and not business.instagram:
                                        business.instagram = socials["instagram"]
                                    if socials.get("facebook") and not business.facebook:
                                        business.facebook = socials["facebook"]
                                    if socials.get("linkedin") and not business.linkedin:
                                        business.linkedin = socials["linkedin"]

                                    session.add(business)
                                    session.commit()
                        except Exception as web_err:
                            logger.warning(f"Enrichment: failed to fetch homepage {business.website}: {web_err}")

                    # Increment campaign counter
                    campaign = session.get(Campaign, campaign_id)
                    campaign.enriched_count += 1
                    session.add(campaign)
                    session.commit()
            except Exception as e:
                logger.error(f"[Campaign {campaign_id}] Enrichment failed for business {bid}: {e}")
                has_pipeline_errors = True

    # --- STEP 3: WEBSITE AUDITS ---
    if auto_audit and business_ids:
        logger.info(f"[Campaign {campaign_id}] Starting audits step...")
        with Session(engine) as session:
            campaign = session.get(Campaign, campaign_id)
            campaign.status = "auditing"
            campaign.updated_at = datetime.utcnow()
            session.add(campaign)
            session.commit()

        from app.services.audit.audit_orchestrator import run_full_audit

        for bid in business_ids:
            try:
                with Session(engine) as session:
                    business = session.get(Business, bid)
                    if not business:
                        continue
                    
                    # Run full audit (deletes old audit dynamically)
                    await run_full_audit(business, session)

                    campaign = session.get(Campaign, campaign_id)
                    campaign.audited_count += 1
                    session.add(campaign)
                    session.commit()
            except Exception as e:
                logger.error(f"[Campaign {campaign_id}] Audit failed for business {bid}: {e}")
                has_pipeline_errors = True

    # --- STEP 4: REPORT GENERATION ---
    if auto_generate_reports and business_ids:
        logger.info(f"[Campaign {campaign_id}] Starting report generation step...")
        with Session(engine) as session:
            campaign = session.get(Campaign, campaign_id)
            campaign.status = "generating_reports"
            campaign.updated_at = datetime.utcnow()
            session.add(campaign)
            session.commit()

        from app.services.report.report_generator import generate_report

        for bid in business_ids:
            try:
                with Session(engine) as session:
                    business = session.get(Business, bid)
                    if not business:
                        continue

                    # Get latest audit
                    audit = session.exec(
                        select(Audit)
                        .where(Audit.business_id == bid)
                        .order_by(Audit.created_at.desc())
                    ).first()

                    if audit:
                        await generate_report(business, audit, session)
                        
                        campaign = session.get(Campaign, campaign_id)
                        campaign.reports_count += 1
                        session.add(campaign)
                        session.commit()
                    else:
                        logger.warning(f"[Campaign {campaign_id}] Business {bid} has no audit. Skipping report.")
            except Exception as e:
                logger.error(f"[Campaign {campaign_id}] Report failed for business {bid}: {e}")
                has_pipeline_errors = True

    # --- STEP 5: OUTREACH GENERATION ---
    if auto_generate_outreach and business_ids:
        logger.info(f"[Campaign {campaign_id}] Starting outreach generation step...")
        with Session(engine) as session:
            campaign = session.get(Campaign, campaign_id)
            campaign.status = "generating_outreach"
            campaign.updated_at = datetime.utcnow()
            session.add(campaign)
            session.commit()

        from app.services.outreach.email_generator import generate_email_content
        from app.services.outreach.whatsapp_generator import generate_whatsapp_content
        from app.services.outreach.call_notes_generator import generate_call_script_notes
        from app.services.outreach.pitch_generator import generate_pitch_content

        for bid in business_ids:
            try:
                with Session(engine) as session:
                    business = session.get(Business, bid)
                    if not business:
                        continue

                    audit = session.exec(
                        select(Audit)
                        .where(Audit.business_id == bid)
                        .order_by(Audit.created_at.desc())
                    ).first()

                    # Clean up existing outreach
                    existing_outreach = session.exec(
                        select(Outreach).where(Outreach.business_id == bid)
                    ).first()
                    if existing_outreach:
                        session.delete(existing_outreach)
                        session.commit()

                    # Generate outreach models
                    email_task = generate_email_content(business, audit)
                    whatsapp_task = generate_whatsapp_content(business)
                    call_task = generate_call_script_notes(business, audit)
                    pitch_task = generate_pitch_content(business, audit)

                    email_content, whatsapp, call_notes, pitch = await asyncio.gather(
                        email_task, whatsapp_task, call_task, pitch_task
                    )

                    outreach = Outreach(
                        business_id=bid,
                        audit_id=audit.id if audit else None,
                        email_subject=email_content.get("subject"),
                        email_body=email_content.get("body"),
                        whatsapp_message=whatsapp,
                        call_notes=call_notes,
                        meeting_pitch=pitch,
                    )
                    session.add(outreach)
                    session.commit()

                    campaign = session.get(Campaign, campaign_id)
                    campaign.outreach_count += 1
                    session.add(campaign)
                    session.commit()
            except Exception as e:
                logger.error(f"[Campaign {campaign_id}] Outreach failed for business {bid}: {e}")
                has_pipeline_errors = True

    # --- STEP 6: FINALIZE PIPELINE ---
    with Session(engine) as session:
        campaign = session.get(Campaign, campaign_id)
        if campaign:
            if has_pipeline_errors:
                campaign.status = "completed_with_errors"
                campaign.pipeline_error = "Encountered processing errors for some leads in the pipeline. Check console logs."
            else:
                campaign.status = "completed"
            campaign.updated_at = datetime.utcnow()
            session.add(campaign)
            session.commit()
            
    logger.info(f"Pipeline finished for Campaign {campaign_id}. Final status: {campaign.status}")
