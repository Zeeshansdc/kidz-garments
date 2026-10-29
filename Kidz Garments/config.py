import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "").strip()
PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "").strip()
GRAPH_API_VERSION = "v21.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

QUEUE_FILE = BASE_DIR / "queue.json"
IMAGES_DIR = BASE_DIR / "images"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
IMAGES_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


def is_configured() -> bool:
    """Check if Page ID and Access Token are configured."""
    return bool(
        PAGE_ID
        and PAGE_ACCESS_TOKEN
        and PAGE_ID != "your_facebook_page_id_here"
        and PAGE_ACCESS_TOKEN != "your_facebook_page_access_token_here"
    )
