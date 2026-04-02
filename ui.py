from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from theme import custom_theme, COLORS
import shutil
import sys
import time


class TerminalUI:
    def __init__(self, mode, os_type):
        self.console = Console(theme=custom_theme)
        self.mode = mode
        self.os_type = os_type
        self.spinner = None

    def _safe_text(self, text):
        """
        Ensure text is printable on the active terminal encoding.
        """
        if text is None:
            return ""
        if not isinstance(text, str):
            return text
        cleaned = text.replace("\x00", "")
        try:
            return cleaned.encode("ascii", errors="replace").decode("ascii", errors="replace")
        except Exception:
            return cleaned.encode("utf-8", errors="replace").decode("utf-8", errors="replace")

    def _terminal_width(self):
        return shutil.get_terminal_size(fallback=(80, 24)).columns

    def _prompt_text(self):
        mode_style = "prompt"
        if self.mode == "expert":
            mode_style = "red"
        elif self.mode == "safe":
            mode_style = "green"

        prompt = Text("➜ ", style=mode_style)
        prompt.append(self.mode.upper(), style=mode_style)
        return prompt

    def _print_prompt_buffer(self, buffer_text=""):
        prompt = self._prompt_text()
        prompt.append(" ")
        if buffer_text:
            prompt.append(self._safe_text(buffer_text), style="foreground")
        self.console.print(prompt, end="")

    def _get_responsive_startup_input(self):
        if sys.platform != "win32":
            return Prompt.ask(self._prompt_text(), console=self.console)

        try:
            import msvcrt
        except ImportError:
            return Prompt.ask(self._prompt_text(), console=self.console)

        buffer = []
        last_width = self._terminal_width()
        self._print_prompt_buffer()

        while True:
            current_width = self._terminal_width()
            if current_width != last_width:
                last_width = current_width
                self.welcome_screen()
                self._print_prompt_buffer("".join(buffer))

            if not msvcrt.kbhit():
                time.sleep(0.05)
                continue

            char = msvcrt.getwch()

            if char == "\x03":
                raise KeyboardInterrupt

            if char in ("\r", "\n"):
                self.console.print()
                return "".join(buffer)

            if char in ("\x00", "\xe0"):
                msvcrt.getwch()
                continue

            if char == "\b":
                if buffer:
                    buffer.pop()
                    self.welcome_screen()
                    self._print_prompt_buffer("".join(buffer))
                continue

            if char.isprintable():
                buffer.append(char)
                self.console.print(self._safe_text(char), end="")

    def update_mode(self, mode):
        self.mode = mode

    def clear(self):
        self.console.clear()

    def welcome_screen(self):
        self.clear()
        title = Text(" NL-Terminal v2.0 ", style="panel.title")
        subtitle = Text(f"Mode: {self.mode.upper()}  |  OS: {self.os_type}", style="comment")

        welcome_panel = Panel(
            Text.assemble(
                ("\nWelcome to the Future of Command Line Interfaces.\n", "info"),
                ("Type 'help' or anything in natural language to get started.\n", "foreground"),
                justify="center",
            ),
            title=title,
            subtitle=subtitle,
            border_style="panel.border",
            padding=(1, 2),
            expand=True,
        )
        self.console.print(welcome_panel)
        self.console.print(Rule(style="comment"))
        self.console.print()

    def get_input(self, responsive_startup=False):
        if responsive_startup:
            return self._get_responsive_startup_input()

        return Prompt.ask(
            self._prompt_text(),
            console=self.console,
        )

    def print_command_execution(self, command):
        self.console.print(f"[comment]Executing:[/comment] [command]{command}[/command]")

    def print_ai_thinking(self):
        self.spinner = self.console.status(
            "[ai.thinking]AI is thinking...[/ai.thinking]", spinner="dots"
        )
        self.spinner.start()

    def stop_ai_thinking(self):
        if self.spinner:
            self.spinner.stop()
            self.spinner = None

    def print_ai_response(self, text):
        self.stop_ai_thinking()
        renderable = self._safe_text(text) if isinstance(text, str) else text
        panel = Panel(
            renderable,
            title="[ai.thinking]AI Knowledge[/ai.thinking]",
            border_style="purple",
            expand=False,
        )
        self.console.print(panel)

    def print_error(self, message):
        self.stop_ai_thinking()
        self.console.print(f"[error]✖ Error:[/error] {self._safe_text(message)}")

    def print_success(self, message):
        self.stop_ai_thinking()
        self.console.print(f"[success]✔ Success:[/success] {self._safe_text(message)}")

    def print_info(self, message):
        self.console.print(f"[info]ℹ Info:[/info] {self._safe_text(message)}")

    def print_warning(self, message):
        self.console.print(f"[warning]⚠ Warning:[/warning] {self._safe_text(message)}")

    def print_help(self):
        help_content = Group(
            Text("Direct Commands", style="bold green"),
            Text("Type any shell command as you normally would:", style="foreground"),
            Text("  gcc --version - git status - pip list - dir - node -v", style="comment"),
            Text("  tasklist | findstr python - echo hello > test.txt", style="comment"),
            Text(""),
            Text("Natural Language", style="bold green"),
            Text("Speak naturally:", style="foreground"),
            Text('  "show me all files" - "create folder projects"', style="comment"),
            Text('  "check ram usage" - "what is my IP address"', style="comment"),
            Text('  "find text TODO in python files"', style="comment"),
            Text(""),
            Text("AI Features", style="bold green"),
            Text("  explain <command>  - Get AI explanation of any command", style="comment"),
            Text("  teach me <topic>   - Learn terminal concepts", style="comment"),
            Text(""),
            Text("Modes", style="bold green"),
            Text('  "switch to expert" - "set mode safe" - "mode beginner"', style="comment"),
            Text("Rollback", style="bold green"),
            Text('  "undo" - "rollback" - Restore deleted files', style="comment"),
            Text("Exit", style="bold green"),
            Text('  "exit" or "quit"', style="comment"),
        )

        panel = Panel(
            help_content,
            title=Text(" NL-Terminal v2.0 - Quick Guide ", style="panel.title"),
            border_style="panel.border",
            padding=(1, 2),
            expand=True,
        )
        self.console.print(panel)

    def stream_output(self, output, markup=False):
        if isinstance(output, str):
            output = self._safe_text(output)
            self.console.print(
                output,
                style="foreground",
                markup=markup,
                highlight=False,
                emoji=False,
            )
            return
        self.console.print(output, style="foreground")
