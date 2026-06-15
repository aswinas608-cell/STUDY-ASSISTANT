import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Define structure using Pydantic for robust parsing
class QuizQuestion(BaseModel):
    question: str = Field(description="The question text.")
    options: List[str] = Field(description="List of exactly 4 options, including the correct one.")
    correct_answer: str = Field(description="The exact text of the correct option from the options list.")
    explanation: str = Field(description="A clear explanation of why this answer is correct and why the others are wrong.")

class Quiz(BaseModel):
    title: str = Field(description="Title of the quiz.")
    questions: List[QuizQuestion] = Field(description="List of quiz questions.")

def generate_quiz(api_key: str, topic: str, num_questions: int, difficulty: str, model_name: str = "llama-3.3-70b-versatile") -> Dict[str, Any]:
    """
    Generates a quiz using Groq and LangChain's structured output.
    Returns a dictionary matching the Quiz schema.
    """
    try:
        llm = ChatGroq(
            temperature=0.3,
            groq_api_key=api_key,
            model_name=model_name
        )
        
        # Try structured output using tools calling
        structured_llm = llm.with_structured_output(Quiz)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert educator. Design a multiple-choice quiz based on the user topic. "
                       "Ensure questions test deep understanding, have exactly 4 clear options, and match the difficulty level. "
                       "Provide detailed explanations for the correct answer."),
            ("user", "Generate a quiz with {num_questions} questions on the topic '{topic}' with a difficulty level of '{difficulty}'.")
        ])
        
        chain = prompt | structured_llm
        result = chain.invoke({"topic": topic, "num_questions": num_questions, "difficulty": difficulty})
        
        # Convert Pydantic object to dict
        if isinstance(result, Quiz):
            return result.model_dump()
        elif isinstance(result, dict):
            return result
        else:
            raise ValueError("Unexpected output format from structured LLM")
            
    except Exception as e:
        logging.warning(f"Structured output failed. Attempting JSON parsing fallback. Error: {e}")
        return generate_quiz_fallback(api_key, topic, num_questions, difficulty, model_name)

def generate_quiz_fallback(api_key: str, topic: str, num_questions: int, difficulty: str, model_name: str) -> Dict[str, Any]:
    """
    Fallback method using JsonOutputParser if structured output tool calls fail.
    """
    llm = ChatGroq(
        temperature=0.3,
        groq_api_key=api_key,
        model_name=model_name
    )
    
    parser = JsonOutputParser(pydantic_object=Quiz)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert educator. Design a multiple-choice quiz based on the user topic. "
                   "Ensure questions test deep understanding, have exactly 4 clear options, and match the difficulty level. "
                   "Provide detailed explanations for the correct answer.\n{format_instructions}"),
        ("user", "Generate a quiz with {num_questions} questions on the topic '{topic}' with a difficulty level of '{difficulty}'.")
    ])
    
    prompt_with_instructions = prompt.partial(format_instructions=parser.get_format_instructions())
    
    chain = prompt_with_instructions | llm | parser
    try:
        return chain.invoke({"topic": topic, "num_questions": num_questions, "difficulty": difficulty})
    except Exception as final_err:
        # Hard fallback dictionary if both methods fail
        return {
            "title": f"Quiz: {topic}",
            "questions": [
                {
                    "question": f"Could not generate quiz automatically. (Error: {str(final_err)})",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_answer": "Option A",
                    "explanation": "Please check your network connection, API key, and try again."
                }
            ]
        }
