import subprocess
import shlex
import os

INTERACTIVE_COMMANDS = {
    "vim", "nano", "top", "htop",
    "less", "more",
    "python", "python3", "py",
    "bash", "sh", "zsh",
    "cmd", "powershell", "pwsh",
    "irb", "node", "lua",
    "mysql", "psql", "sqlite3", "mongosh",
    "gdb", "lldb",
}

def is_interactive(command):
    try:
        parts = shlex.split(command)
        if not parts:
            return False
        base = parts[0].lower()
        # "python script.py" is NOT interactive, but "python" alone IS
        if base in INTERACTIVE_COMMANDS and len(parts) == 1:
            return True
        # "python -i" is interactive
        if base in {"python", "python3", "py"} and "-i" in parts:
            return True
        return False
    except Exception:
        return False


def execute(command):
    """
    Execute a shell command and return (stdout, stderr).
    
    Smart stderr handling:
    - If return code is 0, stderr is treated as informational (not an error).
      Many tools (gcc --version, java -version, git, ffmpeg, etc.) write to stderr.
    - If return code != 0, stderr is treated as an actual error.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd(),
            env=os.environ.copy(),
            encoding="utf-8",
            errors="ignore",
            timeout=60,
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        # Smart stderr handling:
        # If the command succeeded (rc=0), merge stderr into stdout.
        # Many legitimate tools write to stderr even on success.
        if result.returncode == 0:
            if stderr and not stdout.strip():
                # Command only wrote to stderr (e.g., gcc --version, java -version)
                return stderr, ""
            elif stderr:
                # Command wrote to both — append stderr as info
                return stdout + "\n" + stderr, ""
            return stdout, ""
        else:
            # Command genuinely failed
            # Still return stdout if it has content (partial output)
            return stdout, stderr

    except subprocess.TimeoutExpired:
        return "", "Command timed out after 60 seconds."
    except Exception as e:
        return "", str(e)
