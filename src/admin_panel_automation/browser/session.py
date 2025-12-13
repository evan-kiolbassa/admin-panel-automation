"""Playwright persistent browser session management."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from playwright.sync_api import BrowserContext, Error as PlaywrightError, Page, sync_playwright

from admin_panel_automation.models import BrowserType


@dataclass(frozen=True)
class AppPaths:
    """Filesystem paths used by the app.

    Parameters
    ----------
    data_dir:
        Base directory for app data (persistent browser profiles live under here).
    """

    data_dir: Path

    @staticmethod
    def default() -> "AppPaths":
        """Create default paths appropriate for the current OS/user."""
        import os

        if os.name == "nt":
            root = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
        else:
            root = Path.home()
        return AppPaths(data_dir=root / "AdminPanelAutomation")


def _safe_dirname(value: str) -> str:
    """Convert a string into a filesystem-safe directory name."""
    value = value.strip()
    value = re.sub(r"[^a-zA-Z0-9._-]+", "_", value)
    return value or "default"


class BrowserSession:
    """Owns a single persistent Playwright browser context.

    Notes
    -----
    - Always launches an automation-controlled persistent profile (cookies/session persist).
    - Uses a user-data-dir keyed by (browser_type, username) to keep sessions separated per account.
    - This object must be created and used on a single thread (the worker thread).
    """

    def __init__(self, browser_type: BrowserType, username: str, paths: AppPaths) -> None:
        """Initialize the browser session.

        Parameters
        ----------
        browser_type:
            Browser selected in the GUI.
        username:
            Username used to namespace the persistent profile folder.
        paths:
            App filesystem paths for persistence.
        """
        self._browser_type = browser_type
        self._username = username
        self._paths = paths

        self._playwright_cm = None
        self._playwright = None
        self._context: Optional[BrowserContext] = None

    def ensure_ready(self) -> None:
        """Ensure the persistent browser context exists."""
        if self._context is not None:
            return

        self._paths.data_dir.mkdir(parents=True, exist_ok=True)
        user_data_dir = (
            self._paths.data_dir
            / "browser_profiles"
            / self._browser_type.value
            / _safe_dirname(self._username)
        )
        user_data_dir.mkdir(parents=True, exist_ok=True)

        self._playwright_cm = sync_playwright()
        self._playwright = self._playwright_cm.start()

        if self._browser_type == BrowserType.FIREFOX:
            self._context = self._playwright.firefox.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=False,
            )
            return

        channel = "chrome" if self._browser_type == BrowserType.CHROME else "msedge"
        try:
            self._context = self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                channel=channel,
                headless=False,
            )
        except PlaywrightError:
            # Fallback to bundled Chromium.
            self._context = self._playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=False,
            )

    def close(self) -> None:
        """Close the context and stop Playwright."""
        try:
            if self._context is not None:
                self._context.close()
        finally:
            self._context = None
            if self._playwright_cm is not None:
                try:
                    self._playwright_cm.stop()
                except Exception:
                    pass
                self._playwright_cm = None
                self._playwright = None

    def get_or_create_app_page(self, base_url: str) -> Page:
        """Find an existing app tab on `base_url`, or create one.

        Parameters
        ----------
        base_url:
            The base URL to match for an existing tab.

        Returns
        -------
        Page
            Playwright Page instance.
        """
        assert self._context is not None, "Call ensure_ready() first."

        for p in self._context.pages:
            if p.url.startswith(base_url):
                try:
                    p.bring_to_front()
                except Exception:
                    pass
                return p

        page = self._context.new_page()
        page.goto(base_url, wait_until="domcontentloaded")
        return page
