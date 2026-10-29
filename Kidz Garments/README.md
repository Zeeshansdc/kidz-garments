# Kidz Garments - Facebook Page Automation

A professional Python automation system for your Facebook Page. Schedule, queue, and automatically publish posts and product photos using Meta's official Graph API.

---

## 🚀 Quick Start Guide

### Step 1: Open the `.env` file
Open the `.env` file in this folder:
```env
FACEBOOK_PAGE_ID=your_page_id_here
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token_here
```

---

### Step 2: How to Get Your Page ID & Access Token (Takes 2 minutes)

#### 1. Finding Your Page ID (10 seconds)
1. Go to your Facebook Page on Facebook.com.
2. Click **About** $\rightarrow$ **Page Transparency** (or scroll to the bottom of the About section).
3. Copy the numeric **Page ID** (e.g. `102938475619283`).
4. Paste it into `.env` next to `FACEBOOK_PAGE_ID=`.

#### 2. Getting Your Free Page Access Token (2 minutes)
1. Open the [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. Log in with the Facebook account that is an Admin of your Page.
3. In the top-right box:
   * **Meta App:** Choose your app (or click *Create App* $\rightarrow$ Select *Other* $\rightarrow$ *Business*).
   * **User or Page:** Click the dropdown and select **"Page Access Token"**, then select your Page (**Kidz Garments**).
4. Under **Permissions**, ensure these two permissions are added:
   * `pages_manage_posts`
   * `pages_read_engagement`
5. Click **Generate Access Token**.
6. Copy the token string and paste it into `.env` next to `FACEBOOK_PAGE_ACCESS_TOKEN=`.

*(Tip: To make the token permanent/never expire, open the [Access Token Debugger](https://developers.facebook.com/tools/debug/accesstoken/), paste the token, and click **Extend Access Token**).*

---

### Step 3: Run the Automation

Run the interactive dashboard:
```powershell
python autopost.py
```

You will see an easy interactive menu:
```text
============================================================
        KIDZ GARMENTS - FACEBOOK PAGE AUTOMATION        
============================================================
Status: [Configured]

Choose an option:
1. Verify Page Connection & Token
2. Publish Instant Post (Text or Photo)
3. View Post Queue
4. Add Post to Queue
5. Process Queue Now (Publish Due Posts)
6. Start Continuous Automated Scheduler
7. View Instructions / Setup Guide
8. Exit
```

---

## ⚡ Direct Command Line Shortcuts

You can also run commands directly without navigating the menu:

* **Test your connection:**
  ```powershell
  python autopost.py --verify
  ```

* **Publish a quick text post:**
  ```powershell
  python autopost.py --message "New winter collection arrived! 🧸 Direct message us to order."
  ```

* **Publish a post with a product image:**
  ```powershell
  python autopost.py --message "Special 20% discount on baby sets!" --image "images/outfit1.jpg"
  ```

* **Process due posts in `queue.json` right now:**
  ```powershell
  python autopost.py --queue
  ```

* **Start the 24/7 background scheduler:**
  ```powershell
  python autopost.py --scheduler --interval 60
  ```
  *(Checks `queue.json` every 60 seconds and publishes any post whose scheduled time has arrived).*

---

## 📁 Project Structure

```text
Kidz Garments/
├── .env                <- Your Page ID and Access Token (keep private)
├── .env.example        <- Sample configuration template
├── config.py           <- Configuration loader and path settings
├── fb_api.py           <- Meta Graph API communication engine
├── queue_manager.py    <- Queue loader, scheduler & status updater
├── autopost.py         <- Main command-line application & menu
├── queue.json          <- Your post queue list (edit anytime)
├── images/             <- Folder where you can drop product photos
└── logs/               <- Automatic execution logs
```
