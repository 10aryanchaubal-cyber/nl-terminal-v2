import subprocess
import json
import re
from config import AI_MODEL, AI_TIMEOUT

from functools import lru_cache

# Cache the last 32 calls to avoid repetitive LLM hits for same inputs
@lru_cache(maxsize=32)
def run_llm(prompt):
    try:
        # Check if ollama is running first (simple ping check could be added in main, 
        # but here we just try-except properly)
        result = subprocess.run(
            ["ollama", "run", AI_MODEL],
            input=prompt,
            text=True,
            capture_output=True,
            encoding='utf-8',
            errors='ignore',
            timeout=AI_TIMEOUT
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""
    except Exception:
        return ""

def extract_json(text):
    """
    Robustly extract JSON object or array from LLM output using regex.
    """
    try:
        # Try to find a JSON object
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        
        # Try to find a JSON array
        match_arr = re.search(r'(\[.*\])', text, re.DOTALL)
        if match_arr:
            return json.loads(match_arr.group(1))
            
        return None
    except json.JSONDecodeError:
        return None

def ai_interpret(sentence):
    # Optimized prompt: shorter, clearer instructions, less tokens
    prompt = f"""
Act as a terminal assistant NLP engine.
Extract intent and entities from: "{sentence}"

Intents:
CREATE_FOLDER, DELETE_FOLDER, CREATE_FILE, DELETE_FILE,
RENAME_FILE, MOVE_FILE, COPY_FILE, LIST_FILES, CURRENT_DIR,
GO_TO, GO_BACK, GO_HOME, CAT_FILE, WHOAMI, SYSTEM_INFO,
CHANGE_DRIVE

Return JSON ONLY:
{{
  "intent": "INTENT_NAME",
  "entities": {{
    "name": "filename/foldername",
    "source": "src",
    "destination": "dest",
    "drive": "drive_letter"
  }},
  "confidence": 0.0-1.0
}}
"""
    response = run_llm(prompt)
    data = extract_json(response)
    
    if data:
        # Ensure entities is always a dict
        if "entities" in data and data["entities"] is None:
            data["entities"] = {}
        return data
        
    return {"intent": "UNKNOWN", "entities": {}, "confidence": 0.0}

def ai_suggest_options(sentence):
    prompt = f"""
User input: "{sentence}"
Suggest 3 terminal actions.
Return JSON Array ONLY:
[
  {{
    "intent": "INTENT",
    "entities": {{ "name": "", "source": "", "destination": "", "drive": "" }},
    "description": "Short description"
  }}
]
"""
    response = run_llm(prompt)
    data = extract_json(response)
    # Check if data is list, if not try to wrap? No, just return [] on failure
    return data if isinstance(data, list) else []

def ai_explain(topic):
    prompt = f"Explain terminal command '{topic}' in 1 short sentence."
    return run_llm(prompt)

def ai_teach(topic):
    prompt = f"Show how to use '{topic}' command with 2 concise examples."
    return run_llm(prompt)
