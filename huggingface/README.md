---
title: AI Study Assistant
emoji: 🧠
colorFrom: indigo
colorTo: pink
sdk: docker
pinned: false
---

# Agentic AI Study Assistant (Flask Version)

An interactive learning companion for students built using **Python, Flask, HTML/CSS/JS, LangChain, and Groq API**.

This app is designed to be hosted on Hugging Face Spaces using the **Docker SDK**.

## 🚀 Features

1. **💬 Ask Doubt**:
   - A conversational agent that helps students understand academic topics.
   - Equipped with tools like **Wikipedia**, **DuckDuckGo Web Search**, and a **Calculator** to answer factual and numerical questions.
   - Resilient design: catches rate limits or API overloads and falls back to alternate tools automatically.

2. **📝 Generate Notes**:
   - Generates beautifully structured markdown study sheets tailored to target grade levels.
   - Renders interactive knowledge mindmaps live using **Mermaid.js** directly in the DOM.
   - Includes a direct markdown export/download button.

3. **🧠 Create Quiz**:
   - Generates multiple-choice quizzes with real-time scoring.
   - Outputs clear explanations of correct answers and marks user options with dynamic success/error alert boxes.

## ⚙️ Hugging Face Space Configuration

To run this app on your own Hugging Face Space:

1. **Create a Space**:
   Go to your Space's **New Space** creator -> choose **Docker** as the SDK (instead of Streamlit or Gradio) -> select the **Blank** template -> click **Create Space**.

2. **Set up Secrets**:
   Go to your Space's **Settings** tab -> **Variables and secrets** section -> **New secret**, and add:
   * **Key**: `GROQ_API_KEY`
   * **Value**: *[Your Groq API Key]* (Get one for free at [console.groq.com](https://console.groq.com))

3. **Deploy Files**:
   Push the files inside this directory (including `app.py`, `templates/`, `static/`, `Dockerfile`, `requirements.txt`, and this `README.md`) to the Hugging Face space repository. 
   The Docker container will build automatically, bind to port `7860`, and serve the Flask app!
