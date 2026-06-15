import os
import streamlit as st
from dotenv import load_dotenv

# Import and reload custom modules to prevent Streamlit module caching issues
import importlib
import agent
import notes_generator
import quiz_creator

importlib.reload(agent)
importlib.reload(notes_generator)
importlib.reload(quiz_creator)

from agent import get_study_agent
from notes_generator import generate_study_notes, extract_mermaid_code
from quiz_creator import generate_quiz

# Load environment variables
load_dotenv()

# Set up Streamlit Page config first
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling using CSS
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Main font override */
html, body, [class*="css"], .stMarkdown {
    font-family: 'Outfit', sans-serif;
}

/* Gradient Header */
.main-header {
    background: linear-gradient(135deg, #a78bfa 0%, #ec4899 50%, #f43f5e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
    letter-spacing: -0.05rem;
}

.sub-header {
    color: #94a3b8;
    font-size: 1.15rem;
    margin-bottom: 2rem;
    font-weight: 300;
}

/* Glassmorphic Container Cards */
.glass-card {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 20px;
    padding: 30px;
    margin-bottom: 25px;
    box-shadow: 0 10px 30px 0 rgba(0, 0, 0, 0.25);
}

.badge {
    background: linear-gradient(90deg, rgba(167, 139, 250, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
    color: #e879f9;
    border: 1px solid rgba(236, 72, 153, 0.3);
    padding: 6px 14px;
    border-radius: 50px;
    font-weight: 500;
    font-size: 0.85rem;
    display: inline-block;
    margin-bottom: 15px;
}

/* Custom button styles */
div.stButton > button {
    background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
    width: 100%;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%);
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);
    transform: translateY(-2px);
    color: white;
}

/* Custom text inputs */
.stTextInput > div > div > input {
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background-color: rgba(255, 255, 255, 0.02) !important;
}

/* Chat Input customizations */
.stChatInputContainer {
    border-radius: 16px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    background-color: rgba(15, 23, 42, 0.6) !important;
    backdrop-filter: blur(10px) !important;
}

/* Quiz styling */
.quiz-card {
    background: rgba(139, 92, 246, 0.03);
    border: 1px solid rgba(139, 92, 246, 0.1);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 15px;
}

.correct-box {
    border-left: 5px solid #22c55e;
    background-color: rgba(34, 197, 94, 0.05);
    padding: 15px;
    border-radius: 0 10px 10px 0;
    margin-top: 10px;
}

.wrong-box {
    border-left: 5px solid #ef4444;
    background-color: rgba(239, 68, 68, 0.05);
    padding: 15px;
    border-radius: 0 10px 10px 0;
    margin-top: 10px;
}

/* Sidebar styling */
.css-1d391kg {
    background-color: #0b0f19 !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "notes" not in st.session_state:
    st.session_state.notes = None
if "notes_topic" not in st.session_state:
    st.session_state.notes_topic = ""
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "quiz_topic" not in st.session_state:
    st.session_state.quiz_topic = ""

# Sidebar Content
st.sidebar.markdown("<h2 style='text-align: center; color: white;'>🧠 Study Buddy</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #64748b; font-size:0.9rem;'>Your Agentic AI Study Assistant</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Navigation Selector
menu_options = ["💬 Ask Doubt", "📝 Generate Notes", "🧠 Create Quiz"]
choice = st.sidebar.radio("Navigate Tasks:", menu_options)

st.sidebar.markdown("---")
st.sidebar.subheader("Configuration")

# API Key Retrieval
env_key = os.getenv("GROQ_API_KEY", "")
api_key = env_key

if not env_key:
    api_key = st.sidebar.text_input("Groq API Key:", type="password", help="Enter your Groq API key to activate the assistant.")
    if not api_key:
        st.sidebar.warning("⚠️ Groq API Key required to run this app.")
else:
    st.sidebar.success("🔑 Groq API Key loaded from .env")

# LLM Model Selector
selected_model = st.sidebar.selectbox(
    "Choose LLM Model:",
    ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "llama3-70b-8192", "llama3-8b-8192"],
    index=0,
    help="Select the Groq model to power your study assistant."
)

st.sidebar.markdown("---")
# Reset Application Session State
if st.sidebar.button("Clear Application Cache / Reset"):
    st.session_state.messages = []
    st.session_state.notes = None
    st.session_state.notes_topic = ""
    st.session_state.quiz_data = None
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_topic = ""
    st.rerun()

# ----------------- PAGE IMPLEMENTATIONS -----------------

# Dynamic Page Title & Description helper
def render_header(title, desc, badge_text):
    st.markdown(f'<div class="badge">{badge_text}</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="main-header">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{desc}</p>', unsafe_allow_html=True)

# Helper to render Mermaid diagrams via a clean iframe
def render_mermaid(code_string):
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
      <script>
        mermaid.initialize({{
          startOnLoad: true,
          theme: 'dark',
          securityLevel: 'loose',
          themeVariables: {{
            background: '#0f172a',
            primaryColor: '#7c3aed',
            primaryTextColor: '#ffffff',
            lineColor: '#ec4899',
            nodeBorder: '#ec4899'
          }}
        }});
      </script>
      <style>
        body {{
          background-color: #0f172a;
          margin: 0;
          display: flex;
          justify-content: center;
          align-items: center;
          color: white;
          font-family: 'Outfit', sans-serif;
          overflow: auto;
        }}
        .mermaid {{
          background-color: #0f172a;
          border: 1px solid rgba(255, 255, 255, 0.05);
          border-radius: 16px;
          padding: 25px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
          min-width: 90%;
        }}
      </style>
    </head>
    <body>
      <div class="mermaid">
{code_string}
      </div>
    </body>
    </html>
    """
    st.components.v1.html(html_code, height=500, scrolling=True)

# VIEW 1: ASK DOUBT
if choice == "💬 Ask Doubt":
    render_header("Ask Your Doubts", "Type in any academic question. The assistant uses search, Wikipedia, and math solvers to get precise step-by-step answers.", "CONVERSATIONAL AGENT")
    
    if not api_key:
        st.info("💡 Please provide your Groq API Key in the sidebar to begin asking questions.")
    else:
        # Render historical chat messages
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        if prompt := st.chat_input("E.g. Explain quantum tunneling simply, or solve: sqrt(256) * 12 + 55"):
            # Display user query
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Show assistant thinking state and generate answer
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                with st.spinner("Analyzing doubt and executing tools..."):
                    try:
                        agent_executor = get_study_agent(api_key, selected_model)
                        
                        # Format session chat history for the agent context
                        formatted_history = ""
                        # Only take last 10 messages to avoid context bloat
                        for m in st.session_state.messages[-10:-1]:
                            role_name = "Student" if m["role"] == "user" else "Assistant"
                            formatted_history += f"{role_name}: {m['content']}\n"
                        
                        # Build consolidated input with system instructions and chat history
                        consolidated_input = (
                            "System Instruction: You are an engaging, pedagogical, and highly supportive AI Study Assistant. "
                            "Help the student understand the material deeply by explaining concepts step-by-step. Use beautiful markdown formatting.\n\n"
                            f"Previous Chat History:\n{formatted_history if formatted_history else '(No history yet)'}\n\n"
                            f"Current Student Doubt: {prompt}"
                        )
                        
                        # Call LangChain agent
                        response = agent_executor.invoke({
                            "input": consolidated_input
                        })
                        
                        output_text = response["output"]
                        message_placeholder.markdown(output_text)
                        st.session_state.messages.append({"role": "assistant", "content": output_text})
                        
                    except Exception as e:
                        error_msg = f"An error occurred while answering your doubt. \n\n*Error details: {str(e)}*"
                        message_placeholder.error(error_msg)

# VIEW 2: GENERATE NOTES
elif choice == "📝 Generate Notes":
    render_header("Study Notes Generator", "Generate comprehensive study notes along with summary checklists and interactive mindmaps.", "CURRICULUM WRITER")
    
    if not api_key:
        st.info("💡 Please provide your Groq API Key in the sidebar to generate study notes.")
    else:
        # Layout input fields
        col1, col2 = st.columns(2)
        with col1:
            topic = st.text_input("Enter Topic Name:", value=st.session_state.notes_topic, placeholder="E.g. Photosynthesis, Cellular Respiration, Cold War")
        with col2:
            audience = st.selectbox("Target Grade/Audience:", ["Elementary School", "Middle School", "High School", "Undergraduate College", "General/Professional"])
            
        depth = st.select_slider("Level of Detail:", options=["Summary Outline", "Detailed Explanations", "Comprehensive Guide"])
        
        # Action button
        if st.button("Create Notes & Mindmap"):
            if not topic:
                st.warning("⚠️ Please specify a topic.")
            else:
                with st.spinner(f"Curating study notes on '{topic}'..."):
                    st.session_state.notes_topic = topic
                    notes_content = generate_study_notes(api_key, topic, audience, depth, selected_model)
                    st.session_state.notes = notes_content
        
        # Display notes if they exist in session state
        if st.session_state.notes:
            st.markdown("---")
            
            # Setup Tabs: 📄 Read Notes, 🗺️ Visual Mindmap
            tab1, tab2 = st.tabs(["📄 Study Notes Document", "🗺️ Visual Concept Mindmap"])
            
            with tab1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown(st.session_state.notes)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Download button
                st.download_button(
                    label="📥 Download Study Notes (.md)",
                    data=st.session_state.notes,
                    file_name=f"Study_Notes_{st.session_state.notes_topic.replace(' ', '_')}.md",
                    mime="text/markdown"
                )
                
            with tab2:
                st.subheader("Interactive Knowledge Mindmap")
                st.caption("A hierarchical visual mapping of key ideas. Hover and scroll to explore.")
                mermaid_code = extract_mermaid_code(st.session_state.notes)
                if mermaid_code:
                    render_mermaid(mermaid_code)
                else:
                    st.warning("⚠️ Visual Mindmap could not be loaded. Please ensure the model output generated the mermaid block correctly.")

# VIEW 3: CREATE QUIZ
elif choice == "🧠 Create Quiz":
    render_header("Interactive MCQ Quiz Creator", "Generate quizzes based on study topics. Select answers, submit, and get instant detailed explanations.", "KNOWLEDGE EVALUATOR")
    
    if not api_key:
        st.info("💡 Please provide your Groq API Key in the sidebar to generate quizzes.")
    else:
        # Layout input fields
        col1, col2, col3 = st.columns(3)
        with col1:
            quiz_topic = st.text_input("Quiz Topic:", value=st.session_state.quiz_topic, placeholder="E.g. Newtonian Physics, SQL Joins, Ancient Rome")
        with col2:
            num_q = st.slider("Number of Questions:", min_value=1, max_value=10, value=5)
        with col3:
            difficulty = st.selectbox("Difficulty Level:", ["Easy", "Medium", "Hard"])
            
        if st.button("Generate Quiz"):
            if not quiz_topic:
                st.warning("⚠️ Please specify a quiz topic.")
            else:
                with st.spinner(f"Formulating {num_q} '{difficulty}' questions on {quiz_topic}..."):
                    st.session_state.quiz_topic = quiz_topic
                    st.session_state.quiz_data = generate_quiz(api_key, quiz_topic, num_q, difficulty, selected_model)
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    st.rerun()
                    
        # Check if quiz exists in session state
        if st.session_state.quiz_data:
            st.markdown("---")
            st.markdown(f"### 📋 {st.session_state.quiz_data.get('title', 'Academic Evaluation Quiz')}")
            
            questions = st.session_state.quiz_data.get("questions", [])
            
            # Loop through questions and render radio options
            for idx, q in enumerate(questions):
                # Render question card
                st.markdown(f'<div class="quiz-card">', unsafe_allow_html=True)
                st.markdown(f"**Question {idx + 1}:** {q['question']}")
                
                # Handle selection logic
                options = q["options"]
                
                # Check if user has answered before, else default to None selection (blank index)
                # To support None selection in Streamlit radio, we can use selectbox or radio with an index
                current_ans = st.session_state.quiz_answers.get(idx, None)
                
                # Find index of previous selection
                default_idx = 0
                if current_ans in options:
                    default_idx = options.index(current_ans)
                
                # Enable input only if not submitted yet
                selected = st.radio(
                    f"Select answer for Question {idx + 1}:",
                    options,
                    index=default_idx,
                    key=f"q_radio_{idx}",
                    disabled=st.session_state.quiz_submitted,
                    label_visibility="collapsed"
                )
                
                # Save state
                if not st.session_state.quiz_submitted:
                    st.session_state.quiz_answers[idx] = selected
                
                # Render explanations if submitted
                if st.session_state.quiz_submitted:
                    user_selection = st.session_state.quiz_answers.get(idx)
                    correct_selection = q["correct_answer"]
                    
                    if user_selection == correct_selection:
                        st.markdown(
                            f'<div class="correct-box"><b>✅ Correct!</b> Your choice: <i>{user_selection}</i><br><br>'
                            f'<b>Explanation:</b> {q["explanation"]}</div>', 
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f'<div class="wrong-box"><b>❌ Incorrect.</b> Your choice: <i>{user_selection}</i><br>'
                            f'<b>Correct Answer:</b> <i>{correct_selection}</i><br><br>'
                            f'<b>Explanation:</b> {q["explanation"]}</div>', 
                            unsafe_allow_html=True
                        )
                st.markdown('</div>', unsafe_allow_html=True)
                
            # Submit button
            if not st.session_state.quiz_submitted:
                if st.button("Submit All Answers"):
                    st.session_state.quiz_submitted = True
                    st.rerun()
            else:
                # Calculate score
                score = 0
                for idx, q in enumerate(questions):
                    if st.session_state.quiz_answers.get(idx) == q["correct_answer"]:
                        score += 1
                
                percentage = int((score / len(questions)) * 100)
                
                # Score Card
                st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
                st.markdown(f"<h2>Your Final Score: {score} / {len(questions)} ({percentage}%)</h2>", unsafe_allow_html=True)
                
                if percentage == 100:
                    st.balloons()
                    st.markdown("🏆 **Perfect Score! Outstanding work!**")
                elif percentage >= 70:
                    st.markdown("🌟 **Great job! You have a solid grasp of this topic.**")
                else:
                    st.markdown("📖 **Keep reviewing! Try asking Study Buddy for clarification on missed concepts.**")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.button("Retake / Try Another Quiz"):
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                    st.rerun()
