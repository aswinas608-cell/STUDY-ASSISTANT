import os
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import LLMMathChain
from langchain_core.tools import Tool

def get_study_agent(api_key: str, model_name: str = "llama-3.3-70b-versatile"):
    """
    Initializes and returns a LangChain ReAct agent executor configured with Groq.
    All tools are fully wrapped with try-except safety blocks to prevent runtime crashes.
    """
    llm = ChatGroq(
        temperature=0.1,  # Lower temperature for better format compliance
        groq_api_key=api_key,
        model_name=model_name
    )
    
    # 1. Resilient DuckDuckGo Search Tool
    try:
        ddg_run = DuckDuckGoSearchRun()
        def safe_search_run(query: str) -> str:
            try:
                return ddg_run.run(query)
            except Exception as search_err:
                return f"Web search failed: {str(search_err)}. Please try lookup using Wikipedia instead."
        
        search_tool = Tool(
            name="web_search",
            func=safe_search_run,
            description="Search the web for real-time information, current events, and advanced explanations."
        )
    except Exception as e:
        search_tool = Tool(
            name="web_search",
            func=lambda x, err=str(e): f"Web search is currently offline. (Reason: {err})",
            description="Search the web for real-time information."
        )
    
    # 2. Resilient Wikipedia Tool (Wraps JSONDecodeError and network faults)
    try:
        wiki_wrapper = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=1500)
        wiki_run = WikipediaQueryRun(api_wrapper=wiki_wrapper)
        
        def safe_wiki_run(query: str) -> str:
            try:
                return wiki_run.run(query)
            except Exception as wiki_err:
                return f"Wikipedia lookup failed: {str(wiki_err)}. Please try using web_search instead."
                
        wiki_tool = Tool(
            name="wikipedia",
            func=safe_wiki_run,
            description="Search Wikipedia for structured academic concepts, historical facts, and encyclopedia articles."
        )
    except Exception as e:
        wiki_tool = Tool(
            name="wikipedia",
            func=lambda x, err=str(e): f"Wikipedia lookup is currently offline. (Reason: {err})",
            description="Search Wikipedia for structured academic concepts."
        )
        
    # 3. Resilient Math Tool
    try:
        math_chain = LLMMathChain.from_llm(llm=llm)
        def safe_math_run(query: str) -> str:
            try:
                return math_chain.run(query)
            except Exception as math_err:
                return f"Math computation failed: {str(math_err)}. Provide the mathematical answer using your own knowledge if possible."
                
        math_tool = Tool(
            name="calculator",
            func=safe_math_run,
            description="Solve math equations and complex numeric computations. Input should be a clear mathematical expression, e.g. '2 + 2' or 'sqrt(16) * 5'."
        )
    except Exception as e:
        math_tool = Tool(
            name="calculator",
            func=lambda x, err=str(e): f"Calculator is currently offline. (Reason: {err})",
            description="Solve math equations."
        )

    tools = [search_tool, wiki_tool, math_tool]
    
    # Standard ReAct prompt layout with strict formatting instructions
    template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

CRITICAL FORMATTING RULES:
1. You MUST use the exact prefix "Final Answer:" when giving your final response. Do not use phrases like "The final answer is:" or "Response:".
2. Explain concepts step-by-step to help the student understand. Use clean markdown formatting (bold text, lists, bullet points).
3. Do not include any "Action:" or "Action Input:" blocks in your Final Answer.

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

    prompt = PromptTemplate(
        template=template,
        input_variables=["input", "tools", "tool_names", "agent_scratchpad"]
    )
    
    # Construct the ReAct agent
    agent = create_react_agent(llm, tools, prompt)
    
    # Custom error handler to nudge the agent when it outputs incorrect format
    def handle_parsing_error(error) -> str:
        return (
            "Invalid format. You forgot to output 'Final Answer:' or outputted a thought block without a tool action. "
            "If you know the final answer, output:\n"
            "Thought: I now know the final answer\n"
            "Final Answer: [your response to the student]"
        )
    
    # Create the executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=handle_parsing_error,
        max_iterations=6
    )
    
    return agent_executor
