from plugin_loader import load_plugins

def map_command(intent, os_type, e, plugins=None):
    """
    Map an intent + entities to a shell command.
    Returns a command string, an INTERNAL: response, or None.
    """
    # 🔌 Plugin commands
    if plugins:
        for plugin in plugins:
            if intent in plugin.intents:
                return plugin.execute(intent, e, os_type)

    # ─── Entities helper ─────────────────────────────────────────────
    name = e.get("name") or ""
    source = e.get("source") or ""
    destination = e.get("destination") or ""
    drive = e.get("drive") or ""

    # ══════════════════════════════════════════════════════════════════
    # WINDOWS COMMANDS
    # ══════════════════════════════════════════════════════════════════
    if os_type == "WINDOWS":
        # ── File & Directory ──
        if intent == "LIST_FILES":
            return "dir"
        if intent == "CURRENT_DIR":
            return "cd"
        if intent == "GO_BACK":
            return "cd .."
        if intent == "GO_HOME":
            return "cd %USERPROFILE%"
        if intent == "GO_TO" and name:
            return f"cd {name}"
        if intent == "CREATE_FOLDER" and name:
            return f"mkdir {name}"
        if intent == "DELETE_FOLDER" and name:
            return f"rmdir /s /q {name}"
        if intent == "CREATE_FILE" and name:
            return f"type nul > {name}"
        if intent == "DELETE_FILE" and name:
            return f"del {name}"
        if intent == "RENAME_FILE" and source and destination:
            return f"ren {source} {destination}"
        if intent == "MOVE_FILE" and source and destination:
            return f"move {source} {destination}"
        if intent == "COPY_FILE" and source and destination:
            return f"copy {source} {destination}"
        if intent == "CAT_FILE" and name:
            return f"type {name}"

        # ── System & Info ──
        if intent == "SYSTEM_INFO":
            return "systeminfo"
        if intent == "WHOAMI":
            return "whoami"
        if intent == "CHANGE_DRIVE" and drive:
            return f"{drive}:"
        if intent == "CHECK_RAM":
            return "wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value"
        if intent == "CHECK_CPU":
            return "wmic cpu get loadpercentage"
        if intent == "CHECK_DISK":
            return "wmic logicaldisk get size,freespace,caption"
        if intent == "CHECK_IP":
            return "ipconfig"
        if intent == "CHECK_INTERNET":
            return "ping 8.8.8.8 -n 1"
        if intent == "LIST_PROCESSES":
            return "tasklist"
        if intent == "KILL_PROCESS" and name:
            return f"taskkill /IM {name} /F"
        if intent == "CLEAR_SCREEN":
            return "cls"
        if intent == "CHECK_TIME":
            return "time /t"
        if intent == "CHECK_DATE":
            return "date /t"
        if intent == "SYSTEM_UPTIME":
            return 'wmic os get lastbootuptime'

        # ── Package Management ──
        if intent == "UPGRADE_PIP":
            return "python -m pip install --upgrade pip"
        if intent == "UPGRADE_PACKAGE" and name:
            return f"pip install --upgrade {name}"
        if intent == "INSTALL_PACKAGE" and name:
            return f"pip install {name}"

        # ── Search & Find ──
        if intent == "SEARCH_FILES" and name:
            return f'dir /s /b *{name}*'
        if intent == "FIND_TEXT" and name:
            return f'findstr /s /i /n /p "{name}" *.*'

        # ── Version Check ──
        if intent == "CHECK_VERSION" and name:
            return f"{name} --version"

        # ── Run Script ──
        if intent == "RUN_SCRIPT" and name:
            return f"python {name}"

        # ── Editor ──
        if intent == "OPEN_EDITOR" and name:
            return f"notepad {name}"

        # ── Compress / Extract ──
        if intent == "COMPRESS_FILE" and name:
            return f'powershell Compress-Archive -Path "{name}" -DestinationPath "{name}.zip"'
        if intent == "EXTRACT_FILE" and name:
            return f'powershell Expand-Archive -Path "{name}" -DestinationPath "."'

        # ── Download ──
        if intent == "DOWNLOAD_FILE" and name:
            return f'powershell Invoke-WebRequest -Uri "{name}" -OutFile "downloaded_file"'

        # ── Environment ──
        if intent == "SHOW_ENV":
            return "set"

        # ── File/Folder Size ──
        if intent == "SHOW_SIZE" and name:
            return f'powershell (Get-Item "{name}").Length'

        # ── Network ──
        if intent == "NETWORK_STATUS":
            return "netstat -an"

        # ── Power ──
        if intent == "SHUTDOWN":
            return "shutdown /s /t 0"
        if intent == "RESTART":
            return "shutdown /r /t 0"


    # ══════════════════════════════════════════════════════════════════
    # LINUX COMMANDS
    # ══════════════════════════════════════════════════════════════════
    if os_type == "LINUX":
        # ── File & Directory ──
        if intent == "LIST_FILES":
            return "ls -la"
        if intent == "CURRENT_DIR":
            return "pwd"
        if intent == "GO_BACK":
            return "cd .."
        if intent == "GO_HOME":
            return "cd ~"
        if intent == "GO_TO" and name:
            return f"cd {name}"
        if intent == "CREATE_FOLDER" and name:
            return f"mkdir -p {name}"
        if intent == "DELETE_FOLDER" and name:
            return f"rm -rf {name}"
        if intent == "CREATE_FILE" and name:
            return f"touch {name}"
        if intent == "DELETE_FILE" and name:
            return f"rm {name}"
        if intent == "RENAME_FILE" and source and destination:
            return f"mv {source} {destination}"
        if intent == "MOVE_FILE" and source and destination:
            return f"mv {source} {destination}"
        if intent == "COPY_FILE" and source and destination:
            return f"cp {source} {destination}"
        if intent == "CAT_FILE" and name:
            return f"cat {name}"

        # ── System & Info ──
        if intent == "SYSTEM_INFO":
            return "uname -a"
        if intent == "WHOAMI":
            return "whoami"
        if intent == "CHECK_RAM":
            return "free -h"
        if intent == "CHECK_CPU":
            return "top -bn1 | grep 'Cpu(s)'"
        if intent == "CHECK_DISK":
            return "df -h"
        if intent == "CHECK_IP":
            return "hostname -I"
        if intent == "CHECK_INTERNET":
            return "ping -c 1 8.8.8.8"
        if intent == "LIST_PROCESSES":
            return "ps aux"
        if intent == "KILL_PROCESS" and name:
            return f"pkill -f {name}"
        if intent == "CLEAR_SCREEN":
            return "clear"
        if intent == "CHECK_TIME":
            return "date +%T"
        if intent == "CHECK_DATE":
            return "date +%D"
        if intent == "SYSTEM_UPTIME":
            return "uptime"

        # ── Package Management ──
        if intent == "UPGRADE_PIP":
            return "python3 -m pip install --upgrade pip"
        if intent == "UPGRADE_PACKAGE" and name:
            return f"pip install --upgrade {name}"
        if intent == "INSTALL_PACKAGE" and name:
            return f"pip install {name}"

        # ── Search & Find ──
        if intent == "SEARCH_FILES" and name:
            return f'find . -name "*{name}*"'
        if intent == "FIND_TEXT" and name:
            return f'grep -rni "{name}" .'

        # ── Version Check ──
        if intent == "CHECK_VERSION" and name:
            return f"{name} --version"

        # ── Run Script ──
        if intent == "RUN_SCRIPT" and name:
            return f"python3 {name}"

        # ── Editor ──
        if intent == "OPEN_EDITOR" and name:
            return f"nano {name}"

        # ── Compress / Extract ──
        if intent == "COMPRESS_FILE" and name:
            return f'tar -czf "{name}.tar.gz" "{name}"'
        if intent == "EXTRACT_FILE" and name:
            if name.endswith(".zip"):
                return f'unzip "{name}"'
            return f'tar -xzf "{name}"'

        # ── Download ──
        if intent == "DOWNLOAD_FILE" and name:
            return f'wget "{name}"'

        # ── Environment ──
        if intent == "SHOW_ENV":
            return "env"

        # ── File/Folder Size ──
        if intent == "SHOW_SIZE" and name:
            return f'du -sh "{name}"'

        # ── Network ──
        if intent == "NETWORK_STATUS":
            return "ss -tuln"

        # ── Power ──
        if intent == "SHUTDOWN":
            return "sudo shutdown -h now"
        if intent == "RESTART":
            return "sudo reboot"

    return None
