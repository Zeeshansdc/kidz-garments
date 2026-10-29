import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import QUEUE_FILE, BASE_DIR
import fb_api

logger = logging.getLogger("QueueManager")


def load_queue() -> List[Dict[str, Any]]:
    """Load the current post queue from JSON file."""
    if not QUEUE_FILE.exists():
        save_queue([])
        return []
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading queue file: {e}")
        return []


def save_queue(queue_data: List[Dict[str, Any]]) -> None:
    """Save the post queue to JSON file."""
    temp_file = QUEUE_FILE.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=2, ensure_ascii=False)
    temp_file.replace(QUEUE_FILE)


def add_post_to_queue(
    message: str,
    images: Optional[List[str]] = None,
    scheduled_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a new post item to the queue.
    scheduled_time format: "YYYY-MM-DD HH:MM" (local time) or None for next queue run.
    """
    queue = load_queue()
    new_id = len(queue) + 1

    post_item = {
        "id": new_id,
        "message": message,
        "images": images or [],
        "scheduled_time": scheduled_time,  # e.g., "2026-10-29 18:00"
        "status": "pending",               # pending | published | failed
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "published_at": None,
        "facebook_post_id": None,
        "error": None
    }
    queue.append(post_item)
    save_queue(queue)
    return post_item


def process_queue() -> Dict[str, int]:
    """
    Checks the queue and publishes posts that are ready.
    Returns counts: {'processed': count, 'published': count, 'failed': count, 'skipped': count}
    """
    queue = load_queue()
    stats = {"processed": 0, "published": 0, "failed": 0, "skipped": 0}
    now = datetime.now()

    updated = False

    for item in queue:
        if item.get("status") != "pending":
            continue

        sched_str = item.get("scheduled_time")
        if sched_str:
            try:
                # Support "YYYY-MM-DD HH:MM" or "YYYY-MM-DD HH:MM:SS"
                fmt = "%Y-%m-%d %H:%M:%S" if len(sched_str.strip()) > 16 else "%Y-%m-%d %H:%M"
                sched_dt = datetime.strptime(sched_str.strip(), fmt)
                if now < sched_dt:
                    stats["skipped"] += 1
                    continue  # Not time yet
            except ValueError:
                # If invalid format, proceed to publish
                pass

        stats["processed"] += 1
        msg = item.get("message", "")
        raw_images = item.get("images", [])

        # Resolve relative image paths to BASE_DIR if needed
        resolved_images = []
        for img in raw_images:
            p = Path(img)
            if not p.is_absolute():
                p = BASE_DIR / p
            resolved_images.append(str(p))

        try:
            print(f"[*] Publishing Queue Item #{item['id']}...")
            if not resolved_images:
                res = fb_api.post_text(msg)
            elif len(resolved_images) == 1:
                res = fb_api.post_single_photo(msg, resolved_images[0])
            else:
                res = fb_api.post_multi_photo(msg, resolved_images)

            item["status"] = "published"
            item["published_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            item["facebook_post_id"] = res.get("id") or res.get("post_id")
            item["error"] = None
            stats["published"] += 1
            updated = True
            print(f"[SUCCESS] Item #{item['id']} published successfully! (ID: {item['facebook_post_id']})")
        except Exception as e:
            item["status"] = "failed"
            item["error"] = str(e)
            stats["failed"] += 1
            updated = True
            print(f"[ERROR] Item #{item['id']} failed: {e}")

    if updated:
        save_queue(queue)

    return stats
