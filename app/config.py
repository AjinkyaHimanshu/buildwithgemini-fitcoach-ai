# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Centralized Configuration Module for FitCoach AI (Google ADK Agent Framework).

Consolidates all GCP environment variables, API endpoints, model choices,
GCS bucket locations, and system instruction mandates in a single authoritative source.
"""

import os

# =====================================================================
# 1. GCP Project & Infrastructure Configuration
# =====================================================================
GCP_PROJECT_ID: str = os.getenv("PROJECT_ID", "qwiklabs-gcp-02-f169ce6219d4").strip()
GCP_PROJECT_NUMBER: str = os.getenv("PROJECT_NUMBER", "916472058254").strip()
GCP_REGION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1").strip()
FIRESTORE_PROJECT_ID: str = GCP_PROJECT_ID
FIRESTORE_DATABASE: str = os.getenv("FIRESTORE_DATABASE", "(default)").strip()

GCS_MEDIA_BUCKET: str = os.getenv(
    "GCS_MEDIA_BUCKET", f"fitcoach-ai-media-{GCP_PROJECT_ID}"
).strip()

AGENT_ENGINE_RESOURCE_NAME: str = os.getenv(
    "AGENT_ENGINE_RESOURCE_NAME",
    f"projects/{GCP_PROJECT_NUMBER}/locations/{GCP_REGION}/reasoningEngines/4401436855208247296",
).strip()

# =====================================================================
# 2. Model Selection & GenAI API Options
# =====================================================================
DEFAULT_MODEL_NAME: str = "gemini-2.5-flash"
IMAGE_MODEL_NAME: str = "gemini-2.5-flash-image"
VIDEO_MODEL_NAME: str = "gemini-omni-flash-preview"

# =====================================================================
# 3. Third-Party API Integrations
# =====================================================================
WGER_API_KEY: str = os.getenv("WGER_API_KEY", "").strip()
THEMEALDB_API_KEY: str = os.getenv("THEMEALDB_API_KEY", "1").strip()
OPENFDA_API_KEY: str = os.getenv("OPENFDA_API_KEY", "").strip()

# =====================================================================
# 4. Shared Exercise Catalog Memory Fallback
# =====================================================================
IN_MEMORY_CATALOG = {
    "chest_supported_db_row": {
        "exercise_id": "chest_supported_db_row",
        "name": "Chest-Supported Dumbbell Row",
        "category": "Upper Body Pull",
        "target_muscle": "Lats & Upper Back",
        "difficulty": "Intermediate",
        "joint_friendly_tags": ["lower_back_friendly", "spinal_decompression"],
        "form_instructions": "• Setup: Lie face down on an incline bench set to 45 degrees.\n• Execution: Pull dumbbells towards your hips, squeezing your shoulder blades together without arching your lower back.",
        "equipment_needed": "Incline Bench, Dumbbells",
        "gif_url_male": f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/visual_guides/chest_supported_row_male.gif",
        "gif_url_female": f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/visual_guides/chest_supported_row_female.gif",
    },
    "romanian_deadlift_dumbbells": {
        "exercise_id": "romanian_deadlift_dumbbells",
        "name": "Dumbbell Romanian Deadlift",
        "category": "Lower Body Hinge",
        "target_muscle": "Hamstrings & Glutes",
        "difficulty": "Intermediate",
        "joint_friendly_tags": ["knee_friendly"],
        "form_instructions": "• Setup: Stand with feet hip-width apart holding dumbbells.\n• Execution: Keep knees slightly bent and hinge strictly at hips. Lower dumbbells along shins until you feel a deep stretch in hamstrings.",
        "equipment_needed": "Dumbbells",
        "gif_url_male": f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/visual_guides/dumbbell_romanian_deadlift_male.gif",
        "gif_url_female": f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/visual_guides/dumbbell_romanian_deadlift_female.gif",
    },
    "squat": {
        "exercise_id": "squat",
        "name": "Squat",
        "category": "Lower Body Push",
        "target_muscle": "Quadriceps & Glutes",
        "difficulty": "Beginner to Intermediate",
        "joint_friendly_tags": ["quad_builder"],
        "form_instructions": "• Setup: Stand with feet shoulder-width apart, chest up, and toes pointed slightly out.\n• Descent: Push hips back as if sitting into a chair. Lower until thighs are parallel to the floor.\n• Knee Position: Ensure knees track in line with feet; do not let them cave inward.\n• Ascent: Drive through heels to return to standing position. Squeeze glutes at top.",
        "equipment_needed": "Bodyweight or Dumbbells",
        "gif_url_male": f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/visual_guides/goblet_box_squat_male.gif",
        "gif_url_female": f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/visual_guides/goblet_box_squat_female.gif",
    },
}
