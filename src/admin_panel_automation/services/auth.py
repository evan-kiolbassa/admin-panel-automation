"""Authentication automation for the web application."""

from __future__ import annotations

import re
from typing import Optional

from playwright.sync_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

from admin_panel_automation.browser.session import BrowserSession
from admin_panel_automation.config import SELECTORS, WEB_APP_CONFIG
from admin_panel_automation.models import AuthResult


class AuthService:
    """Implements the login check + login flow against the target web app."""

    _SUCCESS_TEXT = "You have been logged in."
    _FAIL_TEXT = "Please check your login credentials and try again."

    def __init__(self, session: BrowserSession) -> None:
        """Create the service.

        Parameters
        ----------
        session:
            Persistent browser session used to drive the app.
        """
        self._session = session

    def authenticate(self, username: str, password: str) -> AuthResult:
        """Authenticate the persistent browser session as `username`.

        Parameters
        ----------
        username:
            Username used for login and profile verification.
        password:
            Password used for login.

        Returns
        -------
        AuthResult
            Outcome of the authentication attempt.
        """
        self._session.ensure_ready()
        page = self._session.get_or_create_app_page(WEB_APP_CONFIG.base_url)

        detected = self._try_get_profile(page)
        if detected is not None and detected.casefold() == username.casefold():
            return AuthResult(True, "Already authenticated in this browser session.", detected)

        page.goto(WEB_APP_CONFIG.login_url, wait_until="domcontentloaded")
        page.locator(SELECTORS.login_username).fill(username)
        page.locator(SELECTORS.login_password).fill(password)
        page.locator(SELECTORS.login_submit).click()

        modal_text = self._wait_for_modal_and_close(page)

        if self._SUCCESS_TEXT in modal_text:
            page.goto(WEB_APP_CONFIG.base_url, wait_until="domcontentloaded")
            detected_after = self._try_get_profile(page)
            if detected_after is None:
                return AuthResult(False, "Login succeeded, but profile element was not found.", None)
            if detected_after.casefold() != username.casefold():
                return AuthResult(
                    False,
                    "Logged in, but detected profile does not match the requested username.",
                    detected_after,
                )
            return AuthResult(True, "Authenticated successfully.", detected_after)

        if self._FAIL_TEXT in modal_text:
            return AuthResult(False, "Authentication failed. Verify username/password.", None)

        return AuthResult(False, f"Unexpected response after login: {modal_text!r}", None)

    @staticmethod
    def _extract_profile(text: str) -> Optional[str]:
        """Extract profile from text like `Profile (ARTISANAL)`."""
        m = re.search(r"\(([^)]+)\)", text)
        return m.group(1).strip() if m else None

    def _try_get_profile(self, page) -> Optional[str]:
        """Best-effort detection of logged-in profile via `a#profile`."""
        try:
            loc = page.locator(SELECTORS.profile_anchor)
            if loc.count() == 0:
                return None
            raw = loc.first.inner_text(timeout=1000)
            return self._extract_profile(raw) or raw.strip()
        except PlaywrightError:
            return None

    def _wait_for_modal_and_close(self, page) -> str:
        """Wait for the Bootstrap modal, read body text, click Close."""
        body = page.locator(SELECTORS.modal_body_visible)
        try:
            body.wait_for(state="visible", timeout=15000)
        except PlaywrightTimeoutError:
            return "No modal appeared after login."

        text = body.first.inner_text().strip()
        try:
            page.locator(SELECTORS.modal_close_visible).click(timeout=3000)
        except Exception:
            pass
        return text
