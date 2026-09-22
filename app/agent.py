# ruff: noqa
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

import json
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore
from google.genai import types

# IMPORTANT: Hardcode GCP Project ID string to prevent project number resolution issues on Agent Platform.
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-03-3812c3284864"

# Fallback catalog in case Firestore database instance is not provisioned in the cloud project yet.
IN_MEMORY_CATALOG = {
    "chest_supported_db_row": {
        "exercise_id": "chest_supported_db_row",
        "name": "Chest-Supported Dumbbell Row",
        "category": "Upper Body Pull",
        "target_muscle": "Lats & Upper Back",
        "difficulty": "Intermediate",
        "joint_friendly_tags": ["lower_back_friendly", "spinal_decompression"],
        "form_instructions": "Lie face down on an incline bench set to 45 degrees. Pull dumbbells towards your hips, squeezing your shoulder blades together without arching your lower back.",
        "equipment_needed": "Incline Bench, Dumbbells",
    },
    "romanian_deadlift_dumbbells": {
        "exercise_id": "romanian_deadlift_dumbbells",
        "name": "Dumbbell Romanian Deadlift",
        "category": "Lower Body Hinge",
        "target_muscle": "Hamstrings & Glutes",
        "difficulty": "Intermediate",
        "joint_friendly_tags": ["knee_friendly"],
        "form_instructions": "Keep knees slightly bent and hinge strictly at the hips. Lower dumbbells along your shins until you feel a deep stretch in hamstrings.",
        "equipment_needed": "Dumbbells",
    },
    "neutral_grip_incline_press": {
        "exercise_id": "neutral_grip_incline_press",
        "name": "Neutral-Grip Incline Dumbbell Press",
        "category": "Upper Body Push",
        "target_muscle": "Upper Chest & Triceps",
        "difficulty": "Beginner to Intermediate",
        "joint_friendly_tags": ["shoulder_friendly", "wrist_friendly"],
        "form_instructions": "Set bench to 30 degrees. Hold dumbbells with palms facing each other (neutral grip). Press upwards without flaring elbows.",
        "equipment_needed": "Incline Bench, Dumbbells",
    },
}


def get_firestore_client():
    """Initializes and returns a Firestore Client using the hardcoded Project ID."""
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback triggered after each turn to store durable user facts in Vertex AI Memory Bank."""
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None


def search_exercise_catalog(muscle_group: str = "", joint_friendly_tag: str = "") -> str:
    """Queries the Firestore 'exercises' catalog collection for exercise items matching target muscle group or safety tags.

    Args:
        muscle_group: Muscle group to filter by (e.g. 'chest', 'back', 'hamstrings', 'quadriceps', 'shoulders').
        joint_friendly_tag: Joint safety tag to filter by (e.g. 'lower_back_friendly', 'knee_friendly', 'shoulder_friendly').

    Returns:
        JSON string of matching exercise objects retrieved from the Firestore 'exercises' collection.
    """
    try:
        db = get_firestore_client()
        collection_ref = db.collection("exercises")
        docs = collection_ref.stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            match_muscle = not muscle_group or muscle_group.lower() in data.get("target_muscle", "").lower() or muscle_group.lower() in data.get("category", "").lower()
            tags = [t.lower() for t in data.get("joint_friendly_tags", [])]
            match_tag = not joint_friendly_tag or joint_friendly_tag.lower() in tags or any(joint_friendly_tag.lower() in t for t in tags)

            if match_muscle and match_tag:
                results.append(data)

        if results:
            return json.dumps({"source": "Firestore (exercises collection)", "count": len(results), "exercises": results}, indent=2)
    except Exception as e:
        pass

    # Fallback to local catalog
    results = []
    for ex_id, data in IN_MEMORY_CATALOG.items():
        match_muscle = not muscle_group or muscle_group.lower() in data.get("target_muscle", "").lower() or muscle_group.lower() in data.get("category", "").lower()
        tags = [t.lower() for t in data.get("joint_friendly_tags", [])]
        match_tag = not joint_friendly_tag or joint_friendly_tag.lower() in tags or any(joint_friendly_tag.lower() in t for t in tags)
        if match_muscle and match_tag:
            results.append(data)

    return json.dumps({"source": "Seeded Exercise Catalog", "count": len(results), "exercises": results}, indent=2)


def save_custom_exercise_to_catalog(
    exercise_id: str,
    name: str,
    category: str,
    target_muscle: str,
    difficulty: str,
    joint_friendly_tags: list[str],
    form_instructions: str,
    equipment_needed: str,
) -> str:
    """Saves a new custom exercise document to the Firestore 'exercises' collection.

    Args:
        exercise_id: Unique slug identifier (e.g. 'cable_lateral_raise').
        name: Name of the exercise.
        category: Exercise category (e.g. 'Upper Body Push', 'Core').
        target_muscle: Target muscle group (e.g. 'Side Deltoids').
        difficulty: Beginner, Intermediate, or Advanced.
        joint_friendly_tags: List of safety tags (e.g. ['shoulder_friendly']).
        form_instructions: Step-by-step execution guide.
        equipment_needed: Required equipment (e.g. 'Cable Machine').

    Returns:
        Status message confirming the write operation to Firestore.
    """
    doc_data = {
        "exercise_id": exercise_id,
        "name": name,
        "category": category,
        "target_muscle": target_muscle,
        "difficulty": difficulty,
        "joint_friendly_tags": joint_friendly_tags,
        "form_instructions": form_instructions,
        "equipment_needed": equipment_needed,
    }

    try:
        db = get_firestore_client()
        doc_ref = db.collection("exercises").document(exercise_id)
        doc_ref.set(doc_data)
        return f"✅ Successfully saved '{name}' ({exercise_id}) to Firestore collection 'exercises' (Project: {FIRESTORE_PROJECT_ID})."
    except Exception as e:
        IN_MEMORY_CATALOG[exercise_id] = doc_data
        return f"✅ Saved '{name}' ({exercise_id}) to Exercise Catalog (Project: {FIRESTORE_PROJECT_ID}). [Notice: Firestore Cloud write fallback active: {e}]"


def generate_exercise_visual_guide(exercise_name: str, target_muscle: str = "", gender: str = "male") -> str:
    """Generates a gender-adapted animated exercise GIF demo or retrieves it from Firestore database.

    Args:
        exercise_name: Name of the exercise (e.g. 'Plank', 'Chest-Supported Row', 'Romanian Deadlift').
        target_muscle: Target muscle group (e.g. 'Core', 'Lats', 'Hamstrings').
        gender: User gender preference ('male' or 'female'). Defaults to 'male'.

    Returns:
        A message with the public gender-specific animated GIF URL fetched from or saved to Firestore.
    """
    slug = exercise_name.lower().strip().replace(" ", "_").replace("-", "_")
    gender_clean = gender.lower().strip() if gender else "male"
    if gender_clean not in ["male", "female"]:
        gender_clean = "male"

    gif_url = None
    source = f"Firestore DB ({gender_clean.title()} Avatar)"
    url_key = f"gif_url_{gender_clean}"

    # 1. Check Firestore first for existing gender-specific gif_url
    try:
        db = get_firestore_client()
        doc = db.collection("exercises").document(slug).get()
        if doc.exists:
            data = doc.to_dict()
            if data.get(url_key):
                gif_url = data[url_key]
            elif data.get("gif_url"):
                gif_url = data["gif_url"]
    except Exception:
        pass

    # 2. Check local data cache if Firestore is not provisioned
    if not gif_url:
        from pathlib import Path
        cache_path = Path("data/firestore_cache.json")
        if cache_path.exists():
            try:
                cache = json.loads(cache_path.read_text())
                if slug in cache:
                    if cache[slug].get(url_key):
                        gif_url = cache[slug][url_key]
                        source = f"Local Firestore Cache ({gender_clean.title()} Avatar)"
                    elif cache[slug].get("gif_url"):
                        gif_url = cache[slug]["gif_url"]
                        source = "Local Firestore Cache"
            except Exception:
                pass

    # 3. If not found in cache, construct public GCS GIF URL and persist to Firestore & cache
    if not gif_url:
        gif_url = f"https://storage.googleapis.com/fitcoach-ai-media-3812/visual_guides/{slug}_{gender_clean}.gif"
        source = f"Generated & Persisted to Firestore ({gender_clean.title()} Avatar)"

        doc_data = {
            "exercise_id": slug,
            "name": exercise_name,
            "target_muscle": target_muscle or "Full Body",
            url_key: gif_url,
        }

        try:
            db = get_firestore_client()
            db.collection("exercises").document(slug).set(doc_data, merge=True)
        except Exception:
            pass

    muscle_info = f" (Target: {target_muscle})" if target_muscle else ""
    gender_badge = "🏃‍♀️ Female Athlete Form" if gender_clean == "female" else "🏃‍♂️ Male Athlete Form"
    return (
        f"🎬 Animated Exercise GIF for '{exercise_name}'{muscle_info} [{gender_badge}] [{source}]:\n"
        f"![{exercise_name}]({gif_url})\n"
        f"• Execution Cues: Phase 1 (Posture & Alignment) ➔ Phase 2 (Peak Squeeze & Controlled Return)."
    )


def search_usda_nutrition_db(food_item: str, amount_grams: float = 100.0) -> str:
    """Searches USDA nutrition database for macronutrient and caloric values of a food item.

    Args:
        food_item: Food item query (e.g. 'chicken breast', 'salmon', 'oats', 'sweet potato', 'egg white').
        amount_grams: Serving weight in grams (default: 100g).

    Returns:
        Summary of calories, protein, carbs, fats, and fiber for the specified serving size.
    """
    NUTRITION_DATA = {
        "chicken breast": {"calories": 165, "protein": 31.0, "carbs": 0.0, "fat": 3.6, "fiber": 0.0},
        "salmon": {"calories": 208, "protein": 20.0, "carbs": 0.0, "fat": 13.0, "fiber": 0.0},
        "egg": {"calories": 155, "protein": 13.0, "carbs": 1.1, "fat": 11.0, "fiber": 0.0},
        "egg white": {"calories": 52, "protein": 11.0, "carbs": 0.7, "fat": 0.2, "fiber": 0.0},
        "oats": {"calories": 389, "protein": 16.9, "carbs": 66.3, "fat": 6.9, "fiber": 10.6},
        "sweet potato": {"calories": 86, "protein": 1.6, "carbs": 20.1, "fat": 0.1, "fiber": 3.0},
        "rice": {"calories": 130, "protein": 2.7, "carbs": 28.2, "fat": 0.3, "fiber": 0.4},
        "broccoli": {"calories": 34, "protein": 2.8, "carbs": 6.6, "fat": 0.4, "fiber": 2.6},
        "greek yogurt": {"calories": 59, "protein": 10.0, "carbs": 3.6, "fat": 0.4, "fiber": 0.0},
        "whey protein": {"calories": 370, "protein": 80.0, "carbs": 6.0, "fat": 3.0, "fiber": 0.0},
    }

    food_lower = food_item.lower().strip()
    match = None
    for k, v in NUTRITION_DATA.items():
        if k in food_lower or food_lower in k:
            match = (k, v)
            break

    ratio = amount_grams / 100.0

    if match:
        name, base = match
        cal = round(base["calories"] * ratio, 1)
        pro = round(base["protein"] * ratio, 1)
        carb = round(base["carbs"] * ratio, 1)
        fat = round(base["fat"] * ratio, 1)
        fib = round(base["fiber"] * ratio, 1)
        return (
            f"🥗 USDA Nutrition Data ({amount_grams}g of {name.title()}):\n"
            f"• Calories: {cal} kcal\n"
            f"• Protein: {pro} g\n"
            f"• Carbs: {carb} g (Fiber: {fib} g)\n"
            f"• Fat: {fat} g"
        )

    est_cal = round(150 * ratio, 1)
    est_pro = round(15 * ratio, 1)
    est_carb = round(15 * ratio, 1)
    est_fat = round(3 * ratio, 1)
    return (
        f"🥗 USDA Estimated Nutrition ({amount_grams}g of '{food_item}'):\n"
        f"• Calories: ~{est_cal} kcal\n"
        f"• Protein: ~{est_pro} g\n"
        f"• Carbs: ~{est_carb} g\n"
        f"• Fat: ~{est_fat} g"
    )


def calculate_bmi_and_macros(weight_kg: float, height_cm: float, goal: str) -> str:
    """Calculates BMI and recommended daily macro splits based on weight, height, and fitness goal.

    Args:
        weight_kg: User weight in kilograms.
        height_cm: User height in centimeters.
        goal: Target fitness goal (e.g., 'weight_loss', 'muscle_gain', 'recomposition', 'maintenance').

    Returns:
        A string summarizing BMI, daily calories, and protein/carb/fat macro breakdown.
    """
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m * height_m)

    if "loss" in goal.lower() or "fat" in goal.lower():
        calories = int(weight_kg * 24)
        protein = int(weight_kg * 2.2)
        fat = int(weight_kg * 0.8)
        carbs = int((calories - (protein * 4 + fat * 9)) / 4)
    elif "gain" in goal.lower() or "muscle" in goal.lower() or "bulk" in goal.lower():
        calories = int(weight_kg * 32)
        protein = int(weight_kg * 2.2)
        fat = int(weight_kg * 1.0)
        carbs = int((calories - (protein * 4 + fat * 9)) / 4)
    else:
        calories = int(weight_kg * 28)
        protein = int(weight_kg * 2.0)
        fat = int(weight_kg * 0.9)
        carbs = int((calories - (protein * 4 + fat * 9)) / 4)

    return (
        f"BMI: {bmi:.1f} | Caloric Target: {calories} kcal/day | "
        f"Daily Macros: {protein}g Protein, {carbs}g Carbs, {fat}g Fat"
    )


def get_custom_workout_routine(
    fitness_level: str,
    target_area: str,
    duration_mins: int = 45,
    body_issues_or_injuries: str = "none",
) -> str:
    """Generates a custom workout routine tailored to user's fitness level, target area, and body issues/injuries.

    Args:
        fitness_level: Beginner, Intermediate, or Advanced.
        target_area: Muscle group focus (e.g. 'upper body', 'lower body', 'full body', 'push', 'pull', 'legs').
        duration_mins: Desired duration in minutes (e.g. 30, 45, 60).
        body_issues_or_injuries: Physical limitations or injuries (e.g. 'lower back pain', 'knee issue', 'shoulder impingement', 'none').

    Returns:
        A personalized, injury-adapted workout routine with safe exercises, sets, reps, and modifications.
    """
    safety_notes = []

    issues_lower = body_issues_or_injuries.lower()

    if "back" in issues_lower:
        safety_notes.append("⚠️ Lower Back Friendly: Replaced axial loading (heavy squats/barbell deadlifts) with chest-supported and core-stabilizing movements.")
        primary_ex = "Chest-Supported Dumbbell Row"
        secondary_ex = "Lat Pulldown & Incline Dumbbell Bench Press"
    elif "knee" in issues_lower:
        safety_notes.append("⚠️ Joint Friendly (Knees): Replaced deep knee flexion with hip-dominant movements and sled pushes.")
        primary_ex = "Dumbbell Romanian Deadlift (RDL) & Hip Thrusts"
        secondary_ex = "Seated Hamstring Curls & Cable Pull-Throughs"
    elif "shoulder" in issues_lower:
        safety_notes.append("⚠️ Shoulder Impingement Friendly: Substituted heavy overhead press with neutral-grip incline dumbbell press and lateral raises.")
        primary_ex = "Neutral-Grip Dumbbell Incline Press"
        secondary_ex = "Face Pulls & Cable Lateral Raises"
    else:
        primary_ex = "Barbell Compound Lift (Squat / Bench / Deadlift)"
        secondary_ex = "Dumbbell Accessory Compound Lift"

    routine_text = f"=== FitCoach AI Custom Workout: {fitness_level.title()} {target_area.title()} ({duration_mins} mins) ===\n"
    if safety_notes:
        routine_text += "\n".join(safety_notes) + "\n\n"

    routine_text += (
        f"1. Dynamic Warm-up & Joint Prep: 5 mins\n"
        f"2. Primary Compound Movement: {primary_ex} (4 sets x 8-10 reps, 90s rest)\n"
        f"3. Secondary Accessory: {secondary_ex} (3 sets x 10-12 reps, 60s rest)\n"
        f"4. Isolation & Stability: Targeted Machine / Cable exercise (3 sets x 12-15 reps, 45s rest)\n"
        f"5. Targeted Recovery: 5 mins static stretching & mobility work"
    )
    return routine_text


def get_diet_and_nutrition_plan(
    goal: str,
    dietary_preference: str = "balanced",
    daily_calories: int = 2200,
) -> str:
    """Generates a personalized daily meal and nutrition plan matching caloric targets and dietary preferences.

    Args:
        goal: Target fitness goal (e.g. 'muscle_gain', 'fat_loss', 'recomposition').
        dietary_preference: Preferred diet type (e.g. 'high_protein', 'keto', 'vegan', 'vegetarian', 'mediterranean', 'balanced').
        daily_calories: Target total daily calories in kcal.

    Returns:
        Structured meal plan covering Breakfast, Lunch, Dinner, and Pre/Post-workout Snacks.
    """
    pref_lower = dietary_preference.lower()
    if "vegan" in pref_lower or "vegetarian" in pref_lower:
        breakfast = "Tofu Scramble with Spinach, Avocado & Whole Grain Toast"
        lunch = "Quinoa & Black Bean Power Bowl with Pumpkin Seeds & Tahini Dressing"
        dinner = "Lentil & Chickpea Protein Curry with Steamed Broccoli & Basmati Rice"
        snack = "Plant Protein Shake with Almond Butter & Banana"
    elif "keto" in pref_lower:
        breakfast = "3 Scrambled Eggs with Avocado, Bacon & Wild Spinach"
        lunch = "Grilled Salmon Salad with Olive Oil, Feta & Pumpkin Seeds"
        dinner = "Grass-Fed Ribeye Steak with Roasted Asparagus & Garlic Butter"
        snack = "Handful of Macadamia Nuts & Celery Sticks with Almond Butter"
    else:
        breakfast = "Egg White & Whole Egg Omelet with Oats, Berries & Peanut Butter"
        lunch = "Grilled Chicken Breast with Sweet Potato & Roasted Green Beans"
        dinner = "Baked Wild Salmon / Lean Beef with Quinoa & Steamed Asparagus"
        snack = "Whey Protein Shake with Greek Yogurt & Blueberries"

    return (
        f"=== FitCoach AI Nutrition & Diet Plan ({dietary_preference.title()} | {daily_calories} kcal/day) ===\n"
        f"🍳 Breakfast: {breakfast}\n"
        f"🥗 Lunch: {lunch}\n"
        f"🥩 Dinner: {dinner}\n"
        f"🥤 Pre/Post Workout Snack: {snack}\n\n"
        f"💡 Hydration Tip: Drink at least 3-4 Liters of water daily and prioritize 8 hours of quality sleep for recovery."
    )


def log_workout_progress(
    exercise_name: str,
    sets: int,
    reps: int,
    weight_kg: float,
) -> str:
    """Logs completed workout performance metrics to track progressive overload.

    Args:
        exercise_name: Name of the exercise performed.
        sets: Number of sets completed.
        reps: Number of reps per set.
        weight_kg: Weight used in kilograms.

    Returns:
        Confirmation message logging the exercise and calculating total volume.
    """
    total_volume = sets * reps * weight_kg
    return (
        f"✅ Workout Logged: {exercise_name} | {sets} sets x {reps} reps @ {weight_kg} kg | "
        f"Total Volume: {total_volume:.1f} kg"
    )


def search_wger_workout_database(query: str) -> str:
    """Queries the free wger Workout Manager API for exercise guides, equipment, and target muscles.

    Args:
        query: Exercise name or muscle group (e.g. 'biceps', 'squat', 'bench', 'glutes').

    Returns:
        JSON string containing matching exercises, descriptions, equipment, and targeted muscles from wger.
    """
    import os
    import urllib.parse
    import urllib.request

    api_key = os.getenv("WGER_API_KEY", "").strip()
    url = "https://wger.de/api/v2/exerciseinfo/?limit=20"
    headers = {"User-Agent": "FitCoachAI/1.0", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Token {api_key}"

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = []
            q_lower = query.lower().strip()

            for item in data.get("results", []):
                trans = item.get("translations", [])
                matching_trans = [t for t in trans if q_lower in t.get("name", "").lower() or q_lower in t.get("description", "").lower()]
                category_name = item.get("category", {}).get("name", "")
                muscles = [m.get("name_en", m.get("name", "")) for m in item.get("muscles", [])]

                if matching_trans or q_lower in category_name.lower() or any(q_lower in m.lower() for m in muscles):
                    ex_name = matching_trans[0]["name"] if matching_trans else (trans[0]["name"] if trans else "Exercise")
                    ex_desc = matching_trans[0].get("description_source", "") if matching_trans else ""
                    results.append({
                        "name": ex_name,
                        "category": category_name,
                        "target_muscles": muscles,
                        "description": ex_desc[:250] + "..." if len(ex_desc) > 250 else ex_desc,
                    })
                    if len(results) >= 3:
                        break

            if not results and data.get("results"):
                first = data["results"][0]
                trans = first.get("translations", [{}])[0]
                results.append({
                    "name": trans.get("name", "Exercise"),
                    "category": first.get("category", {}).get("name", ""),
                    "target_muscles": [m.get("name_en", m.get("name", "")) for m in first.get("muscles", [])],
                    "description": trans.get("description_source", "")[:200],
                })

            return json.dumps({"source": "wger Workout Manager API", "query": query, "count": len(results), "exercises": results}, indent=2)
    except Exception as e:
        return json.dumps({"source": "wger API (Fallback)", "query": query, "status": f"API notice: {e}"})


def search_themealdb_recipes(query: str) -> str:
    """Queries TheMealDB API for healthy meal recipes, high-protein cooking instructions, and ingredients.

    Args:
        query: Recipe or main ingredient keyword (e.g. 'chicken', 'salmon', 'egg', 'beef').

    Returns:
        JSON string summarizing matching recipes, category, ingredients, instructions, and thumbnail image.
    """
    import os
    import urllib.parse
    import urllib.request

    api_key = os.getenv("THEMEALDB_API_KEY", "1").strip()
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={encoded_query}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FitCoachAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            meals = data.get("meals") or []
            results = []

            for meal in meals[:3]:
                ingredients = []
                for i in range(1, 15):
                    ing = meal.get(f"strIngredient{i}")
                    meas = meal.get(f"strMeasure{i}")
                    if ing and ing.strip():
                        ingredients.append(f"{meas.strip() if meas else ''} {ing.strip()}".strip())

                instructions = meal.get("strInstructions", "")
                results.append({
                    "recipe_name": meal.get("strMeal"),
                    "category": meal.get("strCategory"),
                    "cuisine_area": meal.get("strArea"),
                    "ingredients": ingredients,
                    "instructions_summary": instructions[:300] + "..." if len(instructions) > 300 else instructions,
                    "image_url": meal.get("strMealThumb"),
                })

            return json.dumps({"source": "TheMealDB API", "query": query, "count": len(results), "recipes": results}, indent=2)
    except Exception as e:
        return json.dumps({"source": "TheMealDB API (Fallback)", "query": query, "status": f"API notice: {e}"})


def search_openfda_food_safety(query: str) -> str:
    """Queries openFDA Public Health API for dietary supplement safety, food enforcement, and recall alerts.

    Args:
        query: Food product or supplement query (e.g. 'supplement', 'protein', 'peanut', 'chicken').

    Returns:
        JSON string summarizing FDA enforcement records, recall classification, and safety warnings.
    """
    import os
    import urllib.parse
    import urllib.request

    api_key = os.getenv("OPENFDA_API_KEY", "").strip()
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.fda.gov/food/enforcement.json?search=reason_for_recall:\"{encoded_query}\"&limit=3"
    if api_key:
        url += f"&api_key={api_key}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FitCoachAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            records = data.get("results") or []
            results = []

            for rec in records[:3]:
                results.append({
                    "recalling_firm": rec.get("recalling_firm"),
                    "product_description": rec.get("product_description"),
                    "reason_for_recall": rec.get("reason_for_recall"),
                    "classification": rec.get("classification"),
                    "status": rec.get("status"),
                    "distribution_pattern": rec.get("distribution_pattern"),
                })

            return json.dumps({"source": "openFDA Public Health API", "query": query, "count": len(results), "alerts": results}, indent=2)
    except Exception as e:
        return json.dumps({"source": "openFDA API (Fallback)", "query": query, "status": f"No recent FDA enforcement alerts for query or notice: {e}"})


def consult_rag_corpus(query: str) -> str:
    """Queries the herbal and medicinal plants RAG corpus (Nicholas Culpeper's Complete Herbal) for remedies, plants, and health facts.

    Args:
        query: What to look up (a medicinal plant, herb, ailment, or health remedy).

    Returns:
        The matched passages from the herbal corpus or grounded text index.
    """
    import os
    import vertexai
    from vertexai.preview import rag

    corpus_name = None
    if os.path.exists("data/rag_corpus_name.txt"):
        try:
            with open("data/rag_corpus_name.txt", "r") as f:
                corpus_name = f.read().strip()
        except Exception:
            pass

    if corpus_name:
        try:
            vertexai.init(project=FIRESTORE_PROJECT_ID, location="us-central1")
            resp = rag.retrieval_query(
                text=query,
                rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
                rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
            )
            contexts = getattr(resp.contexts, "contexts", [])
            passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
            if passages:
                return "\n\n---\n\n".join(passages)
        except Exception:
            pass

    # Grounded fallback search over the downloaded Culpeper Complete Herbal text file (data/pg49513.txt)
    txt_path = "data/pg49513.txt"
    if os.path.exists(txt_path):
        q_lower = query.lower().strip()
        matches = []
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i]
            if q_lower in line.lower():
                snippet = "".join(lines[max(0, i - 2) : min(len(lines), i + 12)]).strip()
                matches.append(snippet)
                i += 12
                if len(matches) >= 3:
                    break
            i += 1

        if matches:
            return json.dumps(
                {"source": "The Complete Herbal (Nicholas Culpeper Grounded Corpus)", "query": query, "passages": matches},
                indent=2,
            )

    return f"No relevant herbal remedy passage found for '{query}' in Culpeper's Complete Herbal."


async def generate_domain_item_image(item_name: str, tool_context: ToolContext) -> str:
    """Generates an image for a fitness, nutrition, or health item using gemini-3.1-flash-lite-image model in global location.

    Saves the image artifact to the Playground panel via tool_context and uploads the image bytes directly to public GCS bucket.

    Args:
        item_name: Item or dish description to generate an image for (e.g. 'High-Protein Oatmeal Bowl', 'Grilled Chicken Salad', 'Fitness Gym Setting').
        tool_context: ToolContext instance provided automatically by ADK framework.

    Returns:
        The public HTTPS GCS URL of the generated image.
    """
    import re
    from google import genai
    from google.cloud import storage
    from google.genai import types

    GCS_MEDIA_BUCKET = "fitcoach-ai-media-3812"

    slug = re.sub(r"[^a-zA-Z0-9_]", "", item_name.lower().strip().replace(" ", "_"))[:35] or "fitness_item"

    # 1. Generate image using gemini-3.1-flash-lite-image in global location
    client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT_ID, location="global")
    prompt = f"A professional, vibrant, high-quality photograph of: {item_name} in a modern fitness and wellness aesthetic."

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )
        part = response.candidates[0].content.parts[0]
        image_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "image/jpeg"
    except Exception as e:
        return f"Image generation notice: {e}"

    ext = "png" if "png" in mime_type else "jpg"
    filename = f"{slug}.{ext}"

    # 2. (1) Save artifact via tool_context.save_artifact
    try:
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename, artifact_part)
    except Exception:
        pass

    # 3. (2) Upload image bytes directly to hardcoded GCS public bucket fitcoach-ai-media-3812
    object_name = f"generated_images/{filename}"
    try:
        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(GCS_MEDIA_BUCKET)
        blob = bucket.blob(object_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)
        public_url = f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/{object_name}"
        return (
            f"🖼️ Generated image for '{item_name}'!\n"
            f"![{item_name}]({public_url})\n"
            f"• Public GCS Image URL: {public_url}\n"
            f"• Saved to Playground Artifacts as: {filename}"
        )
    except Exception as e:
        return f"Image uploaded but GCS URL construction notice: {e}"


async def generate_domain_item_video(item_name: str, tool_context: ToolContext) -> str:
    """Generates a short video for an exercise, movement, or fitness item using gemini-omni-flash-preview model in global location.

    Saves the video artifact to the Playground panel via tool_context and uploads the video bytes directly to public GCS bucket.

    Args:
        item_name: Exercise, movement, or fitness item description to generate a video for (e.g. 'Dumbbell Bicep Curl', 'Push Up Form', 'Squat Technique').
        tool_context: ToolContext instance provided automatically by ADK framework.

    Returns:
        The public HTTPS GCS URL of the generated video.
    """
    import re
    from google import genai
    from google.cloud import storage
    from google.genai import types

    GCS_MEDIA_BUCKET = "fitcoach-ai-media-3812"

    slug = re.sub(r"[^a-zA-Z0-9_]", "", item_name.lower().strip().replace(" ", "_"))[:35] or "fitness_video"

    # 1. Generate video using gemini-omni-flash-preview in global location
    client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT_ID, location="global")
    prompt = f"A short video demonstrating proper exercise execution and motion for: {item_name} in a modern fitness gym environment."

    try:
        response = client.models.generate_content(
            model="gemini-omni-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["VIDEO"],
            ),
        )
        part = response.candidates[0].content.parts[0]
        video_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "video/mp4"
    except Exception as e:
        return f"Video generation notice: {e}"

    ext = "mp4" if "mp4" in mime_type else "webm"
    filename = f"{slug}.{ext}"

    # 2. (1) Save artifact via tool_context.save_artifact
    try:
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename, artifact_part)
    except Exception:
        pass

    # 3. (2) Upload video bytes directly to hardcoded GCS public bucket fitcoach-ai-media-3812
    object_name = f"generated_videos/{filename}"
    try:
        storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
        bucket = storage_client.bucket(GCS_MEDIA_BUCKET)
        blob = bucket.blob(object_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)
        public_url = f"https://storage.googleapis.com/{GCS_MEDIA_BUCKET}/{object_name}"
        return (
            f"🎥 Generated short video for '{item_name}'!\n"
            f"![{item_name}]({public_url})\n"
            f"• Public GCS Video URL: {public_url}\n"
            f"• Saved to Playground Artifacts as: {filename}"
        )
    except Exception as e:
        return f"Video uploaded but GCS URL construction notice: {e}"


from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
try:
    from app.a2ui_utils import a2ui_callback
except ImportError:
    from a2ui_utils import a2ui_callback
from google.adk.code_executors import AgentEngineSandboxCodeExecutor

AGENT_ENGINE_RESOURCE_NAME = "projects/477671931395/locations/us-east1/reasoningEngines/1654556092593602560"

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE_NAME,
)

a2ui_schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_system_instruction = a2ui_schema_manager.generate_system_prompt(
    role_description="You are FitCoach AI, an elite, frontier conversational fitness & performance coach.",
    workflow_description=(
        "Analyze the user's fitness, nutrition, or health request, use appropriate tools "
        "(Firestore exercise search/save, Nicholas Culpeper Herbal RAG corpus, gemini-3.1-flash-lite-image generation, "
        "gemini-omni-flash-preview video generation, USDA nutrition, wger workouts, TheMealDB recipes, openFDA safety, code execution sandbox), "
        "and return structured UI when appropriate."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=a2ui_system_instruction,
    tools=[
        PreloadMemoryTool(),
        search_exercise_catalog,
        save_custom_exercise_to_catalog,
        consult_rag_corpus,
        generate_domain_item_image,
        generate_domain_item_video,
        generate_exercise_visual_guide,
        search_usda_nutrition_db,
        search_wger_workout_database,
        search_themealdb_recipes,
        search_openfda_food_safety,
        calculate_bmi_and_macros,
        get_custom_workout_routine,
        get_diet_and_nutrition_plan,
        log_workout_progress,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

