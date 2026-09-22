# 🏋️‍♂️ FitCoach AI

An agentic conversational fitness and workout performance coach built with the Google Agent Development Kit (ADK), Vertex AI Agent Engine, and Google Cloud Platform.

![FitCoach AI Agent Demo](demo.gif)

---

## 🌟 What FitCoach AI Does

**FitCoach AI** is an intelligent assistant that helps users plan custom exercise routines, calculate heart rate training zones, compute macronutrient splits, inspect exercise safety guides, and generate custom visual exercise guides and video demonstrations on demand.

### 🛠️ Features & Integrated Services (Verified Code Implementation)

Based on the codebase in `app/` and `agents-cli-manifest.yaml`, FitCoach AI directly implements the following capabilities:

* 🧠 **Vertex AI Memory Bank Persistence**: Integrates `generate_memories_callback` (`add_session_to_memory`) to automatically extract and persist user fitness preferences, injuries, and goals across session turns.
* 🗄️ **Google Cloud Firestore Database**: Queries and writes to the `exercises` collection for structured exercise lookup, joint-safety tag filtering, and custom exercise registration (`search_exercise_catalog`, `save_custom_exercise_to_catalog`).
* ☁️ **Google Cloud Storage (GCS) Public Media Uploads**: Uploads generated images, video clips, and visual guides directly to Cloud Storage (`fitcoach-ai-media-3812`) and returns public HTTPS URLs.
* 🖼️ **Vertex AI Image Generation**: Generates high-quality visual exercise form guides using `gemini-3.1-flash-lite-image` in the `global` region (`generate_domain_item_image`). Saves image bytes to ADK Playground Artifacts via `tool_context.save_artifact` and uploads to GCS.
* 🎬 **Vertex AI Video Generation**: Produces short exercise execution demonstration videos using `gemini-omni-flash-preview` in the `global` region (`generate_domain_item_video`). Saves video bytes to ADK Playground Artifacts via `tool_context.save_artifact` and uploads to GCS.
* 🌿 **Vertex AI RAG / Grounded Search**: Queries Nicholas Culpeper's Herbal Corpus using `vertexai.preview.rag` (with local text index fallback) for natural health and herbal remedy lookup (`consult_rag_corpus`).
* 💻 **Sandboxed Code Execution**: Executes dynamic Python calculations safely using `AgentEngineSandboxCodeExecutor` on Vertex AI Agent Engine for Karvonen target heart rate zones, 1-Rep Max estimations, BMI/BMR, and caloric macro distributions.
* 🎴 **A2UI Protocol Surface Rendering**: Employs `A2uiSchemaManager(version="0.8")` and `BasicCatalog` via `after_model_callback` (`a2ui_callback`) to render interactive card UI surfaces.
* 🥗 **External Health & Nutrition Integrations**:
  - **USDA Nutrition DB**: Searches food macros, calories, and fiber (`search_usda_nutrition_db`).
  - **wger Workout Manager API**: Looks up exercise descriptions and target muscle groups (`search_wger_workout_database`).
  - **TheMealDB API**: Searches high-protein recipes and meal preparation guides (`search_themealdb_recipes`).
  - **openFDA Safety API**: Queries food recall notices and dietary supplement safety alerts (`search_openfda_food_safety`).

### 📌 Planned / Future Capabilities (Not Yet Implemented)
* ⌚ **Real-Time Wearable Telemetry**: Live Bluetooth streaming from Apple Watch or Garmin heart rate monitors (Planned for future release).

---

## 📐 Project Structure

```
fitcoach-ai/
├── app/                        # Core ADK Agent Implementation
│   ├── agent.py                # ReAct agent logic, tools, and callbacks
│   ├── a2ui_utils.py           # A2UI v0.8 schema manager & surface builder
│   ├── fast_api_app.py         # Agent FastAPI backend entrypoint
│   └── app_utils/              # Application helpers and code execution sandbox
├── frontend/                   # Web Chat Frontend & Proxy
│   ├── main.py                 # FastAPI proxy connecting to Agent Engine over A2A
│   ├── static/
│   │   └── index.html          # Theme-matched chat UI, A2UI renderer & prompt chips
│   ├── Dockerfile              # Container spec for Cloud Run deployment
│   └── requirements.txt        # Frontend proxy dependencies
├── data/                       # Grounded corpus and cached catalog data
├── tests/                      # Unit and integration test suites
├── agents-cli-manifest.yaml    # Agents CLI configuration manifest
├── pyproject.toml              # Dependencies managed by uv
└── demo.gif                    # Animated walkthrough demo
```

---

## 🚀 Local Setup & Execution Guide

### 1. Prerequisites
- **Python**: `>= 3.11`
- **uv**: Package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **agents-cli**: Installed via `uv tool install google-agents-cli`
- **Google Cloud SDK**: Authenticated to GCP project

### 2. Install Project Dependencies
Run from the project root:
```bash
uv sync
```

### 3. Start Local Agent Playground
Launch the interactive ADK playground locally:
```bash
agents-cli playground
```
Alternatively, launch directly with ADK CLI:
```bash
uv run adk web --port 8080 --allow_origins "*" --reload_agents
```

### 4. Run Web Frontend Proxy Locally
To run the minimal FastAPI proxy and plain HTML chat UI locally:
```bash
cd frontend
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/<LOCATION>/reasoningEngines/<ENGINE_ID>"
export AGENT_DIRECTORY="app"
uv run python main.py
```

### 5. Running Tests & Linting
Run unit and integration test suites:
```bash
uv run pytest tests/unit tests/integration
```
Run code quality checks:
```bash
agents-cli lint
```

---

## 📦 Deployment Commands

### Deploy Agent to Vertex AI Agent Engine
```bash
agents-cli deploy
```

### Deploy Web Frontend to Cloud Run
```bash
gcloud run deploy fitcoach-frontend \
  --source ./frontend \
  --region us-east1 \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUMBER>/locations/<LOCATION>/reasoningEngines/<ENGINE_ID>",AGENT_DIRECTORY="app" \
  --allow-unauthenticated \
  --quiet
```
