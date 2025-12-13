"""Windows-only helpers for sending commands to the Chivalry 2 in-game console."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from admin_panel_automation.config import GAME_CONFIG


@dataclass(frozen=True)
class ChivalryWindowMatch:
    """Window matching configuration for locating Chivalry 2."""

    title_contains: str = "chivalry"
    title_exact_preferred: str = "chivalry 2"


class ChivalryConsoleAutomation:
    """Automation for focusing Chivalry 2 and issuing console commands (Windows only)."""

    _match = ChivalryWindowMatch()

    @staticmethod
    def ensure_windows() -> None:
        """Raise if not running on Windows."""
        if os.name != "nt":
            raise RuntimeError("Chivalry 2 automation is only supported on Windows.")

    @classmethod
    def focus_window(cls) -> None:
        """Bring the Chivalry 2 window to the foreground.

        Raises
        ------
        RuntimeError
            If no suitable window is found.
        """
        from pywinauto import Desktop

        desktop = Desktop(backend="win32")
        candidates = []
        for w in desktop.windows():
            try:
                title = w.window_text()
            except Exception:
                continue
            if title and cls._match.title_contains in title.casefold():
                candidates.append(w)

        if not candidates:
            raise RuntimeError('Could not find an active "Chivalry 2" window. Make sure you are in-game.')

        candidates.sort(
            key=lambda w: 0 if w.window_text().strip().casefold() == cls._match.title_exact_preferred else 1
        )
        win = candidates[0]
        win.set_focus()
        time.sleep(0.2)

    @classmethod
    def paste_and_execute(cls, command: str, restore_clipboard: bool = True) -> None:
        """Open the console, paste `command`, and press Enter.

        Parameters
        ----------
        command:
            Console command to execute.
        restore_clipboard:
            If True, restores the clipboard contents after execution.
        """
        import pyperclip
        from pywinauto.keyboard import send_keys

        old_clip = pyperclip.paste()
        pyperclip.copy(command)

        cls.focus_window()

        send_keys(GAME_CONFIG.console_key_vk, pause=0.02)
        time.sleep(0.12)
        send_keys("^v{ENTER}", pause=0.02)

        # Keep game in foreground.
        time.sleep(0.2)

        if restore_clipboard:
            try:
                pyperclip.copy(old_clip)
            except Exception:
                pass
