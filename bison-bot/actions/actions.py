from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import os
import requests
import json
import re
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

LLM_PROVIDER = "ollama"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
KNOWLEDGE_BASE_PATH = "knowledge_base.md"

SYSTEM_PROMPT = """You are a helpful assistant for the University of Manitoba (UofM). 
Your role is to provide accurate, helpful, and friendly information about:
- Academic programs and faculties
- Admissions requirements and processes
- Campus facilities and services
- Student life and activities
- Tuition and financial aid
- Research opportunities
- Location and transportation
- Housing and residences
- International student support
- Indigenous student support
- Any other topics related to the University of Manitoba

Guidelines:
1. Be friendly, professional, and concise
2. If you don't have specific information, acknowledge it and suggest where to find it (e.g., official website, admissions office)
3. For very specific questions (like exact dates or fees), recommend contacting the relevant department directly
4. Always maintain a helpful and encouraging tone

Important: You must ONLY answer questions related to the University of Manitoba. 
If a question is not related to the university, politely decline and remind the user of your purpose."""


# Vector search setup 

embedder = SentenceTransformer("all-MiniLM-L6-v2")
kb_questions = []
kb_answers = []
faiss_index = None

def parse_markdown_kb(filepath: str) -> list:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    qa_pairs = []
    pattern = r"\*\*Q:\s*(.*?)\*\*\s*\nA:\s*(.*?)(?=\n\n|\n\*\*Q:|\Z)"
    matches = re.findall(pattern, content, re.DOTALL)
    for question, answer in matches:
        qa_pairs.append({"question": question.strip(), "answer": answer.strip()})
    return qa_pairs

def load_knowledge_base():
    global kb_questions, kb_answers, faiss_index
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        print(f"WARNING: knowledge_base.md not found at '{KNOWLEDGE_BASE_PATH}'")
        return
    data = parse_markdown_kb(KNOWLEDGE_BASE_PATH)
    if not data:
        print("WARNING: No Q&A pairs found. Check your markdown format.")
        return
    kb_questions = [item["question"] for item in data]
    kb_answers = [item["answer"] for item in data]
    embeddings = embedder.encode(kb_questions).astype("float32")
    faiss_index = faiss.IndexFlatL2(embeddings.shape[1])
    faiss_index.add(embeddings)
    print(f"Loaded {len(data)} Q&A pairs into fiass index.")

def search_knowledge_base(query: str, top_k: int = 3) -> str:
    if faiss_index is None or len(kb_questions) == 0:
        return ""
    query_embedding = embedder.encode([query]).astype("float32")
    distances, indices = faiss_index.search(query_embedding, top_k)
    context_parts = []
    for idx in indices[0]:
        if idx < len(kb_questions):
            context_parts.append(f"Q: {kb_questions[idx]}\nA: {kb_answers[idx]}")
    return "\n\n".join(context_parts)

load_knowledge_base()


class ActionCheckUniversityRelevance(Action):
    
    def name(self) -> Text:
        return "action_check_university_relevance"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '').lower()
        
        university_keywords = [
            'university of manitoba', 'uofm', 'u of m', 'manitoba',
            'admission', 'program', 'course', 'faculty', 'campus',
            'tuition', 'fee', 'scholarship', 'residence', 'student',
            'enroll', 'apply', 'application', 'degree', 'major',
            'winnipeg', 'fort garry', 'bannatyne', 'engineering',
            'science', 'arts', 'business', 'medicine', 'research'
        ]
        
        is_relevant = any(keyword in user_message for keyword in university_keywords)
        
        return []


class ActionAnswerUniversityQuestion(Action):
    
    def name(self) -> Text:
        return "action_answer_university_question"
    
    def _call_ollama(self, user_question: str, info) -> str:
        try:
            data = {
                "model": "llama2",
                "prompt": f"{SYSTEM_PROMPT}\n\nUser: {user_question}\n\nRelevant information:{info}\n\nAssistant:",
                "stream": False
            }
            
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json=data,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("response", "I apologize, but I couldn't generate a response.")
                
        except requests.exceptions.RequestException as e:
            return f"I'm having trouble connecting to the local LLM. Please ensure Ollama is running. Error: {str(e)}"
        except Exception as e:
            return f"An error occurred while processing your question. Error: {str(e)}"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text', '')
        
        # ── Only change: info is now filled by ChromaDB search ──
        info = search_knowledge_base(user_message)
        
        if LLM_PROVIDER == "ollama":
            response = self._call_ollama(user_message, info)
        else:
            response = "Error: Invalid LLM provider configured."
        
        out_of_scope_indicators = [
            "not related to the university of manitoba",
            "can only answer questions about",
            "outside my scope",
            "only answer questions related to"
        ]
        
        if any(indicator in response.lower() for indicator in out_of_scope_indicators):
            dispatcher.utter_message(text="I'm sorry, but I can only answer questions related to the University of Manitoba. Please ask me something about the university, such as admissions, programs, campus life, or facilities.")
        else:
            dispatcher.utter_message(text=response)
        
        return []