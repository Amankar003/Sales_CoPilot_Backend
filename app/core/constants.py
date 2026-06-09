"""
constants.py - Application-wide constants.
"""

# Business categories for discovery
BUSINESS_CATEGORIES = [
    "Hospital",
    "Clinic",
    "Restaurant",
    "Cafe",
    "Hotel",
    "School",
    "College",
    "Gym",
    "Salon",
    "Spa",
    "Real Estate",
    "Law Firm",
    "CA Firm",
    "Dentist",
    "Pharmacy",
    "Coaching Center",
    "Interior Designer",
    "Event Planner",
    "Travel Agency",
    "Car Dealer",
    "Jewellery Store",
    "Clothing Store",
    "Electronics Store",
    "Furniture Store",
    "Construction Company",
    "Manufacturing",
    "IT Company",
    "Digital Agency",
    "NGO",
    "Other",
]

# Indian cities for discovery
INDIAN_CITIES = [
    "Delhi",
    "Mumbai",
    "Bangalore",
    "Hyderabad",
    "Chennai",
    "Kolkata",
    "Pune",
    "Ahmedabad",
    "Jaipur",
    "Lucknow",
    "Noida",
    "Gurgaon",
    "Ghaziabad",
    "Faridabad",
    "Chandigarh",
    "Indore",
    "Bhopal",
    "Nagpur",
    "Surat",
    "Vadodara",
    "Kochi",
    "Thiruvananthapuram",
    "Coimbatore",
    "Visakhapatnam",
    "Patna",
    "Ranchi",
    "Dehradun",
    "Amritsar",
    "Ludhiana",
    "Agra",
]

# Audit scoring weights
AUDIT_WEIGHTS = {
    "website": 0.40,  # 40% - website quality
    "seo": 0.25,      # 25% - SEO score
    "social": 0.20,   # 20% - social media presence
    "ux": 0.15,       # 15% - user experience
}

# Maximum audit score
MAX_AUDIT_SCORE = 100

# Default number of leads to discover
DEFAULT_DISCOVERY_LIMIT = 10

# CTA keywords to detect on websites
CTA_KEYWORDS = [
    "book now",
    "schedule",
    "appointment",
    "contact us",
    "get quote",
    "free consultation",
    "call now",
    "enquire",
    "register",
    "sign up",
    "download",
    "buy now",
    "order now",
    "get started",
    "learn more",
    "apply now",
]

# Social media platforms to check
SOCIAL_PLATFORMS = [
    "instagram",
    "facebook",
    "linkedin",
    "twitter",
    "youtube",
]

# Services that can be recommended based on pain points
RECOMMENDABLE_SERVICES = [
    "Website Development",
    "Website Redesign",
    "SEO Optimization",
    "Google My Business Setup",
    "Social Media Management",
    "Content Marketing",
    "PPC / Google Ads",
    "WhatsApp Business Setup",
    "Online Booking System",
    "CRM Implementation",
    "Email Marketing",
    "Reputation Management",
    "Video Marketing",
    "Mobile App Development",
    "Chatbot Integration",
    "E-commerce Setup",
    "Branding & Design",
    "Lead Generation",
    "Marketing Automation",
    "Analytics & Reporting",
]
