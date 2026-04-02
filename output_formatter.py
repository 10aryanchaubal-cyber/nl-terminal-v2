from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich import box
from rich.markdown import Markdown


def format_ai_insight(text):
    return Panel(Markdown(text), title="AI Insight", border_style="magenta", expand=False, box=box.ASCII)


def format_ai_explanation(text):
    return Panel(Markdown(text), title="Explanation", border_style="cyan", expand=False, box=box.ASCII)


def format_ai_lesson(text):
    return Panel(Markdown(text), title="AI Tutor", border_style="yellow", expand=False, box=box.ASCII)


def format_output(intent, stdout, os_type):
    """
    Routes raw output to specific formatters based on intent.
    Returns a Rich renderable (Table, Panel, etc.) or None if no formatting applies.
    """
    if not stdout.strip():
        return None

    if intent == "CHECK_RAM":
        return format_ram(stdout, os_type)
    if intent == "CHECK_CPU":
        return format_cpu(stdout, os_type)
    if intent == "CHECK_DISK":
        return format_disk(stdout, os_type)
    if intent == "CHECK_IP":
        return format_ip(stdout, os_type)
    if intent == "LIST_PROCESSES":
        return format_processes(stdout, os_type)

    return None


def format_ram(stdout, os_type):
    try:
        table = Table(title="Memory Status", box=box.ASCII)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        if os_type == "WINDOWS":
            # Output: FreePhysicalMemory=123456\nTotalVisibleMemorySize=234567
            lines = [l.strip() for l in stdout.split("\n") if l.strip()]
            data = {}
            for line in lines:
                if "=" in line:
                    k, v = line.split("=", 1)
                    data[k] = int(v)

            free_mb = data.get("FreePhysicalMemory", 0) / 1024
            total_mb = data.get("TotalVisibleMemorySize", 0) / 1024
            used_mb = total_mb - free_mb
            percent = (used_mb / total_mb) * 100 if total_mb else 0

            table.add_row("Total Memory", f"{total_mb/1024:.2f} GB")
            table.add_row("Used Memory", f"{used_mb/1024:.2f} GB")
            table.add_row("Free Memory", f"{free_mb/1024:.2f} GB")
            table.add_row("Usage", f"{percent:.1f}%")
            return table

        else:  # Linux
            # Output from free -h is already a table, but we can parse it to make it prettier
            #               total        used        free      shared  buff/cache   available
            # Mem:           15G        5.2G        8.1G        280M        2.1G        9.8G
            lines = stdout.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                if parts[0] == "Mem:":
                    table.add_row("Total", parts[1])
                    table.add_row("Used", parts[2])
                    table.add_row("Free", parts[3])
                    table.add_row("Available", parts[6] if len(parts) > 6 else parts[5])
                    return table

    except Exception:
        return None  # Fallback to raw output on error
    return None


def format_cpu(stdout, os_type):
    try:
        if os_type == "WINDOWS":
            # Output: 14 (just the number usually, specifically wmic cpu get loadpercentage)
            # Or: LoadPercentage \n 14
            lines = stdout.strip().split()
            load = None
            for part in lines:
                if part.isdigit():
                    load = part
                    break

            if load:
                return Panel(f"[bold green]{load}%[/bold green]", title="CPU Usage", expand=False, box=box.ASCII)
        else:
            # %Cpu(s):  6.2 us,  2.0 sy, ...
            return Panel(stdout.strip(), title="CPU Status", expand=False, box=box.ASCII)

    except Exception:
        return None
    return None


def format_disk(stdout, os_type):
    try:
        table = Table(title="Disk Usage", box=box.ASCII)
        table.add_column("Drive/Mount")
        table.add_column("Size")
        table.add_column("Free")

        if os_type == "WINDOWS":
            # Caption  FreeSpace     Size
            # C:       12345         23456
            lines = stdout.strip().split("\n")
            # Skip header
            for line in lines:
                if "Caption" in line or not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    # wmic output order isn't guaranteed fixed by column, usually Caption Free Size based on query
                    # query was: wmic logicaldisk get size,freespace,caption
                    # default alphabetical: Caption, FreeSpace, Size
                    # Ex: C: 12345 56789
                    caption = parts[0]
                    free = int(parts[1])
                    size = int(parts[2])

                    free_gb = free / (1024**3)
                    size_gb = size / (1024**3)

                    table.add_row(caption, f"{size_gb:.2f} GB", f"{free_gb:.2f} GB")
            return table
        else:
            # Filesystem      Size  Used Avail Use% Mounted on
            lines = stdout.strip().split("\n")
            for line in lines[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 6:
                    table.add_row(parts[0], parts[1], parts[3])
            return table

    except Exception:
        return None
    return None


def format_ip(stdout, os_type):
    # Just wrap it nicely
    return Panel(Text(stdout.strip(), style="bold yellow"), title="Network Info", border_style="blue", box=box.ASCII)


def format_processes(stdout, os_type):
    try:
        table = Table(title="Top Processes", box=box.ASCII)

        if os_type == "WINDOWS":
            # Image Name                     PID Session Name        Session#    Mem Usage
            # System Idle Process              0 Services                   0          8 K
            # Parsing this is hard because spaces in names.
            # We will just take the first N lines and make them a generic table row

            lines = stdout.strip().split("\n")
            # Header is usually lines[0], separator lines[1]
            if len(lines) > 3:
                table.add_column("Process Output (Top 15)")
                for line in lines[:18]:  # Header + sep + 15 rows
                    table.add_row(line)
                return table
        else:
            lines = stdout.strip().split("\n")
            table.add_column("Output (Top 15)")
            for line in lines[:16]:
                table.add_row(line)
            return table

    except Exception:
        return None
    return None
