document.addEventListener("DOMContentLoaded", () => {
    // App State
    const state = {
        currentView: "doubt",
        chatHistory: [], // stores message objects {role: "user"/"assistant", content: ""}
        quizData: null,
        quizAnswers: {}, // index -> selected option string
        quizSubmitted: false,
        generatedNotes: ""
    };

    // Initialize Mermaid
    if (typeof mermaid !== "undefined") {
        mermaid.initialize({
            startOnLoad: false,
            theme: "dark",
            securityLevel: "loose",
            themeVariables: {
                background: "#0f172a",
                primaryColor: "#7c3aed",
                primaryTextColor: "#ffffff",
                lineColor: "#ec4899",
                nodeBorder: "#ec4899"
            }
        });
    }

    // DOM Elements
    const views = document.querySelectorAll(".content-view");
    const navItems = document.querySelectorAll(".nav-item");
    const apiKeyInput = document.getElementById("apiKeyInput");
    const apiKeyStatus = document.getElementById("apiKeyStatus");
    const modelSelect = document.getElementById("modelSelect");
    const resetBtn = document.getElementById("resetBtn");
    const loadingOverlay = document.getElementById("loadingOverlay");
    const loadingMessage = document.getElementById("loadingMessage");

    // Load API Key from localStorage if exists
    if (localStorage.getItem("groq_api_key")) {
        apiKeyInput.value = localStorage.getItem("groq_api_key");
    }

    // Check .env key existence on load
    checkEnvKey();

    // ----------------- ROUTING / VIEW CHANGING -----------------
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetView = item.getAttribute("data-view");
            switchView(targetView);
        });
    });

    function switchView(viewName) {
        state.currentView = viewName;
        
        // Update navigation active state
        navItems.forEach(item => {
            if (item.getAttribute("data-view") === viewName) {
                item.classList.add("active");
            } else {
                item.classList.remove("active");
            }
        });

        // Toggle visibility of views
        views.forEach(view => {
            if (view.id === `view-${viewName}`) {
                view.classList.add("active");
            } else {
                view.classList.remove("active");
            }
        });
    }

    // Save API key on change
    apiKeyInput.addEventListener("input", () => {
        localStorage.setItem("groq_api_key", apiKeyInput.value.trim());
        checkEnvKey();
    });

    // Reset Application Button
    resetBtn.addEventListener("click", () => {
        if (confirm("Are you sure you want to clear the chat history and reset all views?")) {
            localStorage.removeItem("groq_api_key");
            apiKeyInput.value = "";
            state.chatHistory = [];
            state.quizData = null;
            state.quizAnswers = {};
            state.quizSubmitted = false;
            state.generatedNotes = "";

            // Reset Chat HTML
            document.getElementById("chatMessages").innerHTML = `
                <div class="message assistant-message">
                    Hi there! I am your AI Study Assistant. Ask me any conceptual question or paste a math problem, and we'll break it down together!
                </div>
            `;
            
            // Reset Notes HTML
            document.getElementById("notesTopic").value = "";
            document.getElementById("notesOutputContainer").classList.add("hidden");
            
            // Reset Quiz HTML
            document.getElementById("quizTopic").value = "";
            document.getElementById("quizDisplayContainer").classList.add("hidden");

            checkEnvKey();
            switchView("doubt");
            alert("App cache reset successfully.");
        }
    });

    // Helper: Show/Hide Loading
    function showLoading(msg) {
        loadingMessage.textContent = msg;
        loadingOverlay.classList.remove("hidden");
    }

    function hideLoading() {
        loadingOverlay.classList.add("hidden");
    }

    // Get current API key to use (priority: custom input -> env variable)
    function getApiKey() {
        return apiKeyInput.value.trim();
    }

    // Hitting API to see if GROQ_API_KEY is configured in backend environment
    async function checkEnvKey() {
        try {
            const res = await fetch("/api/config");
            const data = await res.json();
            
            if (getApiKey()) {
                apiKeyStatus.textContent = "🔑 Using custom API Key";
                apiKeyStatus.className = "status-badge status-loaded";
            } else if (data.has_key) {
                apiKeyStatus.textContent = "🔑 Groq API Key loaded from .env";
                apiKeyStatus.className = "status-badge status-loaded";
            } else {
                apiKeyStatus.textContent = "⚠️ Groq API Key missing";
                apiKeyStatus.className = "status-badge status-missing";
            }
        } catch (e) {
            console.error("Config check failed", e);
        }
    }


    // ----------------- VIEW 1: ASK DOUBT CHAT LOGIC -----------------
    const chatInput = document.getElementById("chatInput");
    const sendChatBtn = document.getElementById("sendChatBtn");
    const chatMessages = document.getElementById("chatMessages");

    sendChatBtn.addEventListener("click", submitChat);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") submitChat();
    });

    async function submitChat() {
        const query = chatInput.value.trim();
        if (!query) return;

        // Clear input
        chatInput.value = "";

        // Add user bubble
        appendMessage("user", query);
        state.chatHistory.push({ role: "user", content: query });

        // Add dummy assistant loading bubble
        const loadingBubble = appendMessage("assistant", "Let me search and compute step-by-step...", true);

        try {
            const payload = {
                query: query,
                history: state.chatHistory.slice(0, -1), // send history up to before this message
                api_key: getApiKey(),
                model: modelSelect.value
            };

            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            
            // Remove loading bubble
            loadingBubble.remove();

            if (res.ok) {
                appendMessage("assistant", data.output);
                state.chatHistory.push({ role: "assistant", content: data.output });
            } else {
                appendMessage("assistant", `❌ **Error:** ${data.error || "Failed to get response."}`);
            }
        } catch (err) {
            loadingBubble.remove();
            appendMessage("assistant", `❌ **Network Error:** Could not connect to Flask server. Details: ${err.message}`);
        }
    }

    function appendMessage(role, text, isLoading = false) {
        const bubble = document.createElement("div");
        bubble.className = `message ${role}-message`;
        
        if (isLoading) {
            bubble.innerHTML = `<span class="loading-dots">${text}</span>`;
        } else {
            // Render Markdown using marked
            bubble.innerHTML = marked.parse(text);
        }
        
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return bubble;
    }


    // ----------------- VIEW 2: STUDY NOTES GENERATOR -----------------
    const generateNotesBtn = document.getElementById("generateNotesBtn");
    const notesTopicInput = document.getElementById("notesTopic");
    const notesAudienceSelect = document.getElementById("notesAudience");
    const notesDepthSelect = document.getElementById("notesDepth");
    const notesOutputContainer = document.getElementById("notesOutputContainer");
    const notesMarkdownBody = document.getElementById("notesMarkdownBody");
    const downloadNotesBtn = document.getElementById("downloadNotesBtn");
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    // Tab Switching
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            
            tabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            tabContents.forEach(content => {
                if (content.id === targetTab) {
                    content.classList.add("active");
                } else {
                    content.classList.remove("active");
                }
            });
            
            // Trigger mermaid render if canvas tab selected
            if (targetTab === "tab-mindmap") {
                renderMermaidMindmap();
            }
        });
    });

    generateNotesBtn.addEventListener("click", async () => {
        const topic = notesTopicInput.value.trim();
        if (!topic) {
            alert("Please specify a topic name.");
            return;
        }

        showLoading(`Curating study notes on '${topic}'...`);

        try {
            const payload = {
                topic: topic,
                audience: notesAudienceSelect.value,
                depth: notesDepthSelect.value,
                api_key: getApiKey(),
                model: modelSelect.value
            };

            const res = await fetch("/api/notes", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            hideLoading();

            if (res.ok) {
                state.generatedNotes = data.notes;
                notesMarkdownBody.innerHTML = marked.parse(data.notes);
                notesOutputContainer.classList.remove("hidden");
                switchNotesTab("tab-document");
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (err) {
            hideLoading();
            alert(`Network Error: ${err.message}`);
        }
    });

    function switchNotesTab(tabId) {
        tabBtns.forEach(btn => {
            if (btn.getAttribute("data-tab") === tabId) {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });

        tabContents.forEach(content => {
            if (content.id === tabId) {
                content.classList.add("active");
            } else {
                content.classList.remove("active");
            }
        });
    }

    // Render Mermaid Code
    async function renderMermaidMindmap() {
        const canvas = document.getElementById("mermaidCanvas");
        canvas.innerHTML = "<p>Loading mindmap...</p>";

        // Extract mermaid code block from state.generatedNotes
        const pattern = /```mermaid\s*\n([\s\S]*?)\n```/i;
        const match = state.generatedNotes.match(pattern);
        
        if (match && match[1]) {
            const rawMermaid = match[1].trim();
            canvas.innerHTML = `<div class="mermaid">${rawMermaid}</div>`;
            try {
                if (typeof mermaid !== "undefined") {
                    await mermaid.run({
                        nodes: [canvas.querySelector(".mermaid")]
                    });
                }
            } catch (err) {
                canvas.innerHTML = `<p class="wrong-box">⚠️ Mindmap visualizer failed to compile syntax. Valid Mermaid output was:<br><pre style="text-align:left; padding:10px;">${rawMermaid}</pre></p>`;
            }
        } else {
            canvas.innerHTML = `<p class="wrong-box">⚠️ No valid Mermaid.js block was found in the generated notes.</p>`;
        }
    }

    // Download Notes Markdown
    downloadNotesBtn.addEventListener("click", () => {
        if (!state.generatedNotes) return;
        const topicName = notesTopicInput.value.trim().replace(/\s+/g, "_");
        const blob = new Blob([state.generatedNotes], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Study_Notes_${topicName}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });


    // ----------------- VIEW 3: MCQ QUIZ CREATOR -----------------
    const generateQuizBtn = document.getElementById("generateQuizBtn");
    const quizTopicInput = document.getElementById("quizTopic");
    const quizCountInput = document.getElementById("quizCount");
    const quizDifficultySelect = document.getElementById("quizDifficulty");
    const quizDisplayContainer = document.getElementById("quizDisplayContainer");
    const quizTitle = document.getElementById("quizTitle");
    const quizQuestionsList = document.getElementById("quizQuestionsList");
    const submitQuizBtn = document.getElementById("submitQuizBtn");
    const resetQuizBtn = document.getElementById("resetQuizBtn");
    const quizScoreCard = document.getElementById("quizScoreCard");

    generateQuizBtn.addEventListener("click", async () => {
        const topic = quizTopicInput.value.trim();
        if (!topic) {
            alert("Please specify a quiz topic.");
            return;
        }

        const count = parseInt(quizCountInput.value) || 5;
        showLoading(`Formulating ${count} questions on '${topic}'...`);

        try {
            const payload = {
                topic: topic,
                count: count,
                difficulty: quizDifficultySelect.value,
                api_key: getApiKey(),
                model: modelSelect.value
            };

            const res = await fetch("/api/quiz", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            hideLoading();

            if (res.ok) {
                state.quizData = data.quiz;
                state.quizAnswers = {};
                state.quizSubmitted = false;
                
                // Reset buttons and scorecard visibility
                submitQuizBtn.classList.remove("hidden");
                resetQuizBtn.classList.add("hidden");
                quizScoreCard.classList.add("hidden");
                
                renderQuizQuestions();
                quizDisplayContainer.classList.remove("hidden");
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (err) {
            hideLoading();
            alert(`Network Error: ${err.message}`);
        }
    });

    function renderQuizQuestions() {
        quizTitle.textContent = state.quizData.title || "Academic Evaluation Quiz";
        quizQuestionsList.innerHTML = "";

        state.quizData.questions.forEach((q, qIdx) => {
            const card = document.createElement("div");
            card.className = "quiz-card";
            card.id = `quiz-card-${qIdx}`;

            const qText = document.createElement("div");
            qText.className = "quiz-question-text";
            qText.innerHTML = `<strong>Question ${qIdx + 1}:</strong> ${q.question}`;
            card.appendChild(qText);

            const optionsDiv = document.createElement("div");
            optionsDiv.className = "quiz-options";

            q.options.forEach(option => {
                const optBtn = document.createElement("button");
                optBtn.className = "quiz-option-btn";
                optBtn.textContent = option;
                optBtn.addEventListener("click", () => selectOption(qIdx, option, optBtn));
                optionsDiv.appendChild(optBtn);
            });

            card.appendChild(optionsDiv);
            quizQuestionsList.appendChild(card);
        });
    }

    function selectOption(qIdx, option, buttonElement) {
        if (state.quizSubmitted) return;

        state.quizAnswers[qIdx] = option;

        // Toggle selected styling
        const cardOptions = document.querySelectorAll(`#quiz-card-${qIdx} .quiz-option-btn`);
        cardOptions.forEach(btn => btn.classList.remove("selected"));
        buttonElement.classList.add("selected");
    }

    submitQuizBtn.addEventListener("click", () => {
        const questionsCount = state.quizData.questions.length;
        const answersCount = Object.keys(state.quizAnswers).length;

        if (answersCount < questionsCount) {
            if (!confirm(`You have only answered ${answersCount} out of ${questionsCount} questions. Submit anyway?`)) {
                return;
            }
        }

        state.quizSubmitted = true;
        submitQuizBtn.classList.add("hidden");
        resetQuizBtn.classList.remove("hidden");

        // Grade the quiz
        let score = 0;
        state.quizData.questions.forEach((q, qIdx) => {
            const userAns = state.quizAnswers[qIdx];
            const correctAns = q.correct_answer;
            const card = document.getElementById(`quiz-card-${qIdx}`);
            
            // Disable option buttons
            const optionBtns = card.querySelectorAll(".quiz-option-btn");
            optionBtns.forEach(btn => btn.disabled = true);

            const resultBox = document.createElement("div");
            
            if (userAns === correctAns) {
                score++;
                resultBox.className = "correct-box";
                resultBox.innerHTML = `<strong>✅ Correct!</strong> Your choice: <i>${userAns}</i><br><br><strong>Explanation:</strong> ${q.explanation}`;
            } else {
                resultBox.className = "wrong-box";
                resultBox.innerHTML = `<strong>❌ Incorrect.</strong> Your choice: <i>${userAns || "No answer selected"}</i><br><strong>Correct Answer:</strong> <i>${correctAns}</i><br><br><strong>Explanation:</strong> ${q.explanation}`;
            }
            
            card.appendChild(resultBox);
        });

        // Show Score Card
        const pct = Math.round((score / questionsCount) * 100);
        document.getElementById("scoreTitle").textContent = `Your Final Score: ${score} / ${questionsCount} (${pct}%)`;
        
        const scoreMsg = document.getElementById("scoreMessage");
        if (pct === 100) {
            scoreMsg.innerHTML = "🏆 <strong>Perfect Score! Outstanding work!</strong>";
        } else if (pct >= 70) {
            scoreMsg.innerHTML = "🌟 <strong>Great job! You have a solid grasp of this topic.</strong>";
        } else {
            scoreMsg.innerHTML = "📖 <strong>Keep reviewing! Try asking Study Buddy for clarification on missed concepts.</strong>";
        }

        quizScoreCard.classList.remove("hidden");
        quizScoreCard.scrollIntoView({ behavior: "smooth" });
    });

    resetQuizBtn.addEventListener("click", () => {
        state.quizAnswers = {};
        state.quizSubmitted = false;
        
        submitQuizBtn.classList.remove("hidden");
        resetQuizBtn.classList.add("hidden");
        quizScoreCard.classList.add("hidden");

        // Re-render
        renderQuizQuestions();
    });
});
