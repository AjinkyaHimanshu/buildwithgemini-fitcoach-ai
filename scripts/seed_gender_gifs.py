"""Generate gender-specific exercise GIFs (Male/Female), upload to GCS, and cache in Firestore."""

import json
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw
from google.cloud import firestore, storage

BUCKET_NAME = "fitcoach-ai-media-3812"
PROJECT_ID = "qwiklabs-gcp-03-3812c3284864"
LOCAL_CACHE_FILE = Path("data/firestore_cache.json")

EXERCISES = [
    ("Plank", "Core & Abdominals"),
    ("Chest-Supported Dumbbell Row", "Lats & Upper Back"),
    ("Dumbbell Romanian Deadlift", "Hamstrings & Glutes"),
    ("Neutral-Grip Incline Dumbbell Press", "Upper Chest & Triceps"),
    ("Goblet Box Squat", "Quadriceps & Glutes"),
    ("Cable Face Pull", "Rear Delts & Rotator Cuff"),
]


def create_gender_exercise_gif(exercise_name: str, target_muscle: str, gender: str) -> bytes:
    frames = []

    is_female = gender.lower() == "female"
    accent_color = (244, 63, 94) if is_female else (59, 130, 246)  # Rose vs Blue
    avatar_label = "🏃‍♀️ FEMALE DEMO • ATHLETE FORM" if is_female else "🏃‍♂️ MALE DEMO • ATHLETE FORM"
    pill_border = (251, 113, 133) if is_female else (96, 165, 250)

    # Frame 1: Starting Position
    img1 = Image.new("RGB", (800, 450), color=(15, 23, 42))
    d1 = ImageDraw.Draw(img1)
    d1.rectangle([0, 0, 800, 10], fill=accent_color)
    d1.rectangle([0, 440, 800, 450], fill=(20, 184, 166))
    d1.text((40, 35), "FITCOACH AI • GENDER-ADAPTED VISUAL GUIDE", fill=(148, 163, 184))
    d1.text((40, 65), avatar_label, fill=accent_color)
    d1.text((40, 98), f"▶ PHASE 1: START POSITION — {exercise_name.upper()}", fill=(255, 255, 255))
    d1.rounded_rectangle([40, 142, 420, 182], radius=8, fill=(30, 41, 59), outline=pill_border)
    d1.text((55, 154), f"TARGET: {target_muscle.upper()}", fill=(226, 232, 240))
    d1.rounded_rectangle([40, 205, 760, 395], radius=12, fill=(30, 41, 59))
    d1.text((60, 225), "STEP 1: INITIAL ALIGNMENT & PREP", fill=(52, 211, 153))
    d1.text((60, 270), "1. Engage core tight, pack shoulders back, and balance center of gravity.", fill=(226, 232, 240))
    d1.text((60, 310), "2. Inhale deeply into diaphragm before initiating movement.", fill=(226, 232, 240))
    frames.append(img1)

    # Frame 2: Peak Contraction
    img2 = Image.new("RGB", (800, 450), color=(15, 23, 42))
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([0, 0, 800, 10], fill=(20, 184, 166))
    d2.rectangle([0, 440, 800, 450], fill=accent_color)
    d2.text((40, 35), "FITCOACH AI • GENDER-ADAPTED VISUAL GUIDE", fill=(148, 163, 184))
    d2.text((40, 65), avatar_label, fill=accent_color)
    d2.text((40, 98), f"⚡ PHASE 2: PEAK CONTRACTION — {exercise_name.upper()}", fill=(255, 255, 255))
    d2.rounded_rectangle([40, 142, 420, 182], radius=8, fill=(30, 41, 59), outline=accent_color)
    d2.text((55, 154), f"TARGET: {target_muscle.upper()}", fill=(226, 232, 240))
    d2.rounded_rectangle([40, 205, 760, 395], radius=12, fill=(30, 41, 59))
    d2.text((60, 225), "STEP 2: DRIVE & CONTROLLED TEMPO", fill=(251, 191, 36))
    d2.text((60, 270), "1. Drive weight smoothly; squeeze target muscles hard at peak contraction.", fill=(226, 232, 240))
    d2.text((60, 310), "2. Exhale smoothly and control the 2-3 second lowering phase.", fill=(226, 232, 240))
    frames.append(img2)

    buf = BytesIO()
    frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=1500, loop=0)
    return buf.getvalue()


def seed_gender_gifs():
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

    print("🚀 Seeding Male & Female Gender-Specific Exercise GIFs...")

    for ex_name, target in EXERCISES:
        slug = ex_name.lower().strip().replace(" ", "_").replace("-", "_")

        # Generate Male GIF
        male_gif_bytes = create_gender_exercise_gif(ex_name, target, "male")
        male_blob = bucket.blob(f"visual_guides/{slug}_male.gif")
        male_blob.upload_from_string(male_gif_bytes, content_type="image/gif")
        male_url = f"https://storage.googleapis.com/fitcoach-ai-media-3812/visual_guides/{slug}_male.gif"

        # Generate Female GIF
        female_gif_bytes = create_gender_exercise_gif(ex_name, target, "female")
        female_blob = bucket.blob(f"visual_guides/{slug}_female.gif")
        female_blob.upload_from_string(female_gif_bytes, content_type="image/gif")
        female_url = f"https://storage.googleapis.com/fitcoach-ai-media-3812/visual_guides/{slug}_female.gif"

        doc_data = {
            "exercise_id": slug,
            "name": ex_name,
            "target_muscle": target,
            "gif_url_male": male_url,
            "gif_url_female": female_url,
            "gif_url": male_url,
        }

        cache[slug] = doc_data

        if db:
            try:
                db.collection("exercises").document(slug).set(doc_data, merge=True)
            except Exception:
                pass

        print(f"  [+] Male GIF for '{ex_name}' -> {male_url}")
        print(f"  [+] Female GIF for '{ex_name}' -> {female_url}")

    LOCAL_CACHE_FILE.write_text(json.dumps(cache, indent=2))
    print("✅ Gender-specific exercise GIFs seeded and cached successfully!")


if __name__ == "__main__":
    seed_gender_gifs()
