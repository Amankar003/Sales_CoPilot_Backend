import asyncio
import logging
from app.services.discovery.business_collector import discover_businesses
from app.database.session import engine
from sqlmodel import Session

logging.basicConfig(level=logging.INFO)

async def test():
    with Session(engine) as session:
        results = await discover_businesses("Hospital", "Noida", 1, 60, session)
        print(f"Total results: {len(results)}")

if __name__ == "__main__":
    asyncio.run(test())
