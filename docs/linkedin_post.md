🚀 **From zero to a production AI fitness coach — built at Google's "Building with Gemini" event, in collaboration with Cognizant.**

Forget generic chatbot fitness advice. **FitCoach AI** is a conversational performance coach that *reasons* like a real trainer — pulling from exercise science, live nutrition data, and even classical herbal medicine texts — and answers not with walls of text, but with a rich, interactive UI.

Built on **Google's Agent Development Kit (ADK)** + **Gemini 2.5 Flash**, wrapped in a glassmorphic **A2UI** interface.

⚡ **What it can do in a single session:**
🎬 Generate animated exercise form guides on the fly — powered by **`gemini-2.5-flash-image`**
🩹 Adapt routines around injuries (wrist-friendly push-up variants, etc.)
📋 Build a custom workout plan for your fitness level
📊 Log sets, reps & track performance over time
🥗 Break down real ingredient macros (USDA FoodData Central)
🍲 Recommend high-protein vegetarian recipes (TheMealDB)
⚠️ Flag live supplement recalls/safety warnings (openFDA)
🌿 Suggest herbal recovery remedies via a RAG pipeline built on a classical herbal text

🧠 **Under the hood:** Vertex AI Memory Bank for cross-session memory, Firestore for the exercise catalog, Cloud Storage for generated media, and 14 autonomous tools the agent chooses between based on what you actually ask.

📈 **The repo tells the whole build story across 3 branches:**
1️⃣ **main** → the working MVP: every core tool wired end-to-end
2️⃣ **feature/fitcoach-ai-omni-v2** → hardened video generation + real A2UI rendering for animated micro-guides
3️⃣ **feature/fitcoach-ai-adk-release** → the production cut: centralized config, glassmorphic UI overhaul, full architecture docs

Zero to production, one commit at a time. 👇

Grateful to Google and Cognizant for the platform and the push to build this end-to-end.

🎥 Demo video attached
🔗 GitHub: https://github.com/AjinkyaHimanshu/buildwithgemini-fitcoach-ai

#BuildingWithGemini #GoogleADK #Gemini #Cognizant #AI #AgenticAI #VertexAI #GenerativeAI #SoftwareEngineering
