import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

from config import GRAPH_API_BASE, PAGE_ID, PAGE_ACCESS_TOKEN, LOGS_DIR

# Set up logging
logger = logging.getLogger("FacebookAPI")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(LOGS_DIR / "facebook_api.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
if not logger.handlers:
    logger.addHandler(file_handler)


class FacebookAPIError(Exception):
    """Custom exception for Facebook API errors with clear user feedback."""
    def __init__(self, message: str, code: Optional[int] = None, subcode: Optional[int] = None):
        super().__init__(message)
        self.code = code
        self.subcode = subcode


def _parse_error_response(response: requests.Response) -> FacebookAPIError:
    """Extract descriptive error message from Facebook Graph API response."""
    try:
        data = response.json()
        error_info = data.get("error", {})
        message = error_info.get("message", response.text)
        code = error_info.get("code")
        subcode = error_info.get("error_subcode")
        type_ = error_info.get("type", "OAuthException")
        
        hint = ""
        if code in (190, 102):
            hint = " (Your Access Token appears expired or invalid. Please generate a new Page Access Token.)"
        elif code == 200:
            hint = " (Permission error: Ensure the token has 'pages_manage_posts' and 'pages_read_engagement' permissions.)"
        elif code == 100:
            hint = " (Invalid parameter: check your Page ID or post payload.)"

        return FacebookAPIError(f"[{type_} code {code}] {message}{hint}", code=code, subcode=subcode)
    except Exception:
        return FacebookAPIError(f"HTTP {response.status_code}: {response.text}")


def verify_connection() -> Dict[str, Any]:
    """Verify that credentials can access the target Facebook Page."""
    if not PAGE_ID or not PAGE_ACCESS_TOKEN:
        raise FacebookAPIError("Missing Page ID or Access Token in .env file.")

    url = f"{GRAPH_API_BASE}/{PAGE_ID}"
    params = {
        "fields": "id,name,link,category",
        "access_token": PAGE_ACCESS_TOKEN,
    }

    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code != 200:
            raise _parse_error_response(res)
        data = res.json()
        logger.info(f"Verified connection to page: {data.get('name')} (ID: {data.get('id')})")
        return data
    except requests.RequestException as e:
        logger.error(f"Network error verifying credentials: {e}")
        raise FacebookAPIError(f"Network connection failed: {e}")


def post_text(message: str) -> Dict[str, Any]:
    """Publish a status / text post to the Facebook Page feed."""
    if not message.strip():
        raise ValueError("Post message cannot be empty.")

    url = f"{GRAPH_API_BASE}/{PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": PAGE_ACCESS_TOKEN,
    }

    try:
        res = requests.post(url, data=payload, timeout=20)
        if res.status_code != 200:
            raise _parse_error_response(res)
        data = res.json()
        logger.info(f"Published text post. Post ID: {data.get('id')}")
        return data
    except requests.RequestException as e:
        logger.error(f"Failed to publish text post: {e}")
        raise FacebookAPIError(f"Network error while publishing post: {e}")


def post_single_photo(message: str, image_path_or_url: str) -> Dict[str, Any]:
    """
    Publish a single photo with a caption to the Facebook Page.
    Accepts either a local file path or a public web image URL.
    """
    url = f"{GRAPH_API_BASE}/{PAGE_ID}/photos"

    path_obj = Path(image_path_or_url)
    is_local_file = path_obj.exists() and path_obj.is_file()

    try:
        if is_local_file:
            with open(path_obj, "rb") as img_file:
                files = {"source": img_file}
                payload = {
                    "message": message,
                    "access_token": PAGE_ACCESS_TOKEN,
                }
                res = requests.post(url, data=payload, files=files, timeout=45)
        else:
            # Treat as public image URL
            payload = {
                "url": image_path_or_url,
                "message": message,
                "access_token": PAGE_ACCESS_TOKEN,
            }
            res = requests.post(url, data=payload, timeout=30)

        if res.status_code != 200:
            raise _parse_error_response(res)
        data = res.json()
        logger.info(f"Published photo post. ID: {data.get('id')} / Post ID: {data.get('post_id')}")
        return data
    except requests.RequestException as e:
        logger.error(f"Failed to publish photo post: {e}")
        raise FacebookAPIError(f"Network error while uploading photo: {e}")


def post_multi_photo(message: str, image_paths: List[str]) -> Dict[str, Any]:
    """
    Publish an album post with multiple photos and a shared caption.
    Uploads each photo unpublished first, then attaches them to a single feed post.
    """
    if not image_paths:
        return post_text(message)

    if len(image_paths) == 1:
        return post_single_photo(message, image_paths[0])

    photo_ids = []
    upload_url = f"{GRAPH_API_BASE}/{PAGE_ID}/photos"

    for img in image_paths:
        path_obj = Path(img)
        if not path_obj.exists():
            raise FileNotFoundError(f"Local image not found: {img}")

        with open(path_obj, "rb") as img_file:
            files = {"source": img_file}
            payload = {
                "published": "false",
                "access_token": PAGE_ACCESS_TOKEN,
            }
            res = requests.post(upload_url, data=payload, files=files, timeout=45)
            if res.status_code != 200:
                raise _parse_error_response(res)
            photo_data = res.json()
            photo_ids.append(photo_data["id"])

    # Now create feed post with attached media
    feed_url = f"{GRAPH_API_BASE}/{PAGE_ID}/feed"
    payload = {
        "message": message,
        "access_token": PAGE_ACCESS_TOKEN,
    }
    for i, pid in enumerate(photo_ids):
        payload[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})

    res = requests.post(feed_url, data=payload, timeout=30)
    if res.status_code != 200:
        raise _parse_error_response(res)
    data = res.json()
    logger.info(f"Published multi-photo album post. ID: {data.get('id')}")
    return data
