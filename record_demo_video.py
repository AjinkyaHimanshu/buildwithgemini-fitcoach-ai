import os
import time
import sys
from playwright.sync_api import sync_playwright

ARTIFACTS_DIR = "/config/.gemini/antigravity/brain/7b1bf65a-f8fc-462b-ae0d-68a304a83d09"
VIDEO_TEMP_DIR = os.path.join(ARTIFACTS_DIR, "video_temp")
OUTPUT_VIDEO_PATH = os.path.join(ARTIFACTS_DIR, "fitcoach_ai_agent_demo.webm")
TARGET_URL = "https://fitcoach-portal-916472058254.us-central1.run.app"

PROMPTS = [
    "Can you show me an animated GIF of proper form for Push-ups?",
    "My wrists hurt when doing Push-ups on the floor—what's a safer, wrist-friendly modification?",
    "Can you build me a 30-minute home Push-up workout routine tailored for a beginner?",
    "I just finished my session—can you log 4 sets of 12 Push-ups at bodyweight?",
    "What chest and shoulder muscles do Push-ups target?",
    "How much protein and calories are in 200 grams of Paneer and 100 grams of cooked Chana (chickpeas) after my Push-up workout?",
    "Can you find me healthy high-protein Indian vegetarian recipes like Dal or Paneer for post-workout dinner?",
    "Are there any FDA safety warnings or recalls on plant-based vegetarian protein powders?",
    "What natural herbs or herbal teas help soothe wrist joint soreness and speed recovery after Push-ups?",
]

os.makedirs(VIDEO_TEMP_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)

def record_demo():
    log("Starting Playwright Video Recording...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=VIDEO_TEMP_DIR,
            record_video_size={"width": 1280, "height": 800}
        )
        page = context.new_page()

        log(f"Navigating to {TARGET_URL}...")
        page.goto(TARGET_URL, wait_until="networkidle")
        time.sleep(2)

        # 1. Open side menu drawer for reference
        log("Opening side menu drawer (#menu-btn)...")
        menu_btn = page.query_selector("#menu-btn")
        if menu_btn:
            menu_btn.click()
            time.sleep(3.5) # Hold drawer open for reference

        # Close side menu drawer using JS closeDrawer() function
        log("Closing side menu drawer (closeDrawer)...")
        page.evaluate("if (typeof closeDrawer === 'function') closeDrawer();")
        time.sleep(1.2)

        # 2. Click on the "Male" toggle button in header
        log("Selecting 'Male' preferred athlete toggle (#gender-male-btn)...")
        male_btn = page.query_selector("#gender-male-btn")
        if male_btn:
            male_btn.click(force=True)
            time.sleep(1.5)

        # 3. Process all 9 prompts sequentially
        for idx, prompt in enumerate(PROMPTS, 1):
            log(f"[{idx}/9] Sending prompt: '{prompt}'")
            input_box = page.query_selector("#input")
            if input_box:
                input_box.fill(prompt)
                time.sleep(0.5)

                send_btn = page.query_selector("#send-btn")
                if send_btn:
                    send_btn.click()
                else:
                    input_box.press("Enter")

                log("   Waiting for agent response to complete...")
                time.sleep(3)
                page.wait_for_selector("#input:not([disabled])", timeout=45000)
                time.sleep(3.5) # Allow full GIF animation and markdown viewing in recording

        # 4. Click on the "New Chat" button
        log("Clicking 'New Chat' button (#new-chat-btn)...")
        new_chat_btn = page.query_selector("#new-chat-btn")
        if new_chat_btn:
            new_chat_btn.click()
            time.sleep(3)

        page.close()
        context.close()
        video_path = page.video.path()
        browser.close()

        log(f"Raw video saved at: {video_path}")
        if os.path.exists(video_path):
            os.rename(video_path, OUTPUT_VIDEO_PATH)
            log(f"Final Demo Video recorded successfully to: {OUTPUT_VIDEO_PATH}")
            return OUTPUT_VIDEO_PATH

if __name__ == "__main__":
    record_demo()
