"""Script to generate and upload exercise visual guides to Google Cloud Storage bucket."""

from io import BytesIO
from PIL import Image, ImageDraw
from google.cloud import storage

import os

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-02-f169ce6219d4")
BUCKET_NAME = f"fitcoach-ai-media-{PROJECT_ID}"

EXERCISES_TO_SEED = [
    ("Plank", "Core & Abdominals"),
    ("Chest-Supported Dumbbell Row", "Lats & Upper Back"),
    ("Dumbbell Romanian Deadlift", "Hamstrings & Glutes"),
    ("Neutral-Grip Incline Dumbbell Press", "Upper Chest & Triceps"),
    ("Goblet Box Squat", "Quadriceps & Glutes"),
    ("Cable Face Pull", "Rear Delts & Rotator Cuff"),
]


def create_exercise_card(exercise_name: str, target_muscle: str = "Full Body") -> bytes:
    # 800x450 dark theme card
    img = Image.new("RGB", (800, 450), color=(15, 23, 42))  # Slate dark background
    draw = ImageDraw.Draw(img)

    # Accent bars
    draw.rectangle([0, 0, 800, 10], fill=(99, 102, 241))  # Indigo top accent bar
    draw.rectangle([0, 440, 800, 450], fill=(20, 184, 166))  # Teal bottom accent bar

    # Header title
    draw.text((40, 40), "FITCOACH AI • VISUAL EXERCISE GUIDE", fill=(148, 163, 184))
    draw.text((40, 75), exercise_name.upper(), fill=(255, 255, 255))

    # Target muscle pill
    draw.rounded_rectangle([40, 130, 360, 170], radius=8, fill=(30, 41, 59), outline=(99, 102, 241))
    draw.text((55, 142), f"TARGET: {target_muscle.upper()}", fill=(165, 180, 252))

    # Visual cue Box
    draw.rounded_rectangle([40, 195, 760, 390], radius=12, fill=(30, 41, 59))
    draw.text((60, 215), "KEY FORM & EXECUTION CUES:", fill=(52, 211, 153))

    cues = [
        "1. Maintain neutral spine alignment and brace core tight throughout movement.",
        "2. Control eccentric (lowering) phase for maximum muscular tension & stability.",
        "3. Breathe rhythmically and avoid hyperextending lower back or locking joints."
    ]
    y = 255
    for cue in cues:
        draw.text((60, y), cue, fill=(226, 232, 240))
        y += 40

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def seed_visual_guides():
    print(f"Connecting to Cloud Storage bucket '{BUCKET_NAME}'...")
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)

    for ex_name, target in EXERCISES_TO_SEED:
        slug = ex_name.lower().replace(" ", "_").replace("-", "_")
        object_key = f"visual_guides/{slug}.png"
        png_bytes = create_exercise_card(ex_name, target)

        blob = bucket.blob(object_key)
        blob.upload_from_string(png_bytes, content_type="image/png")
        url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_key}"
        print(f"  [+] Uploaded visual guide for '{ex_name}' -> {url}")

    print("✅ All exercise visual guides uploaded successfully!")


if __name__ == "__main__":
    seed_visual_guides()
