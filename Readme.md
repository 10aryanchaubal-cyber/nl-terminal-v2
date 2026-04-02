# NL-Terminal v2.1
### An AI-Augmented Cross-Platform Command Line Interface

---

## 📌 Overview

**NL-Terminal** is an intelligent command-line interface that enhances traditional terminals by allowing users to interact using **natural language**, while still supporting **full raw command execution**.

Instead of replacing the system shell, NL-Terminal operates as a **user-space intelligent layer** on top of the native terminal, preserving correctness, safety, and compatibility while significantly improving usability and learning experience.

The system integrates **offline/local AI (Gemma 2B)**, rule-based command mapping, interactive program passthrough, and user-adaptive modes to create a practical, safe, and extensible terminal environment.

---

## 🎯 New in v2.1

### ✨ Enhanced Capabilities
- **Gemma 2B Powered**: Now running on Google's efficient Gemma 2B model for faster, smarter responses.
- **Drive Switching**: Seamlessly switch drives on Windows (e.g., `change drive to D`, `switch to C:`).
- **Persistent State**: Directory changes (`cd`, `go to...`) and environment variables now persist correctly across commands.

### 🔌 Dynamic Plugin System
- **Hot-Reloading**: Add or modify python plugins in the `plugins/` folder while the terminal is running. It detects and loads them instantly!
- **Zero Restart**: No need to restart the shell to test new features.

### 🛡️ Robust & Stable
- **Crash Protection**: Global error handlers catch crashes and log them without killing your session.
- **Graceful Failures**: Errors are explained in plain English by the AI.

---

## 🎯 Key Features

### ✅ Natural Language Command Execution
Speak to your terminal in plain English. The system maps your intent to the correct OS-specific command.
- **File Ops:** `create folder demo`, `delete file notes.txt`
- **Navigation:** `go to desktop`, `go back`, `change drive to D`
- **System:** `check ram`, `kill process chrome`, `what time is it`

### ✅ Safety Sandbox & Rollback 🛡️
- **Interactive Safety:** Dangerous commands (delete, kill) require explicit user confirmation.
- **Rollback / Undo:** Accidentally deleted a file? Just type `undo` or `rollback` to restore it immediately.
- **Protected Paths:** Sensitive system directories (like `C:\Windows`) are strictly protected.

### ✅ Full Raw Terminal Support
- Executes real shell commands directly (`dir`, `git status`, `npm start`).
- **Interactive Programs:** Full support for `python`, `vim`, `nano`, `htop`.

### ✅ AI-Powered Error Intelligence
When a command fails, the local AI analyzes the error output and:
- Explains what went wrong in simple terms.
- Suggests fixes or alternative commands.
- **Offline Capable:** Works entirely offline using Ollama.

### ✅ Adaptive Session Modes
- **Beginner:** Verbose explanations, previews, and guidance.
- **Expert:** Minimal prompts, faster execution.
- **Safe:** Maximum security checks for every action.
*Switch modes anytime:* `mode expert`, `mode beginner`.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.9+**
- **[Ollama](https://ollama.ai/)**
  - Required model: `ollama pull gemma:2b`

### ⚡ Quick Start (Windows)
We provide a one-click launcher for Windows users.
1. Download the project.
2. Double-click **`run_terminal.bat`**.
3. It will automatically install dependencies and launch the terminal.

### 🛠️ Manual Installation
If you prefer the command line or are on Linux/macOS:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the terminal
python main.py
```

---

## 🧩 Plugin Development
Want to add your own commands? It's easy!
1. Create a `my_plugin.py` in the `plugins/` folder.
2. Inherit from the `Plugin` class.
3. The terminal will load it **automatically**!

See `plugins/README.md` for examples.

---

## 🏗️ Technical Architecture

```mermaid
graph TD
    User[User Input] --> Router{Input Type?}
    Router -->|Raw Command| Shell[Native Shell]
    Router -->|Natural Language| Parser[Intent Parser]
    
    Parser --> Mapper[Command Mapper]
    Mapper --> Safety[Safety Sandbox]
    
    Safety -->|Approved| Executor[Executor]
    Safety -->|Blocked| UI[User Interface]
    
    Executor --> Output[Output Formatter]
    Shell --> Output
    
    subgraph "AI Layer"
        Error[Error Intelligence]
        Learn[Tutor Mode]
        LocalLLM[Ollama (Gemma 2B)]
    end
    
    Output -->|On Error| Error
    Error --> LocalLLM
```

- **Core:** `main.py`, `executor.py`
- **Intelligence:** `local_ai.py`, `intent_parser.py`
- **Safety:** `safety.py`, `backup_manager.py`
- **Config:** `config.py`
- **Plugins:** `plugins/`, `plugin_loader.py`

---

## 👤 Author
**Aryan Chaubal**  
Department of Information Technology  
Prof Ram Meghe Institute of Technology & Research, Badnera, Amravati  

---

<p align="center">
  <i>This project is designed for academic evaluation and real-world utility.</i>
</p>
