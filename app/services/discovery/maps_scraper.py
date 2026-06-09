"""
maps_scraper.py - Simulates Google Maps-like scraping with mock data fallback.
Uses DuckDuckGo search to find businesses in India.
"""

import random
from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Mock Indian businesses for fallback discovery
MOCK_BUSINESSES = {
    "hospital": [
        {"name": "Max Super Speciality Hospital", "rating": 4.3, "reviews": 2850},
        {"name": "Fortis Hospital", "rating": 4.1, "reviews": 1920},
        {"name": "Apollo Hospital", "rating": 4.4, "reviews": 3100},
        {"name": "Medanta - The Medicity", "rating": 4.2, "reviews": 2650},
        {"name": "Artemis Hospital", "rating": 4.0, "reviews": 1800},
        {"name": "BLK Super Speciality Hospital", "rating": 3.9, "reviews": 1500},
        {"name": "Sir Ganga Ram Hospital", "rating": 4.1, "reviews": 2200},
        {"name": "Jaypee Hospital", "rating": 3.8, "reviews": 1100},
        {"name": "Yatharth Hospital", "rating": 4.0, "reviews": 890},
        {"name": "Sharda Hospital", "rating": 3.7, "reviews": 650},
    ],
    "restaurant": [
        {"name": "Bukhara - ITC Maurya", "rating": 4.6, "reviews": 4200},
        {"name": "Indian Accent", "rating": 4.5, "reviews": 3800},
        {"name": "Karim's", "rating": 4.3, "reviews": 5600},
        {"name": "Moti Mahal Delux", "rating": 4.1, "reviews": 2900},
        {"name": "Paranthe Wali Gali", "rating": 4.0, "reviews": 3200},
        {"name": "Haldiram's", "rating": 4.2, "reviews": 6100},
        {"name": "Bikanervala", "rating": 4.0, "reviews": 4500},
        {"name": "Saravana Bhavan", "rating": 4.3, "reviews": 3600},
        {"name": "Punjab Grill", "rating": 4.1, "reviews": 2100},
        {"name": "Sagar Ratna", "rating": 3.9, "reviews": 1800},
    ],
    "school": [
        {"name": "Delhi Public School", "rating": 4.4, "reviews": 1200},
        {"name": "Ryan International School", "rating": 4.0, "reviews": 890},
        {"name": "Amity International School", "rating": 4.2, "reviews": 750},
        {"name": "Lotus Valley International School", "rating": 4.3, "reviews": 620},
        {"name": "The Heritage School", "rating": 4.1, "reviews": 540},
        {"name": "Pathways World School", "rating": 4.5, "reviews": 480},
        {"name": "Sanskriti School", "rating": 4.3, "reviews": 670},
        {"name": "Shiv Nadar School", "rating": 4.4, "reviews": 510},
        {"name": "G.D. Goenka Public School", "rating": 4.0, "reviews": 430},
        {"name": "DAV Public School", "rating": 3.9, "reviews": 380},
    ],
    "gym": [
        {"name": "Gold's Gym", "rating": 4.1, "reviews": 1500},
        {"name": "Anytime Fitness", "rating": 4.0, "reviews": 1200},
        {"name": "Cult.fit", "rating": 4.3, "reviews": 2100},
        {"name": "Talwalkars Gym", "rating": 3.8, "reviews": 900},
        {"name": "Fitness First", "rating": 4.2, "reviews": 1100},
        {"name": "Snap Fitness", "rating": 3.9, "reviews": 780},
        {"name": "Muscle & Strength Gym", "rating": 4.0, "reviews": 650},
        {"name": "The Gym", "rating": 3.7, "reviews": 420},
        {"name": "CrossFit Studio", "rating": 4.4, "reviews": 380},
        {"name": "Iron Paradise Gym", "rating": 4.1, "reviews": 550},
    ],
    "salon": [
        {"name": "Looks Salon", "rating": 4.2, "reviews": 1800},
        {"name": "Lakme Salon", "rating": 4.0, "reviews": 2200},
        {"name": "Jawed Habib Hair & Beauty", "rating": 3.9, "reviews": 1600},
        {"name": "VLCC", "rating": 4.1, "reviews": 1900},
        {"name": "Naturals Salon", "rating": 4.0, "reviews": 1400},
        {"name": "Green Trends", "rating": 3.8, "reviews": 1100},
        {"name": "BBlunt Salon", "rating": 4.3, "reviews": 950},
        {"name": "Enrich Salon", "rating": 4.1, "reviews": 820},
        {"name": "Affinity Salon", "rating": 4.2, "reviews": 760},
        {"name": "Jean-Claude Biguine", "rating": 4.4, "reviews": 680},
    ],
    "hotel": [
        {"name": "The Oberoi", "rating": 4.7, "reviews": 3200},
        {"name": "Taj Palace", "rating": 4.6, "reviews": 4100},
        {"name": "ITC Grand Bharat", "rating": 4.5, "reviews": 2800},
        {"name": "The Leela Palace", "rating": 4.6, "reviews": 3500},
        {"name": "Radisson Blu Hotel", "rating": 4.2, "reviews": 2100},
        {"name": "Hyatt Regency", "rating": 4.3, "reviews": 1900},
        {"name": "Holiday Inn", "rating": 4.0, "reviews": 1500},
        {"name": "Crowne Plaza", "rating": 4.1, "reviews": 1700},
        {"name": "Lemon Tree Hotel", "rating": 3.9, "reviews": 1200},
        {"name": "OYO Townhouse", "rating": 3.7, "reviews": 890},
    ],
}

# Generic fallback for categories not in the mock data
GENERIC_MOCK = [
    {"name": "{category} Solutions India", "rating": 4.0, "reviews": 500},
    {"name": "Premier {category} Services", "rating": 3.9, "reviews": 420},
    {"name": "{category} Hub {location}", "rating": 4.1, "reviews": 380},
    {"name": "New Age {category}", "rating": 3.8, "reviews": 310},
    {"name": "{category} World {location}", "rating": 4.2, "reviews": 550},
    {"name": "Star {category} Center", "rating": 3.7, "reviews": 280},
    {"name": "Royal {category} {location}", "rating": 4.0, "reviews": 460},
    {"name": "{category} Plus Services", "rating": 3.9, "reviews": 340},
    {"name": "Global {category} {location}", "rating": 4.1, "reviews": 490},
    {"name": "Metro {category} Center", "rating": 3.8, "reviews": 270},
]

# Sample addresses for mock data
MOCK_ADDRESSES = {
    "Delhi": [
        "Connaught Place, New Delhi",
        "Lajpat Nagar, South Delhi",
        "Karol Bagh, Central Delhi",
        "Rajouri Garden, West Delhi",
        "Dwarka Sector 12, New Delhi",
    ],
    "Noida": [
        "Sector 18, Noida",
        "Sector 62, Noida",
        "Sector 44, Noida",
        "Sector 15, Noida",
        "Greater Noida West",
    ],
    "Gurgaon": [
        "DLF Phase 1, Gurgaon",
        "MG Road, Gurgaon",
        "Sector 29, Gurgaon",
        "Cyber City, Gurgaon",
        "Sohna Road, Gurgaon",
    ],
    "Mumbai": [
        "Andheri West, Mumbai",
        "Bandra Kurla Complex, Mumbai",
        "Lower Parel, Mumbai",
        "Powai, Mumbai",
        "Juhu, Mumbai",
    ],
    "Bangalore": [
        "Koramangala, Bangalore",
        "Indiranagar, Bangalore",
        "Whitefield, Bangalore",
        "MG Road, Bangalore",
        "Electronic City, Bangalore",
    ],
}

# Default addresses for cities not in mock data
DEFAULT_ADDRESSES = [
    "Main Market Area",
    "City Center",
    "Commercial Complex",
    "Industrial Area",
    "Ring Road",
]


def get_mock_businesses(
    sector: str,
    location: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Generate mock business data for a given sector and location.
    Used as fallback when real scraping is not available.
    """
    logger.info(f"Generating mock businesses: {sector} in {location} (limit: {limit})")

    # Find matching mock data
    sector_lower = sector.lower().rstrip("s")  # Remove trailing 's' for matching
    mock_list = MOCK_BUSINESSES.get(sector_lower, None)

    if not mock_list:
        # Use generic template
        mock_list = [
            {
                "name": item["name"].format(category=sector.title(), location=location),
                "rating": item["rating"],
                "reviews": item["reviews"],
            }
            for item in GENERIC_MOCK
        ]

    # Get addresses for location
    addresses = MOCK_ADDRESSES.get(location, DEFAULT_ADDRESSES)

    # Build business data
    businesses = []
    for i, mock in enumerate(mock_list[:limit]):
        phone_suffix = random.randint(1000000, 9999999)
        business = {
            "name": mock["name"],
            "category": sector.title(),
            "location": location,
            "address": addresses[i % len(addresses)] if addresses else f"{location} Area",
            "phone": f"+91 98{phone_suffix}",
            "email": None,
            "website": None,
            "google_rating": mock.get("rating"),
            "reviews_count": mock.get("reviews"),
            "description": f"A well-known {sector.lower()} located in {location}.",
            "source": "discovered",
            "confidence_score": round(random.uniform(0.6, 0.95), 2),
        }
        businesses.append(business)

    logger.info(f"Generated {len(businesses)} mock businesses")
    return businesses
