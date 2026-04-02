from local_ai import run_llm

# Pattern-based quick fixes.
# These catch common errors without calling AI first.
# AI can then add deeper context.
QUICK_FIXES = [
    {
        "patterns": [
            "is not recognized", "not recognized as", "command not found",
            "not found", "not operable", "unknown command"
        ],
        "fix": (
            "Tip: command was not found. Possible fixes:\n"
            "  1. Check if the tool is installed (e.g., `gcc`, `node`, `python`)\n"
            "  2. Check your system PATH; the tool folder may be missing\n"
            "  3. On Windows, restart terminal after install\n"
            "  4. Use full path to executable"
        ),
    },
    {
        "patterns": [
            "permission denied", "access denied", "access is denied",
            "requires elevation", "not permitted", "run as administrator"
        ],
        "fix": (
            "Permission denied. Try:\n"
            "  1. Run terminal as Administrator (Windows) or use `sudo` (Linux)\n"
            "  2. Check permissions with `icacls <file>` (Windows) or `ls -la` (Linux)\n"
            "  3. Take ownership: `takeown /f <file>` (Windows) or `chmod +x <file>` (Linux)"
        ),
    },
    {
        "patterns": [
            "no such file", "cannot find the file", "cannot find the path",
            "system cannot find", "does not exist", "not exist"
        ],
        "fix": (
            "File or directory not found. Check:\n"
            "  1. Spelling of file/folder name\n"
            "  2. Use `dir` (Windows) or `ls` (Linux) to inspect current directory\n"
            "  3. Use full path if file is elsewhere\n"
            "  4. Check whether file was moved or deleted"
        ),
    },
    {
        "patterns": ["syntax error", "unexpected token", "parsing error"],
        "fix": (
            "Syntax error in command. Check:\n"
            "  1. Missing or extra quotes/parentheses\n"
            "  2. Incorrect flags (try `<command> --help`)\n"
            "  3. Special characters that need escaping"
        ),
    },
    {
        "patterns": [
            "connection refused", "connection timed out", "network unreachable",
            "could not resolve", "name resolution"
        ],
        "fix": (
            "Network error. Try:\n"
            "  1. Check internet connection\n"
            "  2. Run `ping 8.8.8.8` to verify basic connectivity\n"
            "  3. Check firewall/proxy rules\n"
            "  4. Verify URL/hostname"
        ),
    },
    {
        "patterns": ["disk full", "no space left", "insufficient disk space", "not enough space"],
        "fix": (
            "Disk is full. Try:\n"
            "  1. Delete unnecessary files\n"
            "  2. Empty recycle bin/trash\n"
            "  3. Check disk usage with `wmic logicaldisk get size,freespace,caption` (Windows)"
        ),
    },
]


def get_quick_fix(error_output: str) -> str:
    """Return a quick-fix tip if the error matches a known pattern."""
    lower = (error_output or "").lower()
    for entry in QUICK_FIXES:
        for pattern in entry["patterns"]:
            if pattern in lower:
                return entry["fix"]
    return ""


def explain_error(command, error_output):
    """
    Provide error explanation: quick pattern-based fix + AI deep analysis.
    """
    quick = get_quick_fix(error_output)

    prompt = f"""You are a terminal expert assistant.

A command was executed and failed.

Command:
{command}

Error output:
{error_output}

Explain:
- What the error means
- Why it happened
- One or two suggestions to fix it

Do NOT suggest dangerous commands.
Do NOT execute anything.
Keep it concise and helpful.
"""

    try:
        ai_response = run_llm(prompt)
    except Exception:
        ai_response = ""

    parts = []
    if quick:
        parts.append(quick)
    if ai_response:
        parts.append(ai_response)

    return "\n\n".join(parts) if parts else "AI could not analyze the error."
