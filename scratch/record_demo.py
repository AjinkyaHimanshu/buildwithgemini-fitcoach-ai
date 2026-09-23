import asyncio
import os
import shutil
from pathlib import Path
from playwright.async_api import async_playwright
from google.cloud import storage

APP_URL = "https://fitcoach-frontend-477671931395.us-east1.run.app"
ARTIFACT_DIR = "/config/.gemini/antigravity/brain/691e07c5-54d1-46ee-ac92-601d91653505"
GCS_BUCKET = "fitcoach-ai-media-3812"
PROJECT_ID = "qwiklabs-gcp-03-a5949decd8e8"

async def record():
    os.makedirs("scratch/videos", exist_ok=True)
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir="scratch/videos",
            record_video_size={"width": 1280, "height": 800}
        )

        page = await context.new_page()
        print(f"Navigating to {APP_URL}...")
        await page.goto(APP_URL, wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Turn 1: Click 45-min Workout prompt chip
        print("Turn 1: Clicking '45-min Workout' chip...")
        await page.click('button[data-prompt*="45-minute"]')
        await page.wait_for_timeout(1000)
        await page.click("#form button")
        
        # Wait for agent response
        print("Waiting for Turn 1 response...")
        await page.wait_for_selector("#log .msg.agent", timeout=30000)
        await page.wait_for_timeout(6000)

        # Turn 2: Ask for Target HR zones
        print("Turn 2: Asking for Target HR Zones...")
        await page.fill("#input", "Calculate target heart rate zones for age 30 with resting HR 60")
        await page.wait_for_timeout(800)
        await page.click("#form button")
        
        print("Waiting for Turn 2 response...")
        await page.wait_for_timeout(7000)

        # Turn 3: Ask for Bicep Curl Form Guide
        print("Turn 3: Requesting exercise form guide...")
        await page.fill("#input", "Generate an exercise form guide image for Dumbbell Bicep Curl")
        await page.wait_for_timeout(800)
        await page.click("#form button")

        print("Waiting for Turn 3 response...")
        await page.wait_for_timeout(8000)

        video_path = await page.video.path()
        await context.close()
        await browser.close()

        print(f"Recorded video saved locally at: {video_path}")

        target_artifact = os.path.join(ARTIFACT_DIR, "fitcoach_agent_demo.webm")
        shutil.copy(video_path, target_artifact)
        print(f"Copied video to artifact directory: {target_artifact}")

        # Upload to GCS
        try:
            client = storage.Client(project=PROJECT_ID)
            bucket = client.bucket(GCS_BUCKET)
            blob = bucket.blob("demo/fitcoach_agent_demo.webm")
            blob.upload_from_filename(target_artifact, content_type="video/webm")
            gcs_url = f"https://storage.googleapis.com/{GCS_BUCKET}/demo/fitcoach_agent_demo.webm"
            print(f"Public GCS Demo Video URL: {gcs_url}")
        except Exception as e:
            print(f"GCS Upload notice: {e}")

if __name__ == "__main__":
    asyncio.run(record())
