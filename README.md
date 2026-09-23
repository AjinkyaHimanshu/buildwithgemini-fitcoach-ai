# 🏋️ FitCoach AI — Conversational Fitness & Performance Agent

FitCoach AI is an frontier conversational performance coach built on the **Google Agent Development Kit (ADK)** framework. It delivers personalized exercise form guides, injury adaptations, custom workout routines, performance logging, USDA macro calculations, Indian vegetarian recipe search, openFDA supplement safety checks, and herbal joint recovery guidance — rendered via an interactive **A2UI** glassmorphic interface.

---

## 🎬 Agent Demonstration

![FitCoach AI Agent Demo](assets/fitcoach_ai_agent_demo.gif)

---

## 💬 Prompts Featured in the Demo Sequence

The demo video above demonstrates 9 core capabilities centered around a **Push-up** performance & recovery workflow for an Indian vegetarian athlete:

1. **Animated Form Guide**:
   > *"Can you show me an animated GIF of proper form for Push-ups?"*
2. **Injury Adaptation & Joint Safety**:
   > *"My wrists hurt when doing Push-ups on the floor—what's a safer, wrist-friendly modification?"*
3. **Custom Workout Routine**:
   > *"Can you build me a 30-minute home Push-up workout routine tailored for a beginner?"*
4. **Workout Performance Logging**:
   > *"I just finished my session—can you log 4 sets of 12 Push-ups at bodyweight?"*
5. **Exercise Anatomy Database Search (wger API)**:
   > *"What chest and shoulder muscles do Push-ups target?"*
6. **USDA Nutrition & Macro Breakdown**:
   > *"How much protein and calories are in 200 grams of Paneer and 100 grams of cooked Chana (chickpeas) after my Push-up workout?"*
7. **Healthy Vegetarian Recipe Search (TheMealDB API)**:
   > *"Can you find me healthy high-protein Indian vegetarian recipes like Dal or Paneer for post-workout dinner?"*
8. **Food & Supplement Safety Alerts (openFDA API)**:
   > *"Are there any FDA safety warnings or recalls on plant-based vegetarian protein powders?"*
9. **Herbal Recovery & Soreness (Culpeper RAG Knowledge Base)**:
   > *"What natural herbs or herbal teas help soothe wrist joint soreness and speed recovery after Push-ups?"*

---

## 🛠️ Implemented Architecture & Google Cloud Integrations

FitCoach AI connects frontier LLMs with domain tools, structured databases, and Google Cloud services:

* **Google Agent Development Kit (ADK)**: Core agent orchestration framework using `gemini-2.5-flash`.
* **Memory Bank & Conversation Context**: Multi-turn session context tracking athlete gender preferences, conversation history, and user profile state.
* **Google Cloud Firestore**: Persists user profiles and workout performance logs (sets, reps, bodyweight).
* **Google Cloud Storage (GCS)**: Stores public high-definition loopable `.gif` motion guides for exercise form demonstrations.
* **Gemini GenAI Multimodal Image Generation (`gemini-2.5-flash-image`)**: Dynamic generation and fallback handling for custom exercise visual guides.
* **Culpeper Herbal Vector Knowledge Base (RAG)**: Retrieval-augmented generation for natural herbal remedies and joint recovery.
* **wger Exercise Database Integration**: Real-time anatomical muscle targets and exercise execution instructions.
* **USDA FoodData Central API**: Real-time macronutrient breakdown (calories, protein, carbs, fats) for raw and cooked ingredients.
* **TheMealDB Recipe Search API**: High-protein vegetarian recipe discovery for post-workout meal planning.
* **openFDA Drug & Supplement Safety API**: Real-time warning and recall alerts for protein powders and supplements.
* **A2UI Rich Canvas Framework**: Generates structured, responsive glassmorphic cards (`Card`, `Column`, `Row`, `Text`, `Image`).

---

## 🚀 Local Setup & Execution Guide

### Prerequisites
* Python 3.11+
* [`uv`](https://docs.astral.sh/uv/) package manager
* Google Cloud SDK (`gcloud`) with active Vertex AI and Firestore permissions

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/your-org/fitcoach-ai.git
cd fitcoach-ai
uv sync
```

### 2. Environment Configuration
Set your Google Cloud credentials and environment variables:
```bash
export PROJECT_ID="your-gcp-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GCS_MEDIA_BUCKET="fitcoach-ai-media-your-project-id"
```

### 3. Run Web Application Locally
Start the FastAPI server hosting the agent web portal:
```bash
uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8080
```
Open your browser to test the local interface.

### 4. Deploy to Vertex AI Agent Runtime
Deploy the agent reasoning engine using `agents-cli`:
```bash
uv run agents-cli deploy --project $PROJECT_ID --region us-central1
```

---

## 📜 License
Licensed under the Apache License, Version 2.0.
