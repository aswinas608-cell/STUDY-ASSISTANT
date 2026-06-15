---
title: AI Study Assistant
emoji: 🧠
colorFrom: indigo
colorTo: pink
sdk: streamlit
sdk_version: 1.30.0
app_file: app.py
pinned: false
---

# Agentic AI Study Assistant

An interactive learning companion for students built using **Python, Streamlit, LangChain, and Groq API**.

This app is hosted on Hugging Face Spaces. It uses high-speed open-weights models (like Llama 3.3) to power its agentic features.

## 🚀 Features

1. **💬 Ask Doubt**:
   - A conversational agent that helps students understand academic topics.
   - Equipped with tools like **Wikipedia**, **DuckDuckGo Web Search**, and a **Calculator** to answer factual and numerical questions.
   - Resilient design: catches rate limits or API overloads and falls back to alternate tools automatically.

2. **📝 Generate Notes**:
   - Generates beautifully structured markdown study sheets tailored to target grade levels.
   - Renders interactive knowledge mindmaps live using **Mermaid.js**.
   - Includes a direct markdown export/download button.

3. **🧠 Create Quiz**:
   - Generates multiple-choice quizzes with real-time scoring.
   - Outputs clear explanations of correct answers and marks user options with dynamic success/error alert boxes.

## ⚙️ Hugging Face Space Configuration

To run this app on your own Hugging Face Space:

1. **Set up Secrets**:
   Go to your Space's **Settings** tab -> **Variables and secrets** section -> **New secret**, and add:
   * **Key**: `GROQ_API_KEY`
   * **Value**: *[Your Groq API Key]* (Get one for free at [console.groq.com](https://console.groq.com))

2. **Required Files**:
   Ensure the following files are in the repository root (which are pre-packaged in this folder):
   * `app.py`
   * `agent.py`
   * `notes_generator.py`
   * `quiz_creator.py`
   * `requirements.txt`
   * `README.md` (containing this configuration header)
