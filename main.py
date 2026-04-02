import os
import pathlib
import sys
import subprocess
import time
import logging

from os_detector import get_os
from intent_parser import detect_intent, extract_entities
from local_ai import (
    ai_interpret,
    ai_suggest_options,
    ai_explain,
    ai_teach,
)
from command_mapper import map_command
from command_detector import is_direct_command
from executor import execute, is_interactive
from pty_executor import run_interactive
from safety import is_safe, confirm_action
from logger import log_action
from error_intelligence import explain_error
from session import Session
from ui import TerminalUI
from backup_manager import BackupManager
from config import CONFIDENCE_THRESHOLD, LOW_CONFIDENCE_FLOOR, AI_MODEL
from output_formatter import (
    format_output,
    format_ai_insight,
    format_ai_explanation,
    format_ai_lesson,
)
from plugin_loader import PluginManager
import intent_parser  # Import module to update PLUGINS ref

# Setup logging
logging.basicConfig(
    filename="nl_terminal.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def get_default_start_directory() -> str:
    """
    Return the same default startup directory a regular terminal would use.
    """
    home = os.path.expanduser("~")
    return home if os.path.isdir(home) else os.getcwd()


def is_ollama_running():
    try:
        subprocess.run(
            ["ollama", "list"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False



NL_KEYWORDS = {
    "create", "delete", "remove", "make", "show", "list", "where",
    "go", "open", "explain", "teach", "how", "change", "switch",
    "set", "read", "check", "what", "install", "update", "upgrade",
    "find", "search", "rename", "move", "copy", "compress", "zip",
    "unzip", "download", "who", "display", "give", "tell", "run",
    "execute", "launch", "start", "stop", "kill", "terminate",
    "restart", "is", "are", "can", "help", "why", "when",
}


NL_STRUCTURE_WORDS = {
    "the", "a", "an", "my", "this", "that", "these", "those",
    "me", "i", "we", "our", "your", "please", "can", "could",
    "would", "should", "do", "does", "did", "is", "are", "was",
    "were", "am", "be", "been", "have", "has", "had",
    "for", "from", "into", "onto", "about", "with", "without",
    "all", "every", "some", "any", "much", "many",
}

# Question patterns
QUESTION_STARTERS = {
    "what", "where", "how", "why", "when", "who", "which",
    "is", "are", "can", "could", "would", "should", "do", "does",
}

# Special NL commands handled directly by the terminal
SPECIAL_NL_PREFIXES = (
    "explain", "teach me", "learn", "how to use", "how to",
)


def looks_like_nl(sentence: str) -> bool:
    """
    Smarter NL detection. Returns True only if input genuinely looks
    like a natural language sentence, not a shell command.
    """
    lower = sentence.lower().strip()
    words = lower.split()

    if not words:
        return False

    # Single word — not NL (could be a command like "dir", "ls", "cls")
    if len(words) == 1:
        return False

    # Special NL prefixes always treated as NL
    for prefix in SPECIAL_NL_PREFIXES:
        if lower.startswith(prefix):
            return True

    # Questions are NL
    if words[0] in QUESTION_STARTERS and len(words) >= 3:
        return True

    # If it ends with "?" it's a question
    if lower.endswith("?"):
        return True

    # Count NL signals
    nl_keyword_count = sum(1 for w in words if w in NL_KEYWORDS)
    nl_structure_count = sum(1 for w in words if w in NL_STRUCTURE_WORDS)

    # Strong NL: has structure words + keywords + enough words
    if nl_structure_count >= 1 and nl_keyword_count >= 1 and len(words) >= 3:
        return True

    # Multi-word with 2+ NL keywords and at least 3 words total
    if nl_keyword_count >= 2 and len(words) >= 3:
        return True

    # Two-word NL commands like "show files", "list processes", "check ram"
    if len(words) == 2 and words[0] in NL_KEYWORDS:
        # But make sure the second word isn't a flag
        if not words[1].startswith("-") and not words[1].startswith("/"):
            # And the combo isn't a real command (e.g., "set PATH" is a command)
            # We only trigger NL for combos where the first word is a pure NL verb
            pure_nl_verbs = {
                "show", "list", "check", "display", "give", "tell",
                "find", "search", "where", "who", "what", "explain",
                "teach", "learn", "help",
            }
            if words[0] in pure_nl_verbs:
                return True

    return False



def handle_cd(command: str, ui) -> bool:
    """
    Handle cd and drive switching within the current Python process.
    Returns True if the command was handled, False otherwise.
    """
    stripped = command.strip()
    lower = stripped.lower()
 

    if len(stripped) <= 3 and ":" in stripped and stripped[0].isalpha():
        drive = stripped[:2]  # "D:"
        try:
            os.chdir(drive + "\\")
            ui.print_success(f"Switched to drive {drive}")
            log_action(stripped, "CHANGE_DRIVE", stripped, "SUCCESS", f"Changed to {drive}")
            return True
        except Exception as e:
            ui.print_error(f"Cannot switch to {drive}: {e}")
            return True

    # CD command
    if lower == "cd" or lower.startswith("cd ") or lower.startswith("cd\t"):
        target = stripped[2:].strip().strip('"').strip("'")
        if not target:
            # Just "cd" — show current directory
            ui.stream_output(os.getcwd())
            return True

        # Handle "cd /d D:\folder" (Windows)
        if target.lower().startswith("/d "):
            target = target[3:].strip()

        # Expand environment variables and user home
        expanded = os.path.expandvars(target)
        expanded = os.path.expanduser(expanded)

        try:
            os.chdir(expanded)
            log_action(stripped, "GO_TO", stripped, "SUCCESS", f"Changed to {os.getcwd()}")
            return True
        except FileNotFoundError:
            ui.print_error(f"Directory not found: {target}")
            return True
        except PermissionError:
            ui.print_error(f"Permission denied: {target}")
            return True
        except Exception as e:
            ui.print_error(f"Cannot change directory: {e}")
            return True

    return False


# ─── How To Use / Help ───────────────────────────────────────────────────────

HELP_TEXT = """
[bold cyan]=== NL-Terminal v2.0 - Quick Guide ===[/bold cyan]

[bold green]Direct Commands[/bold green] - Type any shell command as you normally would:
   [dim]gcc --version - git status - pip list - dir - node -v[/dim]
   [dim]tasklist | findstr python - echo hello > test.txt[/dim]

[bold green]Natural Language[/bold green] - Speak naturally:
   [dim]"show me all files" - "create folder projects"[/dim]
   [dim]"check ram usage" - "what is my IP address"[/dim]
   [dim]"find text TODO in python files"[/dim]

[bold green]AI Features[/bold green]:
   [dim]explain <command>  - Get AI explanation of any command[/dim]
   [dim]teach me <topic>   - Learn terminal concepts[/dim]

[bold green]Modes[/bold green]: [dim]"switch to expert" - "set mode safe" - "mode beginner"[/dim]
[bold green]Rollback[/bold green]: [dim]"undo" - "rollback" - Restore deleted files[/dim]
[bold green]Exit[/bold green]: [dim]"exit" or "quit"[/dim]
"""


# ─── Main Loop ──────────────────────────────────────────────────────────────

def run_ui():
    # Start in the user's default shell directory, not the project folder.
    try:
        os.chdir(get_default_start_directory())
    except Exception:
        pass

    os_type = get_os()
    session = Session()
    ui = TerminalUI(session.mode, os_type)
    backup_manager = BackupManager()

    # Initialize Plugin Manager
    plugin_manager = PluginManager()
    intent_parser.set_plugin_manager(plugin_manager)

    ui.welcome_screen()

    if not is_ollama_running():
        ui.print_warning("Ollama is not running. AI features will fail.")
        ui.print_info("Please start Ollama in another terminal.")

    startup_prompt = True

    while True:
        try:
            # Check for plugin updates
            if plugin_manager.scan_and_load():
                pass

            user_input = ui.get_input(responsive_startup=startup_prompt).strip()

            if not user_input:
                continue

            startup_prompt = False

            # ── EXIT ──
            if user_input.lower() in ["exit", "quit"]:
                ui.print_info("Goodbye!")
                break

            lower = user_input.lower()

            # ── HELP ──
            if lower in ["help", "how to use", "howto", "?"]:
                ui.print_help()
                continue

            # ── MODE SWITCH ──
            if (
                lower.startswith("mode")
                or "change mode" in lower
                or ("switch" in lower and any(m in lower for m in ["beginner", "expert", "safe"]))
                or "set mode" in lower
            ):
                for m in ["beginner", "expert", "safe"]:
                    if m in lower:
                        session.set_mode(m)
                        ui.update_mode(session.mode)
                        ui.print_success(f"Switched to {session.mode} mode")
                        break
                else:
                    ui.print_warning("Specify mode: beginner | expert | safe")
                continue

            # ── EXPLAIN / TEACH ──
            if lower.startswith("explain"):
                ui.print_ai_thinking()
                topic = user_input[7:].strip()
                explanation = ai_explain(topic)
                ui.print_ai_response(format_ai_explanation(explanation))
                continue

            if lower.startswith(("teach me", "learn")):
                ui.print_ai_thinking()
                topic = lower.replace("teach me", "").replace("learn", "").strip()
                lesson = ai_teach(topic)
                ui.print_ai_response(format_ai_lesson(lesson))
                continue

            # ── INTERACTIVE ──
            if is_interactive(user_input):
                ui.print_info(f"Launching interactive session: {user_input}")
                run_interactive(user_input)
                continue

            # ── CD / DRIVE SWITCH (must happen before command detection) ──
            if handle_cd(user_input, ui):
                continue

            
            #

            # ── PRIORITY 1: Direct Shell Command ──
            if is_direct_command(user_input):
                ui.print_command_execution(user_input)
                out, err = execute(user_input)

                log_action(
                    user_input, "DIRECT_COMMAND", user_input,
                    "SUCCESS" if not err else "ERROR",
                    err[:100] if err else "OK",
                )

                if out:
                    ui.stream_output(out)
                if err:
                    ui.print_error(err)
                    ui.print_ai_response(
                        format_ai_insight(explain_error(user_input, err))
                    )
                continue

            # ── PRIORITY 2: Natural Language ──
            # Treat known intents as NL even if the heuristic is strict.
            intent = detect_intent(user_input)
            if intent != "UNKNOWN" or looks_like_nl(user_input):
                entities = extract_entities(user_input, intent=intent)

                if intent == "UNKNOWN":
                    ui.print_ai_thinking()
                    try:
                        ai_result = ai_interpret(user_input)
                    except Exception:
                        ui.stop_ai_thinking()
                        ui.print_warning("AI is unavailable. Try a direct command.")
                        continue
                    confidence = ai_result.get("confidence", 0.0)

                    if confidence < LOW_CONFIDENCE_FLOOR:
                        ui.stop_ai_thinking()
                        ui.print_warning(
                            f"Too ambiguous (Confidence: {confidence:.2f}). Please rephrase."
                        )
                        continue

                    if confidence < CONFIDENCE_THRESHOLD:
                        try:
                            options = ai_suggest_options(user_input)
                        except Exception:
                            options = []
                        ui.stop_ai_thinking()
                        if not options:
                            ui.print_warning(
                                "AI was unsure and could not suggest options."
                            )
                            continue

                        ui.print_info("Did you mean:")
                        for i, opt in enumerate(options, 1):
                            if isinstance(opt, dict):
                                desc = opt.get("description", "Unknown action")
                            else:
                                desc = str(opt)
                            ui.stream_output(
                                f"[bold cyan]{i})[/bold cyan] {desc}",
                                markup=True,
                            )

                        choice = ui.get_input()
                        if not choice.isdigit():
                            continue
                        idx = int(choice) - 1
                        if 0 <= idx < len(options):
                            selected = options[idx]
                            if isinstance(selected, dict):
                                intent = selected.get("intent", "UNKNOWN")
                                entities = selected.get("entities", {}) or {}
                            else:
                                ai_result = ai_interpret(user_input)
                                intent = ai_result.get("intent", "UNKNOWN")
                                entities = ai_result.get("entities", {}) or {}
                        else:
                            continue
                    else:
                        intent = ai_result.get("intent", "UNKNOWN")
                        entities = ai_result.get("entities", {}) or {}
                        ui.stop_ai_thinking()

                # Ensure entities is always a dict
                entities = entities or {}

               
                if intent == "SHOW_HISTORY":
                    log_path = os.path.join(
                        os.path.dirname(os.path.abspath(__file__)), "logs", "command_log.txt"
                    )
                    if os.path.exists(log_path):
                        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                            history = f.read().strip()
                        if history:
                            ui.stream_output(history)
                        else:
                            ui.print_info("No command history yet.")
                    else:
                        ui.print_info("No command history yet.")
                    continue

               
                if intent == "ROLLBACK":
                    msg = backup_manager.restore_last()
                    ui.print_success(msg)
                    log_action(user_input, intent, "ROLLBACK", "SUCCESS", msg)
                    continue

               
                if intent in ["DELETE_FILE", "DELETE_FOLDER", "KILL_PROCESS"]:
                    if not is_safe(entities.get("name")):
                        ui.print_error(
                            "Action blocked by safety rules (system path protection)."
                        )
                        log_action(
                            user_input, intent, "BLOCKED", "FAIL", "Safety block"
                        )
                        continue

                    action_desc = f"{intent} on {entities.get('name')}"
                    if not confirm_action(action_desc, session.mode):
                        ui.print_warning("Action aborted by user.")
                        log_action(
                            user_input, intent, "ABORTED", "CANCEL", "User denied"
                        )
                        continue

                   
                    if intent == "DELETE_FILE" and entities.get("name"):
                        if backup_manager.backup_file(entities.get("name")):
                            ui.print_success(f"Backup created for {entities.get('name')}")

                command = map_command(
                    intent, os_type, entities, plugins=plugin_manager.get_plugins()
                )
                if not command:
                    ui.print_error(f"Could not map command for intent: {intent}")
                    continue

                # Handle Plugin Internal Commands
                if command.startswith("INTERNAL:"):
                    response = command.split("INTERNAL:", 1)[1]
                    ui.print_success(response)
                    log_action(
                        user_input, intent, "PLUGIN_EXEC", "SUCCESS", response
                    )
                    continue

                # Handle cd commands generated by NL
                if handle_cd(command, ui):
                    log_action(user_input, intent, command, "SUCCESS", "Dir changed")
                    continue

                ui.print_command_execution(command)
                out, err = execute(command)

                status = "SUCCESS" if not err else "ERROR"
                log_action(
                    user_input, intent, command, status,
                    message=err[:100] if err else "OK",
                )

                if out:
                    formatted = format_output(intent, out, os_type)
                    if formatted:
                        ui.stream_output(formatted)
                    else:
                        ui.stream_output(out)

                if err:
                    ui.print_error(err)
                    ui.print_ai_response(
                        format_ai_insight(explain_error(command, err))
                    )
                continue

            # ── PRIORITY 3: Fallback — try executing, AI help on failure ──
            ui.print_command_execution(user_input)
            out, err = execute(user_input)

            log_action(
                user_input, "FALLBACK_EXEC", user_input,
                "SUCCESS" if not err else "ERROR",
                message=err[:100] if err else "OK",
            )

            if out:
                ui.stream_output(out)

            if err:
                ui.print_error(err)
                ui.print_ai_response(
                    format_ai_insight(explain_error(user_input, err))
                )

        except KeyboardInterrupt:
            ui.print_info("\nUser terminated session.")
            break
        except Exception as e:
            logging.error("Crash in main loop", exc_info=True)
            ui.print_error(f"An unexpected error occurred: {str(e)}")
            ui.print_info("The error has been logged. The terminal will not crash.")


def main():
    try:
        run_ui()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Critical Startup Error: {e}")
        logging.critical("Startup violation", exc_info=True)


if __name__ == "__main__":
    main()
