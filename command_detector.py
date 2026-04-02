"""
Smart Command Detector for NL-Terminal.
Determines whether user input is a direct shell command or natural language.
Uses PATH lookup, known-command databases, and pattern analysis.
"""
import shutil
import re
import os

# ─── Known CLI commands that shutil.which() might miss ───────────────────────
# These are common commands users expect to "just work" in a terminal.
# We check shutil.which() FIRST, but fall back to this list for builtins
# and commands that may not be on PATH but are still valid shell commands.

WINDOWS_BUILTINS = {
    # CMD built-ins (no .exe on disk — shutil.which won't find them)
    "dir", "type", "copy", "move", "del", "ren", "rename", "mkdir", "md",
    "rmdir", "rd", "cd", "chdir", "cls", "echo", "set", "path", "title",
    "color", "date", "time", "ver", "vol", "pause", "rem", "call",
    "if", "for", "goto", "shift", "start", "exit", "pushd", "popd",
    "assoc", "ftype", "mklink", "where", "more", "sort", "find",
    "findstr", "tree", "xcopy", "robocopy", "attrib", "icacls",
    "takeown", "cipher", "compact", "expand",
}

LINUX_BUILTINS = {
    "cd", "echo", "export", "alias", "unalias", "source", "type",
    "set", "unset", "read", "eval", "exec", "exit", "history",
    "jobs", "fg", "bg", "wait", "kill", "test", "true", "false",
    "pwd", "pushd", "popd", "dirs", "let", "declare", "local",
    "readonly", "shift", "trap", "ulimit", "umask",
}

# Common CLI tools people expect to work — helps when PATH is weird
KNOWN_EXECUTABLES = {
    # Compilers & Build
    "gcc", "g++", "clang", "clang++", "cl", "make", "cmake", "nmake",
    "msbuild", "ninja", "rustc", "cargo", "go", "javac", "java",
    "dotnet", "mcs", "csc",

    # Interpreters & Runtimes
    "python", "python3", "py", "pip", "pip3", "pipenv", "poetry",
    "conda", "node", "npm", "npx", "yarn", "pnpm", "bun", "deno",
    "ruby", "gem", "perl", "php", "composer", "lua", "r", "rscript",
    "julia", "swift", "kotlin", "kotlinc", "scala", "groovy",

    # Version Control
    "git", "svn", "hg", "gh",

    # Package Managers
    "apt", "apt-get", "yum", "dnf", "pacman", "brew", "choco",
    "scoop", "winget", "snap", "flatpak", "zypper", "emerge",

    # Networking
    "ping", "curl", "wget", "ssh", "scp", "sftp", "ftp",
    "netstat", "nslookup", "dig", "tracert", "traceroute",
    "ipconfig", "ifconfig", "ip", "arp", "route", "nmap",
    "telnet", "nc", "netcat",

    # Containers & Cloud
    "docker", "docker-compose", "podman", "kubectl", "minikube",
    "terraform", "ansible", "vagrant", "helm", "aws", "az", "gcloud",

    # Editors & Tools
    "vim", "nvim", "nano", "code", "notepad", "notepad++",
    "cat", "less", "more", "head", "tail", "grep", "awk", "sed",
    "cut", "sort", "uniq", "wc", "tr", "xargs", "tee",

    # File & Disk
    "ls", "ll", "dir", "cp", "mv", "rm", "touch", "mkdir",
    "rmdir", "ln", "chmod", "chown", "chgrp", "df", "du",
    "tar", "zip", "unzip", "gzip", "gunzip", "bzip2", "7z",
    "rar", "xz",

    # System
    "ps", "top", "htop", "kill", "killall", "pkill", "whoami",
    "hostname", "uname", "uptime", "free", "lsof", "strace",
    "ltrace", "dmesg", "journalctl", "systemctl", "service",
    "tasklist", "taskkill", "systeminfo", "wmic", "powershell",
    "pwsh", "cmd", "reg", "sc", "sfc", "dism", "chkdsk",
    "diskpart", "format",

    # Databases
    "mysql", "psql", "sqlite3", "mongo", "mongosh", "redis-cli",

    # Misc Dev Tools
    "valgrind", "gdb", "lldb", "strace", "ldd", "nm", "objdump",
    "readelf", "strings", "file", "xxd", "hexdump",
    "jest", "pytest", "mocha", "gradle", "mvn", "ant",
    "tsc", "eslint", "prettier", "black", "flake8", "mypy",
    "ffmpeg", "convert", "magick", "pandoc", "latex", "pdflatex",
}

# Flags that strongly indicate shell command usage
COMMAND_FLAGS_PATTERN = re.compile(
    r'(?:^|\s)(?:--?\w[\w-]*)'   # -flag or --flag
)

# Patterns that indicate shell operators (pipe, redirect, chain)
SHELL_OPERATOR_PATTERN = re.compile(
    r'\|{1,2}|>{1,2}|<|&&|;'
)

# Drive switch pattern (Windows): just a letter followed by colon
DRIVE_PATTERN = re.compile(r'^[a-zA-Z]:[\\/]?$')

# ─── NL Phrase Patterns ──────────────────────────────────────────────────────
# Multi-word inputs that START with a command name but are clearly NL.
# These override the builtin/executable detection.
# Format: frozenset of (first_word, second_word) tuples or first_word with
# known NL follow-ups.

# Commands that are ALSO common English words — these need extra checks
# to tell apart shell use from NL use.
AMBIGUOUS_COMMANDS = {
    "where", "find", "sort", "more", "time", "date", "tree",
    "start", "set", "type", "move", "copy", "del", "kill",
    "show", "display",
}

# Words that definitively mark a sentence as NL when they follow
# an ambiguous command as the second word
NL_FOLLOW_WORDS = {
    "am", "is", "are", "was", "were", "do", "does", "did",
    "me", "my", "i", "we", "you", "the", "a", "an", "this",
    "that", "all", "every", "some", "much", "many",
}

def _looks_like_nl_phrase(user_input: str) -> bool:
    """
    Check if multi-word input is a natural language phrase,
    even though the first word might be a valid command name.
    E.g., "where am i", "find files named test", "set the variable"
    
    Only applies to AMBIGUOUS commands (words that are both
    valid shell commands AND common English words).
    """
    words = user_input.lower().split()
    if len(words) < 2:
        return False

    first = words[0]
    second = words[1]

    # Only apply NL detection to ambiguous commands
    if first not in AMBIGUOUS_COMMANDS:
        return False

    # If the second word is a classic NL word, it's NL
    if second in NL_FOLLOW_WORDS:
        return True

    # Known full NL phrases that start with ambiguous command names
    two_word = f"{first} {second}"
    nl_two_word = {
        "where am", "where is", "where are", "where do", "where does",
        "find files", "find file", "find text",
        "show files", "show me", "show the", "show all", "show my",
        "show running", "show contents", "show directory",
        "set mode",
        "copy file",
        "move file",
        "del file",
        "kill process",
        "start the",
        "sort files",
        "more about", "more info",
        "time is",
        "date is",
        "tree of", "tree for",
        "display files", "display memory", "display time", "display date",
        "display ip", "display environment",
    }

    # If second word has a file extension (e.g., "copy file.txt"), it's a command
    if "." in words[1] and not words[1].startswith("."):
        return False

    if two_word in nl_two_word:
        return True

    return False


def _get_first_token(user_input: str) -> str:
    """Extract the first token (command name) from user input."""
    # Handle quoted paths
    stripped = user_input.strip()
    if stripped.startswith('"'):
        end = stripped.find('"', 1)
        if end != -1:
            return stripped[1:end]
    if stripped.startswith("'"):
        end = stripped.find("'", 1)
        if end != -1:
            return stripped[1:end]
    # Split on whitespace
    parts = stripped.split()
    return parts[0] if parts else ""


def _is_executable_on_path(cmd: str) -> bool:
    """Check if a command exists as an executable on the system PATH."""
    if not cmd:
        return False
    try:
        return shutil.which(cmd) is not None
    except Exception:
        return False


def is_direct_command(user_input: str) -> bool:
    """
    Determine if user input is a direct shell command.
    Returns True if input should be executed directly as a shell command.
    Returns False if input looks like natural language.
    """
    if not user_input or not user_input.strip():
        return False

    stripped = user_input.strip()
    lower = stripped.lower()

    # ── 1. Drive switching (e.g., "D:" or "D:\\") ──
    if DRIVE_PATTERN.match(stripped):
        return True

    # ── 2. Starts with ./ or .\ or absolute path — definitely a command ──
    if stripped.startswith(("./", ".\\", "/", "\\\\")) or (
        len(stripped) > 2 and stripped[1] == ":" and stripped[2] in "/\\"
    ):
        return True

    # ── 3. Contains shell operators (|, >, >>, &&, ;) — definitely a command ──
    if SHELL_OPERATOR_PATTERN.search(stripped):
        return True

    # ── 3.5. NL phrase override ──
    # If a multi-word input LOOKS like natural language (e.g., "where am i",
    # "show me files", "find files named test"), DON'T treat it as a command
    # even if the first word is a known command/builtin.
    if _looks_like_nl_phrase(stripped):
        return False

    # ── 4. Has command-line flags (--version, -v, -h, etc.) ──
    if COMMAND_FLAGS_PATTERN.search(stripped):
        return True

    # ── 5. First token is a known executable ──
    first = _get_first_token(stripped).lower()

    # Strip .exe/.bat/.cmd suffix for matching
    base = re.sub(r'\.(exe|bat|cmd|ps1|sh|py|rb|pl)$', '', first, flags=re.I)

    # Check known sets
    if base in KNOWN_EXECUTABLES:
        return True
    if os.name == 'nt' and base in WINDOWS_BUILTINS:
        return True
    if os.name != 'nt' and base in LINUX_BUILTINS:
        return True

    # ── 6. shutil.which() — the command exists on PATH ──
    if _is_executable_on_path(first):
        return True
    # Also try without extension
    if first != base and _is_executable_on_path(base):
        return True

    # ── 7. Looks like a file path being run ──
    if os.path.sep in first or '/' in first:
        return True

    return False
