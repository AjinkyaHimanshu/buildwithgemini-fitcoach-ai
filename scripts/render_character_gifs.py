"""Generate character-animated exercise GIFs with male and female athlete stick-figure/vector drawings."""

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


def draw_athlete_figure(draw: ImageDraw.ImageDraw, gender: str, phase: int, ex_slug: str):
    """Draws animated stick figure / character performing the exercise movement."""
    is_female = gender.lower() == "female"
    body_color = (244, 114, 182) if is_female else (96, 165, 250)  # Pink vs Blue
    joint_color = (255, 255, 255)
    bench_color = (100, 116, 139)

    cx, cy = 600, 260  # Center position of right side animation panel

    # Draw Ground Line
    draw.line([(450, 360), (750, 360)], fill=(71, 85, 105), width=4)

    if "plank" in ex_slug:
        # Plank position
        head = (490, 280)
        shoulder = (530, 290)
        elbow = (530, 350)
        hip = (640, 300 if phase == 1 else 295)
        knee = (700, 325)
        ankle = (740, 350)

        # Head
        draw.ellipse([head[0] - 15, head[1] - 15, head[0] + 15, head[1] + 15], fill=body_color)
        if is_female:
            # Draw ponytail / long hair
            draw.line([(head[0] - 12, head[1] - 5), (head[0] - 30, head[1] + 15)], fill=(217, 70, 239), width=5)

        # Torso & Spine (Head -> Shoulder -> Hip)
        draw.line([head, shoulder], fill=body_color, width=8)
        draw.line([shoulder, hip], fill=body_color, width=10)

        # Arms (Forearm Plank)
        draw.line([shoulder, elbow], fill=body_color, width=8)
        draw.line([elbow, (560, 350)], fill=body_color, width=8)

        # Legs (Hip -> Knee -> Ankle)
        draw.line([hip, knee], fill=body_color, width=8)
        draw.line([knee, ankle], fill=body_color, width=8)

        # Core tension glow in Phase 2
        if phase == 2:
            draw.ellipse([580, 285, 620, 315], outline=(52, 211, 153), width=4)

    elif "squat" in ex_slug:
        if phase == 1:
            # Standing position
            head = (600, 170)
            hip = (600, 250)
            knee = (600, 300)
            ankle = (600, 350)
            elbow = (580, 210)
            hand = (600, 200)
        else:
            # Deep squat position
            head = (570, 230)
            hip = (550, 290)
            knee = (610, 300)
            ankle = (600, 350)
            elbow = (560, 250)
            hand = (580, 240)

        draw.ellipse([head[0] - 15, head[1] - 15, head[0] + 15, head[1] + 15], fill=body_color)
        if is_female:
            draw.line([(head[0] - 10, head[1]), (head[0] - 25, head[1] + 20)], fill=(217, 70, 239), width=5)

        draw.line([head, hip], fill=body_color, width=10)
        draw.line([hip, knee], fill=body_color, width=8)
        draw.line([knee, ankle], fill=body_color, width=8)
        draw.line([(head[0], head[1] + 20), elbow], fill=body_color, width=6)
        draw.line([elbow, hand], fill=body_color, width=6)

        # Draw Goblet DB
        draw.rectangle([hand[0] - 10, hand[1] - 15, hand[0] + 10, hand[1] + 15], fill=(251, 191, 36))

    else:
        # General Row/Press Hinge figure
        if phase == 1:
            head = (540, 200)
            hip = (600, 260)
            knee = (620, 310)
            ankle = (630, 350)
            hand = (540, 300)
            elbow = (550, 250)
        else:
            head = (540, 200)
            hip = (600, 260)
            knee = (620, 310)
            ankle = (630, 350)
            hand = (580, 240)
            elbow = (600, 210)

        draw.ellipse([head[0] - 15, head[1] - 15, head[0] + 15, head[1] + 15], fill=body_color)
        if is_female:
            draw.line([(head[0] - 10, head[1]), (head[0] - 25, head[1] + 25)], fill=(217, 70, 239), width=5)

        draw.line([head, hip], fill=body_color, width=10)
        draw.line([hip, knee], fill=body_color, width=8)
        draw.line([knee, ankle], fill=body_color, width=8)
        draw.line([(head[0], head[1] + 20), elbow], fill=body_color, width=6)
        draw.line([elbow, hand], fill=body_color, width=6)
        draw.ellipse([hand[0] - 8, hand[1] - 8, hand[0] + 8, hand[1] + 8], fill=(251, 191, 36))


def create_character_animated_gif(exercise_name: str, target_muscle: str, gender: str) -> bytes:
    frames = []
    slug = exercise_name.lower().strip().replace(" ", "_").replace("-", "_")
    is_female = gender.lower() == "female"

    accent_color = (244, 63, 94) if is_female else (59, 130, 246)
    badge_label = "🏃‍♀️ FEMALE ATHLETE ANIMATION" if is_female else "🏃‍♂️ MALE ATHLETE ANIMATION"

    # Frame 1: Setup Position
    img1 = Image.new("RGB", (800, 450), color=(15, 23, 42))
    d1 = ImageDraw.Draw(img1)
    d1.rectangle([0, 0, 800, 10], fill=accent_color)
    d1.rectangle([0, 440, 800, 450], fill=(20, 184, 166))
    d1.text((40, 30), "FITCOACH AI • CHARACTER ANIMATION DEMO", fill=(148, 163, 184))
    d1.text((40, 60), badge_label, fill=accent_color)
    d1.text((40, 90), exercise_name.upper(), fill=(255, 255, 255))

    # Left Info Card
    d1.rounded_rectangle([40, 140, 420, 395], radius=10, fill=(30, 41, 59))
    d1.text((60, 160), "PHASE 1: STARTING POSITION", fill=(52, 211, 153))
    d1.text((60, 200), f"Target: {target_muscle}", fill=(165, 180, 252))
    d1.text((60, 240), "• Align head & spine neutral", fill=(226, 232, 240))
    d1.text((60, 275), "• Brace core tight", fill=(226, 232, 240))
    d1.text((60, 310), "• Pack shoulders back", fill=(226, 232, 240))

    # Right Animation Panel
    draw_athlete_figure(d1, gender, phase=1, ex_slug=slug)
    frames.append(img1)

    # Frame 2: Peak Contraction
    img2 = Image.new("RGB", (800, 450), color=(15, 23, 42))
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([0, 0, 800, 10], fill=(20, 184, 166))
    d2.rectangle([0, 440, 800, 450], fill=accent_color)
    d2.text((40, 30), "FITCOACH AI • CHARACTER ANIMATION DEMO", fill=(148, 163, 184))
    d2.text((40, 60), badge_label, fill=accent_color)
    d2.text((40, 90), exercise_name.upper(), fill=(255, 255, 255))

    # Left Info Card
    d2.rounded_rectangle([40, 140, 420, 395], radius=10, fill=(30, 41, 59))
    d2.text((60, 160), "PHASE 2: PEAK CONTRACTION", fill=(251, 191, 36))
    d2.text((60, 200), f"Target: {target_muscle}", fill=(165, 180, 252))
    d2.text((60, 240), "• Squeeze target muscle hard", fill=(226, 232, 240))
    d2.text((60, 275), "• Hold 1 second at top", fill=(226, 232, 240))
    d2.text((60, 310), "• Control 2-3s return", fill=(226, 232, 240))

    # Right Animation Panel
    draw_athlete_figure(d2, gender, phase=2, ex_slug=slug)
    frames.append(img2)

    buf = BytesIO()
    frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=1200, loop=0)
    return buf.getvalue()


def render_all_character_gifs():
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

    print("🎨 Rendering Character-Animated Male & Female GIFs...")

    for ex_name, target in EXERCISES:
        slug = ex_name.lower().strip().replace(" ", "_").replace("-", "_")

        # Generate Male Animated GIF
        male_bytes = create_character_animated_gif(ex_name, target, "male")
        male_blob = bucket.blob(f"visual_guides/{slug}_male.gif")
        male_blob.upload_from_string(male_bytes, content_type="image/gif")
        male_url = f"https://storage.googleapis.com/fitcoach-ai-media-3812/visual_guides/{slug}_male.gif"

        # Generate Female Animated GIF
        female_bytes = create_character_animated_gif(ex_name, target, "female")
        female_blob = bucket.blob(f"visual_guides/{slug}_female.gif")
        female_blob.upload_from_string(female_bytes, content_type="image/gif")
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

        print(f"  [+] Male Character GIF for '{ex_name}' -> {male_url}")
        print(f"  [+] Female Character GIF for '{ex_name}' -> {female_url}")

    LOCAL_CACHE_FILE.write_text(json.dumps(cache, indent=2))
    print("✅ All character-animated exercise GIFs generated & cached successfully!")


if __name__ == "__main__":
    render_all_character_gifs()
