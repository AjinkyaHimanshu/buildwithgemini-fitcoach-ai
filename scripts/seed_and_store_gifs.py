"""Generate exercise GIFs, upload to GCS, and cache gif_url in Firestore & local cache."""

import json
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw
from google.cloud import firestore, storage

import os

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-02-f169ce6219d4")
BUCKET_NAME = f"fitcoach-ai-media-{PROJECT_ID}"
LOCAL_CACHE_FILE = Path("data/firestore_cache.json")

EXERCISES = [
    ("Plank", "Core & Abdominals"),
    ("Chest-Supported Dumbbell Row", "Lats & Upper Back"),
    ("Dumbbell Romanian Deadlift", "Hamstrings & Glutes"),
    ("Neutral-Grip Incline Dumbbell Press", "Upper Chest & Triceps"),
    ("Goblet Box Squat", "Quadriceps & Glutes"),
    ("Cable Face Pull", "Rear Delts & Rotator Cuff"),
]


def create_exercise_gif_bytes(exercise_name: str, target_muscle: str = "Full Body") -> bytes:
    frames = []

    # Frame 1: Starting Alignment
    img1 = Image.new("RGB", (800, 450), color=(15, 23, 42))
    d1 = ImageDraw.Draw(img1)
    d1.rectangle([0, 0, 800, 10], fill=(99, 102, 241))
    d1.rectangle([0, 440, 800, 450], fill=(20, 184, 166))
    d1.text((40, 40), "FITCOACH AI • ANIMATED EXERCISE DEMO", fill=(148, 163, 184))
    d1.text((40, 75), f"▶ PHASE 1: START POSITION — {exercise_name.upper()}", fill=(255, 255, 255))
    d1.rounded_rectangle([40, 130, 380, 170], radius=8, fill=(30, 41, 59), outline=(99, 102, 241))
    d1.text((55, 142), f"TARGET: {target_muscle.upper()}", fill=(165, 180, 252))
    d1.rounded_rectangle([40, 195, 760, 390], radius=12, fill=(30, 41, 59))
    d1.text((60, 215), "STEP 1: INITIAL POSTURE & ALIGNMENT", fill=(52, 211, 153))
    d1.text((60, 260), "1. Brace core tight, pack shoulders, and align spine neutrally.", fill=(226, 232, 240))
    d1.text((60, 300), "2. Inhale deeply into diaphragm before initiating movement.", fill=(226, 232, 240))
    frames.append(img1)

    # Frame 2: Peak Contraction
    img2 = Image.new("RGB", (800, 450), color=(15, 23, 42))
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([0, 0, 800, 10], fill=(20, 184, 166))
    d2.rectangle([0, 440, 800, 450], fill=(99, 102, 241))
    d2.text((40, 40), "FITCOACH AI • ANIMATED EXERCISE DEMO", fill=(148, 163, 184))
    d2.text((40, 75), f"⚡ PHASE 2: PEAK CONTRACTION — {exercise_name.upper()}", fill=(255, 255, 255))
    d2.rounded_rectangle([40, 130, 380, 170], radius=8, fill=(30, 41, 59), outline=(20, 184, 166))
    d2.text((55, 142), f"TARGET: {target_muscle.upper()}", fill=(165, 180, 252))
    d2.rounded_rectangle([40, 195, 760, 390], radius=12, fill=(30, 41, 59))
    d2.text((60, 215), "STEP 2: DRIVE & CONTROLLED RETURN", fill=(251, 191, 36))
    d2.text((60, 260), "1. Drive weight smoothly; contract target muscle hard at top.", fill=(226, 232, 240))
    d2.text((60, 300), "2. Hold peak squeeze 1 second, then control 2-3 second lowering phase.", fill=(226, 232, 240))
    frames.append(img2)

    buf = BytesIO()
    frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=1500, loop=0)
    return buf.getvalue()


def seed_and_cache_gifs():
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)

    try:
        db = firestore.Client(project=PROJECT_ID)
    except Exception:
        db = None

    LOCAL_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    cache = {}
    if LOCAL_CACHE_FILE.exists():
        try:
            cache = json.loads(LOCAL_CACHE_FILE.read_text())
        except Exception:
            cache = {}

    print("🚀 Generating, Uploading, and Caching Exercise GIFs...")

    for ex_name, target in EXERCISES:
        slug = ex_name.lower().strip().replace(" ", "_").replace("-", "_")
        object_key = f"visual_guides/{slug}.gif"

        gif_bytes = create_exercise_gif_bytes(ex_name, target)
        blob = bucket.blob(object_key)
        blob.upload_from_string(gif_bytes, content_type="image/gif")
        gif_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_key}"

        doc_data = {
            "exercise_id": slug,
            "name": ex_name,
            "target_muscle": target,
            "gif_url": gif_url,
        }

        # Save to local cache file
        cache[slug] = doc_data

        # Save to Firestore if available
        if db:
            try:
                db.collection("exercises").document(slug).set(doc_data, merge=True)
            except Exception:
                pass

        print(f"  [+] Saved GIF for '{ex_name}' -> {gif_url}")

    LOCAL_CACHE_FILE.write_text(json.dumps(cache, indent=2))
    print("✅ All exercise GIFs generated, uploaded, and cached successfully!")


if __name__ == "__main__":
    seed_and_cache_gifs()
