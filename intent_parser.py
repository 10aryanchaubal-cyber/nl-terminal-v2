import json
import re
import os
from plugin_loader import load_plugins

_INTENTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intents.json")
with open(_INTENTS_PATH, encoding="utf-8") as f:
    BASE_INTENTS = json.load(f)


# Global reference to be updated by main.py
PLUGIN_MANAGER = None

def set_plugin_manager(pm):
    global PLUGIN_MANAGER
    PLUGIN_MANAGER = pm

def detect_intent(sentence):
    sentence = sentence.lower()

    # Base intents
    for intent, phrases in BASE_INTENTS.items():
        for phrase in phrases:
            if phrase in sentence:
                return intent

    # Plugin intents
    if PLUGIN_MANAGER:
        plugins = PLUGIN_MANAGER.get_plugins()
        # TODO: Implement proper phrase registration for Plugin objects
        pass

    return "UNKNOWN"

def extract_entities(sentence, intent=None):
    """
    Extract entities from natural language input.
    If intent is provided, use intent-specific extraction first.
    """
    original = sentence.strip()
    sentence = original.lower()
    entities = {"name": None, "source": None, "destination": None, "drive": None}

    # 0. Drive switching
    drive_match = re.search(r"\b([a-z])\s*(?:drive|:)|to\s+([a-z])\b", sentence)
    if drive_match:
        drive_letter = drive_match.group(1) or drive_match.group(2)
        if drive_letter:
            entities["drive"] = drive_letter.upper()

    # Preserve quoted value if present
    quoted = re.search(r'["\'](.*?)["\']', original)
    quoted_value = quoted.group(1).strip() if quoted else None

    # 1. Source -> destination style intents
    move_match = re.search(r"(?:move|copy|rename)\s+(.*?)\s+to\s+(.*)", original, re.I)
    if move_match:
        entities["source"] = move_match.group(1).strip()
        entities["destination"] = move_match.group(2).strip()
        return entities

    # 2. Intent-specific extraction
    if intent in {"INSTALL_PACKAGE", "UPGRADE_PACKAGE", "CHECK_VERSION"}:
        if quoted_value:
            entities["name"] = quoted_value
            return entities
        pkg_match = re.search(
            r"(?:install package|install library|install module|add package|upgrade package|update package|version of|check version|what version)\s+([^\s]+)",
            sentence,
        )
        if pkg_match:
            entities["name"] = pkg_match.group(1).strip(" ,.")
            return entities

    if intent in {"GO_TO", "OPEN_EDITOR", "CAT_FILE", "RUN_SCRIPT"}:
        if quoted_value:
            entities["name"] = quoted_value
            return entities
        path_match = re.search(
            r"(?:go to|navigate to|enter folder|enter directory|change to|go into|open folder|open directory|switch to folder|edit file|open in editor|open editor|read file|show file content|display file|view file|show file|run script|execute script|run program|execute program)\s+(.+)",
            original,
            re.I,
        )
        if path_match:
            entities["name"] = path_match.group(1).strip().strip(" ,.")
            return entities

    if intent == "FIND_TEXT":
        if quoted_value:
            entities["name"] = quoted_value
            return entities
        text_match = re.search(r"(?:find text|search for text|grep for|find string|search string)\s+(.+)", original, re.I)
        if text_match:
            entities["name"] = text_match.group(1).strip().strip(" ,.")
            return entities

    if intent == "SEARCH_FILES":
        if quoted_value:
            entities["name"] = quoted_value
            return entities
        file_match = re.search(r"(?:search for file|find file|find files|search files|look for file|locate file|where is file)\s+(.+)", original, re.I)
        if file_match:
            entities["name"] = file_match.group(1).strip().strip(" ,.")
            return entities

    if intent in {"CREATE_FOLDER", "DELETE_FOLDER", "CREATE_FILE", "DELETE_FILE", "SEARCH_FILES", "FIND_TEXT", "SHOW_SIZE", "DOWNLOAD_FILE", "KILL_PROCESS"}:
        if quoted_value:
            entities["name"] = quoted_value
            return entities

    # 3. Generic extraction
    match = re.search(r"(?:file|folder|dir|directory|package|module|library|script|process)\s+([a-zA-Z0-9_\-\.]+(?:\.[a-z0-9]+)?)", sentence)
    if match:
        entities["name"] = match.group(1)

    kill_match = re.search(r"(?:kill process|stop program|end task|terminate|kill|stop)\s+(.*)", sentence)
    if kill_match:
        entities["name"] = kill_match.group(1).strip()
        return entities

    # Last-resort pattern for common "verb target" phrases.
    fallback_name = re.search(
        r"(?:install|upgrade|update|open|edit|read|run|find|search|download|size of)\s+([^\s]+)",
        sentence,
    )
    if fallback_name and not entities["name"]:
        entities["name"] = fallback_name.group(1).strip(" ,.")

    return entities
