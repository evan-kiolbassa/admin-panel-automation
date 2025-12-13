"""Data models shared across GUI, worker, and services."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Optional


class BrowserType(enum.Enum):
    """Supported browser selections from the GUI."""

    CHROME = "chrome"
    EDGE = "edge"
    FIREFOX = "firefox"


@dataclass(frozen=True)
class AuthResult:
    """Outcome of an authentication attempt.

    Parameters
    ----------
    success:
        True if authenticated as the requested profile.
    message:
        Human-readable status message.
    detected_profile:
        Profile parsed from navbar element (e.g., from `Profile (ARTISANAL)`), if present.
    """

    success: bool
    message: str
    detected_profile: Optional[str] = None


@dataclass(frozen=True)
class ParseResult:
    """Outcome of a Parse Player List attempt.

    Parameters
    ----------
    success:
        True if clipboard was captured and submitted to the web app.
    message:
        Human-readable status message.
    clipboard_chars:
        Size of clipboard content captured.
    """

    success: bool
    message: str
    clipboard_chars: int = 0


@dataclass(frozen=True)
class AdminActionResult:
    """Outcome of an Execute Admin Action attempt.

    Parameters
    ----------
    success:
        True if a valid command was executed in the game console.
    message:
        Human-readable status message.
    executed_command:
        Normalized command string executed, if any.
    """

    success: bool
    message: str
    executed_command: Optional[str] = None
