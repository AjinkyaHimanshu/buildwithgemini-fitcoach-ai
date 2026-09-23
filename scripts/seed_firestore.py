"""Seed script to populate Firestore 'exercises' collection for FitCoach AI.

HARDCODED PROJECT ID: 'qwiklabs-gcp-02-f169ce6219d4'
(Avoids Agent Platform project number resolution failures).
"""

import json
from pathlib import Path
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-02-f169ce6219d4"
LOCAL_DB_FILE = Path("data/exercises_db.json")

SEED_EXERCISES = [
    {
        "exercise_id": "plank",
        "name": "Plank",
        "target_muscle": "Core & Abdominals",
        "difficulty": "Beginner",
        "equipment": "Bodyweight",
        "description": "Static isometric core hold. Maintain neutral spine, pack shoulders, and brace abdominals tight.",
        "gif_url_male": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/plank_male.gif",
        "gif_url_female": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/plank_female.gif",
    },
    {
        "exercise_id": "chest_supported_dumbbell_row",
        "name": "Chest-Supported Dumbbell Row",
        "target_muscle": "Lats & Upper Back",
        "difficulty": "Intermediate",
        "equipment": "Dumbbell & Incline Bench",
        "description": "Lower-back friendly pulling movement. Lie chest-down on a 45-degree bench and row dumbbells toward hips.",
        "gif_url_male": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/chest_supported_dumbbell_row_male.gif",
        "gif_url_female": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/chest_supported_dumbbell_row_female.gif",
    },
    {
        "exercise_id": "dumbbell_romanian_deadlift",
        "name": "Dumbbell Romanian Deadlift",
        "target_muscle": "Hamstrings & Glutes",
        "difficulty": "Intermediate",
        "equipment": "Dumbbells",
        "description": "Hip-hinge pattern targeting posterior chain. Hinge at hips while maintaining slight knee bend and flat back.",
        "gif_url_male": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/dumbbell_romanian_deadlift_male.gif",
        "gif_url_female": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/dumbbell_romanian_deadlift_female.gif",
    },
    {
        "exercise_id": "neutral_grip_incline_dumbbell_press",
        "name": "Neutral-Grip Incline Dumbbell Press",
        "target_muscle": "Upper Chest & Triceps",
        "difficulty": "Intermediate",
        "equipment": "Dumbbells & Incline Bench",
        "description": "Upper body pressing variation with palms facing each other to reduce shoulder joint stress.",
        "gif_url_male": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/neutral_grip_incline_dumbbell_press_male.gif",
        "gif_url_female": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/neutral_grip_incline_dumbbell_press_female.gif",
    },
    {
        "exercise_id": "goblet_box_squat",
        "name": "Goblet Box Squat",
        "target_muscle": "Quadriceps & Glutes",
        "difficulty": "Beginner",
        "equipment": "Dumbbell or Kettlebell",
        "description": "Squat variation holding weight at chest level and squatting to a box target for depth consistency.",
        "gif_url_male": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/goblet_box_squat_male.gif",
        "gif_url_female": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/goblet_box_squat_female.gif",
    },
    {
        "exercise_id": "cable_face_pull",
        "name": "Cable Face Pull",
        "target_muscle": "Rear Delts & Rotator Cuff",
        "difficulty": "Beginner",
        "equipment": "Cable Machine & Rope Attachment",
        "description": "Shoulder health and posterior delt exercise. Pull rope toward forehead with high elbows and external rotation.",
        "gif_url_male": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/cable_face_pull_male.gif",
        "gif_url_female": "https://storage.googleapis.com/fitcoach-ai-media-qwiklabs-gcp-02-f169ce6219d4/visual_guides/cable_face_pull_female.gif",
    },
]


def seed_firestore_exercises():
    print(f"🌱 Initializing Firestore client with hardcoded project ID: '{PROJECT_ID}'...")

    LOCAL_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    local_data = {}

    firestore_success = False
    try:
        import os
        db_name = os.getenv("FIRESTORE_DATABASE", "(default)")
        db = firestore.Client(project=PROJECT_ID, database=db_name)
        print(f"⚡ Connected to Firestore client (database='{db_name}'). Populating 'exercises' collection...")

        for ex in SEED_EXERCISES:
            doc_ref = db.collection("exercises").document(ex["exercise_id"])
            doc_ref.set(ex, merge=True)
            local_data[ex["exercise_id"]] = ex
            print(f"  [+] Seeded doc in Firestore: exercises/{ex['exercise_id']}")

        firestore_success = True
        print("✅ Firestore 'exercises' collection seeded successfully!")
    except Exception as e:
        print(f"⚠️ Notice: Cloud Firestore instance not provisioned in lab GCP project ({e}).")
        print("📁 Populating local data fallback file 'data/exercises_db.json'...")

        for ex in SEED_EXERCISES:
            local_data[ex["exercise_id"]] = ex

    LOCAL_DB_FILE.write_text(json.dumps(local_data, indent=2))
    print(f"✅ Local database file '{LOCAL_DB_FILE}' ready with {len(local_data)} exercise items.")


if __name__ == "__main__":
    seed_firestore_exercises()
