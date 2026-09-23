# 🏋️‍♂️ FitCoach AI - Autonomous Fitness & Performance Agent

FitCoach AI is an intelligent, multi-tool conversational fitness and performance agent built with **Google ADK (Agent Development Kit)**, **Gemini**, and **Google Cloud Agent Runtime**. It delivers personalized workout routines, evidence-based sports science advice, USDA nutrition lookups, and visual exercise form guides.

![FitCoach AI Demo](./demo.gif)

---

## ✨ Implemented Agent Capabilities

FitCoach AI connects to Google Cloud services and external APIs via a 15-tool registry defined in [`app/agent.py`](file:///config/Desktop/Session4/buildwithgemini-fitcoach-ai/app/agent.py):

* 🎬 **Exercise Visual & Motion Guides (`generate_exercise_visual_guide`)**: Streams photorealistic exercise form guides and looping HTML5 micro-videos (`.mp4`) for dynamic exercises like Squats, Push-Ups, and Bicep Curls.
* 🎥 **Omni Video Generation (`generate_exercise_demonstration_video`)**: Generates exercise demonstration videos using `gemini-omni-flash-preview` in the `global` region. Saves video bytes to ADK Playground Artifacts via `tool_context.save_artifact` and uploads directly to Google Cloud Storage.
* 🖼️ **Imagen Image Generation (`generate_domain_item_image`)**: Generates fitness item images using `gemini-3.1-flash-lite-image` in the `global` region. Saves image bytes to ADK Playground Artifacts via `tool_context.save_artifact` and uploads directly to Google Cloud Storage.
* 🧠 **Vertex AI Memory Bank (`PreloadMemoryTool` & `add_session_to_memory`)**: Automatically preloads and persists durable user preferences, injury history, and fitness goals across sessions.
* 🗄️ **Google Cloud Firestore Catalog (`search_exercise_catalog`, `save_custom_exercise_to_catalog`)**: Connects to the Firestore `exercises` collection to search joint-friendly movements and persist custom exercise definitions.
* 📚 **Vertex AI RAG Corpus (`consult_rag_corpus`)**: Performs grounding searches across sports science literature using Vertex AI Search / RAG Corpus.
* 🥗 **USDA Nutrition Database (`search_usda_nutrition_db`)**: Queries calories, protein, carbs, fat, and fiber metrics for food items.
* 🏋️ **wger Workout Database (`search_wger_workout_database`)**: Queries the wger open workout manager API for exercise descriptions and targeted muscles.
* 🍲 **TheMealDB Recipes (`search_themealdb_recipes`)**: Searches healthy cooking recipes and meal preparation guides.
* ⚠️ **openFDA Food Safety (`search_openfda_food_safety`)**: Checks food allergen and recall warnings via openFDA API.
* 📊 **Calculators & Loggers**:
  - `calculate_bmi_and_macros`: Calculates BMI and daily macronutrient targets.
  - `get_custom_workout_routine`: Generates routines adapted for lower back, knee, or shoulder issues.
  - `get_diet_and_nutrition_plan`: Generates daily meal plans matching vegan, keto, high-protein, or balanced diets.
  - `log_workout_progress`: Logs completed sets, reps, and calculates progressive overload volume.

---

## 🏗️ Architecture & Project Structure

```
buildwithgemini-fitcoach-ai/
├── app/
│   ├── agent.py            # ADK Agent definition, system prompts, and 15 tool functions
│   └── a2ui_utils.py       # A2UI protocol callback and surface update builder
├── frontend/
│   ├── main.py             # FastAPI proxy bridging A2A web client calls to Agent Runtime
│   └── static/
│       └── index.html      # Responsive client web UI with A2UI card & video renderer
├── agents-cli-manifest.yaml # Agent Runtime deployment manifest (ADK base template)
├── demo.gif                # Looping demonstration recording
└── README.md               # Project documentation
```

---

## 🚀 Local Development & Setup Instructions

### Prerequisites
- **Python 3.11+**
- **uv** package manager
- **Google Cloud SDK (`gcloud`)** authenticated with Application Default Credentials (`gcloud auth application-default login`)

### 1. Install Dependencies
```bash
uv sync
```

### 2. Run Agent Locally
Run the ADK agent server in local development mode:
```bash
uv run agents-cli local
```

### 3. Run Web Portal Proxy Locally
In a separate terminal window, launch the web application frontend:
```bash
cd frontend
uv run uvicorn main:app --reload --port 8080
```
Open your browser to the local server port to interact with the agent interface.

---

## ☁️ Deployment Instructions

### Deploy Agent to Vertex AI Agent Runtime
```bash
uv run agents-cli deploy --project <YOUR_GCP_PROJECT_ID> --region us-east1
```

### Deploy Web Portal Proxy to Cloud Run
```bash
gcloud run deploy fitcoach-web-portal \
  --source frontend/ \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars USE_LOCAL_AGENT=false,AGENT_ENGINE_RESOURCE_NAME=projects/<PROJECT_NUMBER>/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>
```
