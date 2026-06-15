import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Import our custom AI modules
from agent import get_study_agent
from notes_generator import generate_study_notes
from quiz_creator import generate_quiz

# Load environment variables on startup
load_dotenv()

app = Flask(__name__)

def resolve_api_key(client_key: str) -> str:
    """
    Returns the key supplied by the client, or falls back to the local environment variable.
    Raises ValueError if no key is available.
    """
    key = client_key.strip() if client_key else ""
    if not key:
        key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise ValueError("Missing Groq API Key. Please provide it in the sidebar configuration.")
    return key

# Route to serve Front-end SPA
@app.route("/")
def index():
    return render_template("index.html")

# Endpoint to check if GROQ_API_KEY is pre-configured on the server env
@app.route("/api/config", methods=["GET"])
def get_config():
    env_key = os.getenv("GROQ_API_KEY", "").strip()
    return jsonify({
        "has_key": bool(env_key)
    })

# API Endpoint: Conversational Doubt-Solving Agent
@app.route("/api/chat", methods=["POST"])
def api_chat():
    try:
        data = request.json or {}
        query = data.get("query", "").strip()
        history = data.get("history", [])
        client_key = data.get("api_key", "")
        model = data.get("model", "llama-3.3-70b-versatile")

        if not query:
            return jsonify({"error": "Empty search query. Please specify a doubt."}), 400

        # Retrieve key
        api_key = resolve_api_key(client_key)

        # Format history list into string context for the ReAct agent input
        formatted_history = ""
        for msg in history:
            role_name = "Student" if msg["role"] == "user" else "Assistant"
            formatted_history += f"{role_name}: {msg['content']}\n"

        # Instantiate agent executor
        agent_executor = get_study_agent(api_key, model)

        # Consolidate instructions, history, and doubt
        consolidated_input = (
            "System Instruction: You are an engaging, pedagogical, and highly supportive AI Study Assistant. "
            "Help the student understand the material deeply by explaining concepts step-by-step. Use beautiful markdown formatting.\n\n"
            f"Previous Chat History:\n{formatted_history if formatted_history else '(No history yet)'}\n\n"
            f"Current Student Doubt: {query}"
        )

        # Run agent
        response = agent_executor.invoke({"input": consolidated_input})
        output_text = response.get("output", "")

        return jsonify({
            "output": output_text
        })

    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred while executing the doubt solver. Details: {str(e)}"}), 500

# API Endpoint: Study Notes Curation
@app.route("/api/notes", methods=["POST"])
def api_notes():
    try:
        data = request.json or {}
        topic = data.get("topic", "").strip()
        audience = data.get("audience", "High School")
        depth = data.get("depth", "Detailed Explanations")
        client_key = data.get("api_key", "")
        model = data.get("model", "llama-3.3-70b-versatile")

        if not topic:
            return jsonify({"error": "Topic name is required."}), 400

        # Retrieve key
        api_key = resolve_api_key(client_key)

        # Generate Notes
        notes_content = generate_study_notes(api_key, topic, audience, depth, model)

        return jsonify({
            "notes": notes_content
        })

    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred while generating study notes. Details: {str(e)}"}), 500

# API Endpoint: Quiz Creation
@app.route("/api/quiz", methods=["POST"])
def api_quiz():
    try:
        data = request.json or {}
        topic = data.get("topic", "").strip()
        count = int(data.get("count", 5))
        difficulty = data.get("difficulty", "Medium")
        client_key = data.get("api_key", "")
        model = data.get("model", "llama-3.3-70b-versatile")

        if not topic:
            return jsonify({"error": "Quiz topic name is required."}), 400

        # Retrieve key
        api_key = resolve_api_key(client_key)

        # Generate Quiz
        quiz_data = generate_quiz(api_key, topic, count, difficulty, model)

        return jsonify({
            "quiz": quiz_data
        })

    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred while generating the quiz. Details: {str(e)}"}), 500

if __name__ == "__main__":
    # Start Flask Web Server
    print("Starting Flask AI Study Assistant server...")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
