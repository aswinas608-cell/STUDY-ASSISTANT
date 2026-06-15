import re
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def generate_study_notes(api_key: str, topic: str, audience: str, depth: str, model_name: str = "llama-3.3-70b-versatile"):
    """
    Generates structured study notes on the given topic for the specified audience and depth.
    """
    llm = ChatGroq(
        temperature=0.3,
        groq_api_key=api_key,
        model_name=model_name
    )
    
    system_prompt = """You are an expert academic tutor and curriculum designer. 
Your goal is to create premium, comprehensive, and highly engaging study notes for a student.

Create study notes using the following exact structure:
1. # [Topic Title] - a beautiful title
2. ## Overview - a comprehensive introduction to the topic, explaining its significance
3. ## Key Concepts - dive deep into at least 3-4 subtopics. Use headers (###), bold text, bullet points, and code blocks (if relevant) to explain details. Include real-world analogies and clear examples.
4. ## Quick Reference Table - create a markdown table of key terms and their definitions.
5. ## Summary & Key Takeaways - bulleted key points that are essential for exams.
6. ## Visual Mindmap - Include a valid Mermaid.js mindmap diagram representing this topic. Use the `mindmap` syntax. Keep nodes simple and clean. Avoid special characters inside labels. Example:
```mermaid
mindmap
  root((Topic Title))
    Subtopic A
      Detail A1
      Detail A2
    Subtopic B
      Detail B1
```
Make sure the mindmap is enclosed in ```mermaid and ``` code blocks.

Ensure the tone is supportive, academic, and highly readable. Customize the language difficulty based on the target audience and depth requested."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Create study notes for the topic: '{topic}'\nTarget Audience/Grade: {audience}\nLevel of Detail: {depth}")
    ])
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"topic": topic, "audience": audience, "depth": depth})

def extract_mermaid_code(markdown_content: str) -> str:
    """
    Extracts the first mermaid code block found in the markdown content.
    Returns the raw mermaid code or an empty string.
    """
    # Regex to find ```mermaid ... ```
    pattern = r"```mermaid\s*\n(.*?)\n```"
    match = re.search(pattern, markdown_content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""
