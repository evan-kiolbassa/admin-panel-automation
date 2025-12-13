"""Execute Admin Action workflow: clipboard -> validate -> Chivalry 2 console."""

from __future__ import annotations

import re

from admin_panel_automation.models import AdminActionResult
from admin_panel_automation.services.chivalry_console import ChivalryConsoleAutomation


class AdminActionService:
    """Validates and executes an admin action command from the OS clipboard."""

    _PLAYFAB_RE = re.compile(r"^[0-9A-Fa-f]{16,32}$")

    def execute_from_clipboard(self) -> AdminActionResult:
        """Read clipboard, validate command format, execute in Chivalry 2 console.

        Returns
        -------
        AdminActionResult
            Result of validation + execution.
        """
        try:
            ChivalryConsoleAutomation.ensure_windows()
        except RuntimeError as e:
            return AdminActionResult(False, str(e), None)

        command_raw = self._read_clipboard().strip()
        if not command_raw:
            return AdminActionResult(False, "Clipboard is empty. Copy a valid admin command first.", None)

        try:
            command_norm = self._validate_and_normalize(command_raw)
        except ValueError as e:
            return AdminActionResult(False, str(e), None)

        ChivalryConsoleAutomation.paste_and_execute(command_norm, restore_clipboard=True)
        return AdminActionResult(True, "Admin action executed in Chivalry 2 console.", command_norm)

    @staticmethod
    def _read_clipboard() -> str:
        """Read text from OS clipboard."""
        import pyperclip

        try:
            return pyperclip.paste() or ""
        except Exception:
            return ""

    def _validate_and_normalize(self, text: str) -> str:
        """Validate supported command formats and normalize spacing.

        Supported formats
        -----------------
        - KickById <PlayFabId> <reason...>
        - BanById <PlayFabId> <duration_int> <reason...>
        - UnbanById <PlayFabId> <reason...>

        Parameters
        ----------
        text:
            Clipboard text.

        Returns
        -------
        str
            Normalized command string.

        Raises
        ------
        ValueError
            If the text does not match a supported command format.
        """
        parts = text.split()
        if not parts:
            raise ValueError("Clipboard command is empty.")

        verb = parts[0].strip()
        verb_l = verb.casefold()

        if verb_l not in {"kickbyid", "banbyid", "unbanbyid"}:
            raise ValueError(
                "Invalid command. Expected one of: "
                "KickById <PlayFabId> <reason>, "
                "BanById <PlayFabId> <duration_int> <reason>, "
                "UnbanById <PlayFabId> <reason>."
            )

        if verb_l in {"kickbyid", "unbanbyid"}:
            if len(parts) < 3:
                raise ValueError(f"{verb} requires: {verb} <PlayFabId> <reason>.")
            playfab = parts[1]
            reason = " ".join(parts[2:]).strip()
            self._validate_playfab_id(playfab)
            if not reason:
                raise ValueError(f"{verb} requires a non-empty reason.")
            return f"{verb} {playfab} {reason}"

        if len(parts) < 4:
            raise ValueError("BanById requires: BanById <PlayFabId> <duration_int> <reason>.")

        playfab = parts[1]
        duration_s = parts[2]
        reason = " ".join(parts[3:]).strip()

        self._validate_playfab_id(playfab)

        try:
            duration = int(duration_s)
        except ValueError as e:
            raise ValueError("BanById duration must be an integer.") from e

        if duration <= 0:
            raise ValueError("BanById duration must be a positive integer.")

        if not reason:
            raise ValueError("BanById requires a non-empty reason.")

        return f"{verb} {playfab} {duration} {reason}"

    def _validate_playfab_id(self, playfab_id: str) -> None:
        """Validate PlayFabId format.

        Parameters
        ----------
        playfab_id:
            Candidate PlayFabId.

        Raises
        ------
        ValueError
            If the PlayFabId is not acceptable.
        """
        if not self._PLAYFAB_RE.match(playfab_id):
            raise ValueError(
                "Invalid PlayFabId. Expected 16–32 hex characters (0-9, A-F). "
                f"Got: {playfab_id!r}"
            )
