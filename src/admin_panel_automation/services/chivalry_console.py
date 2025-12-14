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
    def _press_virtual_key(vk_code: int) -> None:
        """Press and release a Windows virtual-key code."""
        import ctypes
        from ctypes import wintypes

        INPUT_KEYBOARD = 1
        KEYEVENTF_KEYUP = 0x0002
        KEYEVENTF_SCANCODE = 0x0008
        MAPVK_VK_TO_VSC = 0

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", wintypes.ULONG_PTR),
            ]

        class INPUT(ctypes.Structure):
            class _INPUT_UNION(ctypes.Union):
                _fields_ = [("ki", KEYBDINPUT)]

            _anonymous_ = ("u",)
            _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]

        send_input = ctypes.windll.user32.SendInput
        send_input.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
        send_input.restype = wintypes.UINT

        map_virtual_key = ctypes.windll.user32.MapVirtualKeyW
        map_virtual_key.argtypes = (wintypes.UINT, wintypes.UINT)
        map_virtual_key.restype = wintypes.UINT

        scan_code = map_virtual_key(vk_code, MAPVK_VK_TO_VSC)

        inputs = (INPUT * 2)(
            INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(wVk=0, wScan=scan_code, dwFlags=KEYEVENTF_SCANCODE, time=0, dwExtraInfo=0),
            ),
            INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(
                    wVk=0,
                    wScan=scan_code,
                    dwFlags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP,
                    time=0,
                    dwExtraInfo=0,
                ),
            ),
        )

        sent = send_input(2, inputs, ctypes.sizeof(INPUT))
        if sent != 2:
            raise OSError(f"Failed to send VK 0x{vk_code:02X} (SendInput sent {sent}/2).")

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
        time.sleep(GAME_CONFIG.focus_delay_s)

    @classmethod
    def open_console(cls) -> None:
        """Open the in-game console."""
        cls.ensure_windows()
        if GAME_CONFIG.pre_console_escape:
            try:
                cls._press_virtual_key(0x1B)  # VK_ESCAPE
                time.sleep(0.05)
            except Exception:
                pass
        try:
            cls._press_virtual_key(GAME_CONFIG.console_open_vk)
        except Exception:
            from pywinauto.keyboard import send_keys

            send_keys("`", pause=0.02)

    @classmethod
    def paste_and_execute(cls, command: str, restore_clipboard: bool = True) -> None:
        """Open the console, type `command`, and press Enter.

        Parameters
        ----------
        command:
            Console command to execute.
        restore_clipboard:
            Unused (kept for backwards compatibility).
        """
        from pywinauto.keyboard import send_keys

        cls.focus_window()

        cls.open_console()
        time.sleep(GAME_CONFIG.console_open_delay_s)
        send_keys(command, with_spaces=True, pause=0.01)
        send_keys("{ENTER}", pause=0.02)

        # Keep game in foreground.
        time.sleep(0.2)
