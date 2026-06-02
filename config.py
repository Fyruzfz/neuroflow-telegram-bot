"""
NeuroFlow AI Telegram Bot - Configuration
Token loaded from .env file or environment variable
"""

import os

# --- Load .env file ---
ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key, value)

# --- Bot Token ---
# CEO: Create bot via @BotFather on Telegram, set token here or in env
BOT_TOKEN = os.environ.get("NEUROFLOW_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# --- Admin (CEO) ---
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0"))

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# --- Pricing (USD) ---
PRICES = {
    "scrape_small": 3,
    "scrape_medium": 7,
    "scrape_large": 15,
    "analyze": 8,
    "content_blog": 10,
    "content_social": 5,
}

# --- Free Tier ---
FREE_SCRAPES = 3

# --- Subscription Plans ---
PLANS = {
    "pro": {
        "name": "Pro",
        "price": 9,
        "scrapes": 50,
        "features": "50 scrapes/month, CSV+JSON+Sheets export, email delivery",
    },
    "business": {
        "name": "Business",
        "price": 29,
        "scrapes": -1,
        "features": "Unlimited scrapes, priority processing, API access, white-label",
    },
}

# --- Payment Methods ---
PAYMENT_METHODS = {
    "binance": {"name": "Binance Pay", "id": "BINANCE_PAY_ID_PLACEHOLDER"},
    "payhere": {"name": "PayHere (Sri Lanka)", "url": "PAYHERE_URL_PLACEHOLDER"},
    "bank": {
        "name": "Bank Transfer (Sampath/HNB)",
        "details": "Account details provided on request",
    },
}

# --- Gumroad Catalog ---
GUMROAD_PRODUCTS = [
    {
        "name": "Ultimate Web Scraper Pack",
        "price": 25,
        "url": "https://neuroflowaii.gumroad.com/l/zmlvut",
        "desc": "10 Python scraper scripts, ready to run",
    },
]

# --- Google Sheets ---
GOOGLE_SHEET_ID = "1B333W_BxqQ6x4Wyc-ODy9DziF57sUyR6ucnqkIHWWr8"
GOOGLE_TOKEN_FILE = os.path.join(
    os.environ.get("LOCALAPPDATA", ""), "hermes", "google_token.json"
)

# --- Ensure directories exist ---
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
