from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import os
import requests
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import re


KNOWLEDGE_FILE = os.path.join(os.path.dirname(__file__), "knowledge_base.md")

_model = None
_chunks = []
_embeddings = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def _load_knowledge():
    global _chunks, _embeddings

    if _embeddings is not None:
        return 

    if not os.path.exists(KNOWLEDGE_FILE):
        _chunks = []
        _embeddings = np.array([])
        return

    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = []
    for block in content.split("---"):
        block = block.strip()
        if block:
            chunks.append(block)

    _chunks = chunks
    if chunks:
        model = _get_model()
        _embeddings = model.encode(chunks, convert_to_numpy=True)
    else:
        _embeddings = np.array([])

def _vector_search(query: str, top_k: int = 3) -> str:
    _load_knowledge()

    if not _chunks or _embeddings is None or len(_embeddings) == 0:
        return ""

    model = _get_model()
    query_vec = model.encode([query], convert_to_numpy=True)

    norms = np.linalg.norm(_embeddings, axis=1, keepdims=True)
    normed = _embeddings / np.clip(norms, 1e-10, None)
    query_norm = query_vec / np.clip(np.linalg.norm(query_vec), 1e-10, None)
    scores = normed @ query_norm.T 
    scores = scores.flatten()

    top_indices = np.argsort(scores)[::-1][:top_k]
    top_chunks = [_chunks[i] for i in top_indices if scores[i] > 0.2] 

    return "\n\n---\n\n".join(top_chunks) if top_chunks else ""

LLM_PROVIDER = "ollama"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

SYSTEM_PROMPT = """You are a helpful assistant for the University of Manitoba (UofM). 
Your role is to provide short, accurate, helpful, and friendly information about:
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


# ─── Actions ──────────────────────────────────────────────────────────────────

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
    
    def _call_ollama(self, user_question: str, info: str) -> str:
        try:
            context_block = f"\n\nRelevant information from knowledge base:\n{info}" if info else ""

            data = {
                "model": "llama2",
                "prompt": f"{SYSTEM_PROMPT}{context_block}\n\nUser: {user_question}\n\nAssistant:",
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

        info = _vector_search(user_message, top_k=3)

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