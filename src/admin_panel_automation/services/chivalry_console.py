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
    def _press_vk_keybd_event(vk_code: int) -> None:
        """Press and release a Windows virtual-key code via keybd_event (fallback)."""
        import ctypes
        from ctypes import wintypes

        ULONG_PTR = getattr(wintypes, "ULONG_PTR", ctypes.c_void_p)

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        map_virtual_key = user32.MapVirtualKeyW
        map_virtual_key.argtypes = (wintypes.UINT, wintypes.UINT)
        map_virtual_key.restype = wintypes.UINT

        keybd_event = user32.keybd_event
        keybd_event.argtypes = (wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ULONG_PTR)
        keybd_event.restype = None

        scan = map_virtual_key(vk_code, 0) & 0xFF
        ctypes.set_last_error(0)
        keybd_event(vk_code & 0xFF, scan, 0, 0)
        keybd_event(vk_code & 0xFF, scan, 0x0002, 0)  # KEYEVENTF_KEYUP

    @staticmethod
    def _send_vk_chord(vk_modifier: int, vk_key: int) -> None:
        """Send a chord like Ctrl+V via SendInput (down/up events)."""
        import ctypes
        from ctypes import wintypes

        ULONG_PTR = getattr(wintypes, "ULONG_PTR", ctypes.c_void_p)

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
                ("dwExtraInfo", ULONG_PTR),
            ]

        class INPUT(ctypes.Structure):
            class _INPUT_UNION(ctypes.Union):
                _fields_ = [("ki", KEYBDINPUT)]

            _anonymous_ = ("u",)
            _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        send_input = user32.SendInput
        send_input.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
        send_input.restype = wintypes.UINT

        map_virtual_key = user32.MapVirtualKeyW
        map_virtual_key.argtypes = (wintypes.UINT, wintypes.UINT)
        map_virtual_key.restype = wintypes.UINT

        mod_scan = map_virtual_key(vk_modifier, MAPVK_VK_TO_VSC)
        key_scan = map_virtual_key(vk_key, MAPVK_VK_TO_VSC)
        if not mod_scan or not key_scan:
            raise OSError("MapVirtualKeyW failed for modifier/key chord.")

        events = (INPUT * 4)(
            INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=0, wScan=mod_scan, dwFlags=KEYEVENTF_SCANCODE, time=0, dwExtraInfo=0)),
            INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=0, wScan=key_scan, dwFlags=KEYEVENTF_SCANCODE, time=0, dwExtraInfo=0)),
            INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=0, wScan=key_scan, dwFlags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)),
            INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=0, wScan=mod_scan, dwFlags=KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, time=0, dwExtraInfo=0)),
        )

        sent = send_input(4, events, ctypes.sizeof(INPUT))
        if sent != 4:
            err = ctypes.get_last_error()
            raise OSError(f"Failed to send chord (SendInput sent {sent}/4, err={err}).")

    @staticmethod
    def _press_virtual_key(vk_code: int) -> None:
        """Press and release a Windows virtual-key code."""
        import ctypes
        from ctypes import wintypes

        ULONG_PTR = getattr(wintypes, "ULONG_PTR", ctypes.c_void_p)

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
                ("dwExtraInfo", ULONG_PTR),
            ]

        class INPUT(ctypes.Structure):
            class _INPUT_UNION(ctypes.Union):
                _fields_ = [("ki", KEYBDINPUT)]

            _anonymous_ = ("u",)
            _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]

        user32 = ctypes.WinDLL("user32", use_last_error=True)

        send_input = user32.SendInput
        send_input.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
        send_input.restype = wintypes.UINT

        map_virtual_key = user32.MapVirtualKeyW
        map_virtual_key.argtypes = (wintypes.UINT, wintypes.UINT)
        map_virtual_key.restype = wintypes.UINT

        scan_code = map_virtual_key(vk_code, MAPVK_VK_TO_VSC)
        if not scan_code:
            raise OSError(f"MapVirtualKeyW failed for VK 0x{vk_code:02X}.")

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
            err = ctypes.get_last_error()
            raise OSError(f"Failed to send VK 0x{vk_code:02X} (SendInput sent {sent}/2, err={err}).")

    @staticmethod
    def _press_scan_code(scan_code: int) -> None:
        """Press and release a keyboard scan code (layout-independent)."""
        import ctypes
        from ctypes import wintypes

        ULONG_PTR = getattr(wintypes, "ULONG_PTR", ctypes.c_void_p)

        INPUT_KEYBOARD = 1
        KEYEVENTF_KEYUP = 0x0002
        KEYEVENTF_SCANCODE = 0x0008

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR),
            ]

        class INPUT(ctypes.Structure):
            class _INPUT_UNION(ctypes.Union):
                _fields_ = [("ki", KEYBDINPUT)]

            _anonymous_ = ("u",)
            _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]

        user32 = ctypes.WinDLL("user32", use_last_error=True)

        send_input = user32.SendInput
        send_input.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
        send_input.restype = wintypes.UINT

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
            err = ctypes.get_last_error()
            raise OSError(
                f"Failed to send scan code 0x{scan_code:02X} (SendInput sent {sent}/2, err={err})."
            )

    @staticmethod
    def _send_text_unicode(text: str) -> None:
        """Send text as Unicode keystrokes to the active foreground window."""
        import ctypes
        from ctypes import wintypes

        ULONG_PTR = getattr(wintypes, "ULONG_PTR", ctypes.c_void_p)

        INPUT_KEYBOARD = 1
        KEYEVENTF_KEYUP = 0x0002
        KEYEVENTF_UNICODE = 0x0004

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR),
            ]

        class INPUT(ctypes.Structure):
            class _INPUT_UNION(ctypes.Union):
                _fields_ = [("ki", KEYBDINPUT)]

            _anonymous_ = ("u",)
            _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]

        user32 = ctypes.WinDLL("user32", use_last_error=True)

        send_input = user32.SendInput
        send_input.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
        send_input.restype = wintypes.UINT

        inputs = []
        for ch in text:
            code = ord(ch)
            inputs.append(
                INPUT(
                    type=INPUT_KEYBOARD,
                    ki=KEYBDINPUT(wVk=0, wScan=code, dwFlags=KEYEVENTF_UNICODE, time=0, dwExtraInfo=0),
                )
            )
            inputs.append(
                INPUT(
                    type=INPUT_KEYBOARD,
                    ki=KEYBDINPUT(
                        wVk=0,
                        wScan=code,
                        dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                        time=0,
                        dwExtraInfo=0,
                    ),
                )
            )

        if not inputs:
            return

        arr = (INPUT * len(inputs))(*inputs)
        sent = send_input(len(arr), arr, ctypes.sizeof(INPUT))
        if sent != len(arr):
            err = ctypes.get_last_error()
            raise OSError(f"Failed to send Unicode text (SendInput sent {sent}/{len(arr)}, err={err}).")

    @staticmethod
    def _get_foreground_window_handle() -> int:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        get_foreground = user32.GetForegroundWindow
        get_foreground.argtypes = ()
        get_foreground.restype = wintypes.HWND
        hwnd = get_foreground()
        return int(hwnd) if hwnd else 0

    @staticmethod
    def _get_window_text(hwnd: int) -> str:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        get_len = user32.GetWindowTextLengthW
        get_len.argtypes = (wintypes.HWND,)
        get_len.restype = ctypes.c_int

        get_text = user32.GetWindowTextW
        get_text.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
        get_text.restype = ctypes.c_int

        handle = wintypes.HWND(hwnd)
        length = int(get_len(handle))
        buf = ctypes.create_unicode_buffer(max(length + 1, 512))
        get_text(handle, buf, len(buf))
        return buf.value

    @classmethod
    def _wait_for_foreground(cls, hwnd: int, timeout_s: float = 1.5) -> bool:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if cls._get_foreground_window_handle() == hwnd:
                return True
            time.sleep(0.05)
        return False

    @staticmethod
    def _force_foreground_window(hwnd: int) -> None:
        """Best-effort: force `hwnd` to foreground without mouse clicks."""
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)

        get_foreground = user32.GetForegroundWindow
        get_foreground.argtypes = ()
        get_foreground.restype = wintypes.HWND

        get_window_thread = user32.GetWindowThreadProcessId
        get_window_thread.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
        get_window_thread.restype = wintypes.DWORD

        attach_thread_input = user32.AttachThreadInput
        attach_thread_input.argtypes = (wintypes.DWORD, wintypes.DWORD, wintypes.BOOL)
        attach_thread_input.restype = wintypes.BOOL

        set_foreground = user32.SetForegroundWindow
        set_foreground.argtypes = (wintypes.HWND,)
        set_foreground.restype = wintypes.BOOL

        switch_to = getattr(user32, "SwitchToThisWindow", None)
        if switch_to is not None:
            switch_to.argtypes = (wintypes.HWND, wintypes.BOOL)
            switch_to.restype = None

        bring_to_top = user32.BringWindowToTop
        bring_to_top.argtypes = (wintypes.HWND,)
        bring_to_top.restype = wintypes.BOOL

        show_window = user32.ShowWindow
        show_window.argtypes = (wintypes.HWND, ctypes.c_int)
        show_window.restype = wintypes.BOOL

        get_current_thread = user32.GetCurrentThreadId
        get_current_thread.argtypes = ()
        get_current_thread.restype = wintypes.DWORD

        SW_RESTORE = 9

        target = wintypes.HWND(hwnd)
        show_window(target, SW_RESTORE)
        bring_to_top(target)

        fg = get_foreground()
        fg_tid = 0
        if fg:
            fg_pid = wintypes.DWORD()
            fg_tid = int(get_window_thread(fg, ctypes.byref(fg_pid)))

        target_pid = wintypes.DWORD()
        target_tid = int(get_window_thread(target, ctypes.byref(target_pid)))
        cur_tid = get_current_thread()

        attached_1 = attached_2 = False
        try:
            if fg_tid and fg_tid != cur_tid:
                attached_1 = bool(attach_thread_input(fg_tid, cur_tid, True))
            if target_tid and target_tid != cur_tid:
                attached_2 = bool(attach_thread_input(target_tid, cur_tid, True))
            ok = bool(set_foreground(target))
            if not ok and switch_to is not None:
                switch_to(target, True)
        finally:
            if attached_2:
                attach_thread_input(target_tid, cur_tid, False)
            if attached_1:
                attach_thread_input(fg_tid, cur_tid, False)

    @classmethod
    def _press_enter(cls) -> None:
        """Press Enter with multiple fallbacks (some environments block SendInput for VK_RETURN)."""
        errors: list[Exception] = []
        try:
            cls._press_virtual_key(0x0D)  # VK_RETURN
            return
        except Exception as e:
            errors.append(e)

        try:
            cls._press_scan_code(0x1C)  # ENTER
            return
        except Exception as e:
            errors.append(e)

        try:
            cls._press_vk_keybd_event(0x0D)  # VK_RETURN
            return
        except Exception as e:
            errors.append(e)

        try:
            from pywinauto.keyboard import send_keys

            send_keys("{ENTER}", pause=0.02)
            return
        except Exception as e:
            errors.append(e)

        msg = "; ".join(str(e) for e in errors if str(e))
        raise RuntimeError(f"Failed to press Enter. {msg}") from errors[0]

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
        cls.ensure_windows()
        from pywinauto import Desktop

        desktop = Desktop(backend="win32")
        preferred = cls._match.title_exact_preferred.casefold()
        candidates: list[tuple[tuple[int, int], object, str]] = []
        for w in desktop.windows():
            try:
                if hasattr(w, "is_visible") and not w.is_visible():
                    continue
                title = w.window_text()
            except Exception:
                continue
            if not title:
                continue

            title_clean = title.strip()
            title_cf = title_clean.casefold()
            if cls._match.title_contains not in title_cf:
                continue

            if title_cf == preferred:
                score = (0, len(title_clean))
            elif preferred in title_cf:
                score = (1, len(title_clean))
            else:
                score = (2, len(title_clean))
            candidates.append((score, w, title_clean))

        if not candidates:
            raise RuntimeError('Could not find an active "Chivalry 2" window. Make sure you are in-game.')

        candidates.sort(key=lambda item: item[0])
        win = candidates[0][1]
        target_title = candidates[0][2]
        hwnd = int(win.handle)
        errors: list[Exception] = []
        try:
            cls._force_foreground_window(hwnd)
        except Exception as e:
            errors.append(e)
        try:
            win.set_focus()
        except Exception as e:
            errors.append(e)
        if GAME_CONFIG.click_to_focus:
            try:
                win.click_input(coords=(50, 50))
            except Exception:
                pass
        if not cls._wait_for_foreground(hwnd):
            fg_hwnd = cls._get_foreground_window_handle()
            fg_title = cls._get_window_text(fg_hwnd) if fg_hwnd else ""
            err_text = "; ".join(str(e) for e in errors if str(e))
            raise RuntimeError(
                f'Failed to focus "{target_title}" (0x{hwnd:08X}). '
                f'Foreground is "{fg_title}" (0x{fg_hwnd:08X}). {err_text}'
            )
        time.sleep(GAME_CONFIG.focus_delay_s)

    @classmethod
    def open_console(cls) -> None:
        """Open the in-game console."""
        cls.ensure_windows()
        if GAME_CONFIG.pre_console_escape:
            try:
                cls._press_virtual_key(0x1B)  # VK_ESCAPE
                time.sleep(GAME_CONFIG.after_escape_delay_s)
            except Exception:
                pass
        errors: list[Exception] = []

        # Prefer physical key delivery over text, because games often ignore character input.
        # Note: if all of these fail, we raise (rather than "typing a `") so failures are visible.
        try:
            cls._press_vk_keybd_event(GAME_CONFIG.console_open_vk)
            return
        except Exception as e:
            errors.append(e)

        try:
            cls._press_scan_code(GAME_CONFIG.console_open_scan_code)
            return
        except Exception as e:
            errors.append(e)

        try:
            cls._press_virtual_key(GAME_CONFIG.console_open_vk)
            return
        except Exception as e:
            errors.append(e)

        msg = "; ".join(str(e) for e in errors if str(e))
        raise RuntimeError(f"Failed to open console. {msg}") from errors[0]

    @classmethod
    def paste_and_execute(cls, command: str, restore_clipboard: bool = True) -> None:
        """Open the console, type `command`, and press Enter.

        Parameters
        ----------
        command:
            Console command to execute.
        restore_clipboard:
            If True, restores clipboard contents after execution.
        """
        import pyperclip

        old_clip = None
        if restore_clipboard:
            try:
                old_clip = pyperclip.paste()
            except Exception:
                old_clip = None

        cls.focus_window()

        cls.open_console()
        time.sleep(GAME_CONFIG.console_open_delay_s)
        try:
            from pywinauto.keyboard import send_keys

            send_keys(command, with_spaces=True, pause=0.01)
        except Exception:
            cls._send_text_unicode(command)

        try:
            from pywinauto.keyboard import send_keys

            send_keys("{ENTER}", pause=0.02)
        except Exception:
            cls._press_enter()

        # Keep game in foreground.
        time.sleep(GAME_CONFIG.after_command_delay_s)

        if restore_clipboard and old_clip is not None:
            try:
                pyperclip.copy(old_clip)
            except Exception:
                pass

    @classmethod
    def paste_clipboard_and_execute(cls, command: str, restore_clipboard: bool = True) -> None:
        """Focus game, open console, Ctrl+V, Enter.

        This matches the manual workflow: focus -> ` -> paste -> enter.
        """
        import pyperclip

        cls.ensure_windows()

        old_clip = None
        if restore_clipboard:
            try:
                old_clip = pyperclip.paste()
            except Exception:
                old_clip = None

        cls.focus_window()
        cls.open_console()
        time.sleep(GAME_CONFIG.console_open_delay_s)

        try:
            pyperclip.copy(command)
        except Exception:
            raise RuntimeError("Failed to write command to clipboard.")

        # Prefer a real Ctrl+V chord; fall back to send_keys if blocked.
        try:
            cls._send_vk_chord(0x11, 0x56)  # VK_CONTROL + VK_V
        except Exception:
            from pywinauto.keyboard import send_keys

            send_keys("^v", pause=0.02)

        time.sleep(0.05)
        cls._press_enter()
        time.sleep(GAME_CONFIG.after_command_delay_s)

        if restore_clipboard and old_clip is not None:
            try:
                pyperclip.copy(old_clip)
            except Exception:
                pass
