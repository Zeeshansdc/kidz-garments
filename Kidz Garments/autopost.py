import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import config
import fb_api
import queue_manager


def print_banner():
    print("=" * 60)
    print("        KIDZ GARMENTS - FACEBOOK PAGE AUTOMATION        ")
    print("=" * 60)


def verify_setup():
    """Verify credentials and connectivity."""
    print("\n[*] Verifying connection to Facebook Graph API...")
    if not config.is_configured():
        print("\n[!] Setup required:")
        print("    Your FACEBOOK_PAGE_ID or FACEBOOK_PAGE_ACCESS_TOKEN is missing.")
        print("    Please edit the '.env' file in this folder and add your credentials.")
        print("    See README.md for instructions on getting your free access token.")
        return False

    try:
        page = fb_api.verify_connection()
        print("\n[SUCCESS] Connection Successful!")
        print(f"    Page Name:     {page.get('name')}")
        print(f"    Page ID:       {page.get('id')}")
        print(f"    Category:      {page.get('category', 'N/A')}")
        if page.get("link"):
            print(f"    Page Link:     {page.get('link')}")
        return True
    except fb_api.FacebookAPIError as e:
        print(f"\n[ERROR] Facebook API Error: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected Error: {e}")
        return False


def post_now_interactive():
    print("\n--- Create Instant Post ---")
    message = input("Enter post caption / message: ").strip()
    if not message:
        print("[!] Caption cannot be empty.")
        return

    img_input = input("Image path or URL (optional, press Enter to skip): ").strip()
    try:
        print("\n[*] Publishing to Facebook Page...")
        if img_input:
            res = fb_api.post_single_photo(message, img_input)
            print(f"[SUCCESS] Published photo post successfully! ID: {res.get('id')}")
        else:
            res = fb_api.post_text(message)
            print(f"[SUCCESS] Published text post successfully! ID: {res.get('id')}")
    except Exception as e:
        print(f"[ERROR] Failed to publish post: {e}")


def add_queue_interactive():
    print("\n--- Add Post to Queue ---")
    message = input("Enter post caption: ").strip()
    if not message:
        print("[!] Caption cannot be empty.")
        return

    images_str = input("Image path (relative or full, press Enter to skip): ").strip()
    images = [images_str] if images_str else []

    sched = input("Scheduled time (Format: YYYY-MM-DD HH:MM, or press Enter for next run): ").strip()
    scheduled_time = sched if sched else None

    item = queue_manager.add_post_to_queue(message, images=images, scheduled_time=scheduled_time)
    print(f"[SUCCESS] Added to queue as Item #{item['id']}!")


def view_queue():
    queue = queue_manager.load_queue()
    print("\n--- Current Post Queue ---")
    if not queue:
        print("The queue is empty. Add posts to 'queue.json' or via the menu.")
        return

    for item in queue:
        status_symbol = {
            "pending": "[Pending]",
            "published": "[Published]",
            "failed": "[Failed]"
        }.get(item["status"], item["status"])

        sched_info = f" | Scheduled: {item['scheduled_time']}" if item.get("scheduled_time") else " | Ready now"
        print(f"\n[Item #{item['id']}] {status_symbol}{sched_info}")
        print(f"  Message: {item['message'][:80]}{'...' if len(item['message']) > 80 else ''}")
        if item.get("images"):
            print(f"  Images:  {', '.join(item['images'])}")
        if item.get("facebook_post_id"):
            print(f"  FB Post ID: {item['facebook_post_id']}")
        if item.get("error"):
            print(f"  Error: {item['error']}")
        if item.get("facebook_post_id"):
            print(f"  FB Post ID: {item['facebook_post_id']}")
        if item.get("error"):
            print(f"  Error: {item['error']}")


def run_scheduler_loop(interval_seconds: int = 60):
    print(f"\n[*] Starting Automated Scheduler (Checking queue every {interval_seconds}s)...")
    print("    Press Ctrl+C to stop.")
    try:
        while True:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{now_str}] Checking queue for due posts...")
            stats = queue_manager.process_queue()
            if stats["processed"] > 0:
                print(f"    Summary: {stats['published']} published, {stats['failed']} failed.")
            else:
                print(f"    No due posts to publish right now ({stats['skipped']} pending for future time).")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n[*] Scheduler stopped by user.")


def main():
    parser = argparse.ArgumentParser(description="Kidz Garments Facebook Page Automation Tool")
    parser.add_argument("--verify", action="store_true", help="Verify Page ID and Access Token")
    parser.add_argument("--message", type=str, help="Publish an instant post with this message")
    parser.add_argument("--image", type=str, help="Optional image path or URL for instant post")
    parser.add_argument("--queue", action="store_true", help="Process due posts in queue.json immediately")
    parser.add_argument("--scheduler", action="store_true", help="Start continuous scheduler loop")
    parser.add_argument("--interval", type=int, default=60, help="Scheduler check interval in seconds (default: 60)")

    args = parser.parse_args()

    if args.verify:
        verify_setup()
        return

    if args.message:
        if not config.is_configured():
            print("[!] Configure .env first before posting.")
            return
        if args.image:
            res = fb_api.post_single_photo(args.message, args.image)
            print(f"[✓] Published photo post! ID: {res.get('id')}")
        else:
            res = fb_api.post_text(args.message)
            print(f"[✓] Published text post! ID: {res.get('id')}")
        return

    if args.queue:
        if not config.is_configured():
            print("[!] Configure .env first before processing queue.")
            return
        stats = queue_manager.process_queue()
        print(f"\n[✓] Done! Published: {stats['published']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")
        return

    if args.scheduler:
        if not config.is_configured():
            print("[!] Configure .env first before starting scheduler.")
            return
        run_scheduler_loop(args.interval)
        return

    # Interactive CLI Menu
    while True:
        print_banner()
        configured = config.is_configured()
        print(f"Status: {'[Configured]' if configured else '[Credentials Not Set in .env]'}")
        print("\nChoose an option:")
        print("1. Verify Page Connection & Token")
        print("2. Publish Instant Post (Text or Photo)")
        print("3. View Post Queue")
        print("4. Add Post to Queue")
        print("5. Process Queue Now (Publish Due Posts)")
        print("6. Start Continuous Automated Scheduler")
        print("7. View Instructions / Setup Guide")
        print("8. Exit")

        choice = input("\nEnter choice (1-8): ").strip()
        if choice == "1":
            verify_setup()
        elif choice == "2":
            if not configured:
                print("[!] Please configure .env first.")
            else:
                post_now_interactive()
        elif choice == "3":
            view_queue()
        elif choice == "4":
            add_queue_interactive()
        elif choice == "5":
            if not configured:
                print("[!] Please configure .env first.")
            else:
                queue_manager.process_queue()
        elif choice == "6":
            if not configured:
                print("[!] Please configure .env first.")
            else:
                run_scheduler_loop(60)
        elif choice == "7":
            readme_path = config.BASE_DIR / "README.md"
            if readme_path.exists():
                print(readme_path.read_text(encoding="utf-8"))
            else:
                print("Open README.md in this folder for the full guide.")
        elif choice == "8":
            print("\nGoodbye!")
            break
        else:
            print("[!] Invalid option. Please enter a number between 1 and 8.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
