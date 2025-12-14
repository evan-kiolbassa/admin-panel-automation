"""Parse Player List workflow: Chivalry 2 -> clipboard -> web app submit."""

from __future__ import annotations

import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from admin_panel_automation.browser.session import BrowserSession
from admin_panel_automation.config import SELECTORS, WEB_APP_CONFIG
from admin_panel_automation.models import ParseResult
from admin_panel_automation.services.chivalry_console import ChivalryConsoleAutomation


class PlayerListService:
    """Captures Chivalry 2 `listplayers` output into clipboard, then submits it to the web app."""

    def __init__(self, session: BrowserSession) -> None:
        """Create the service.

        Parameters
        ----------
        session:
            Browser session used to drive the web app submission.
        """
        self._session = session

    def parse_and_submit(self) -> ParseResult:
        """Run listplayers in-game, read clipboard, and submit to the web app.

        Returns
        -------
        ParseResult
            Success/failure and clipboard size.
        """
        try:
            ChivalryConsoleAutomation.ensure_windows()
        except RuntimeError as e:
            return ParseResult(False, str(e), 0)

        try:
            clipboard_text = self._capture_listplayers_to_clipboard(timeout_s=10.0)
        except Exception as e:
            return ParseResult(False, str(e), 0)

        if not clipboard_text.strip():
            return ParseResult(False, "Clipboard was empty after running listplayers.", 0)

        try:
            self._submit_clipboard_to_web(clipboard_text)
        except Exception as e:
            return ParseResult(False, f"Failed submitting to web app: {e}", len(clipboard_text))

        return ParseResult(True, "Player list submitted successfully.", len(clipboard_text))

    @staticmethod
    def _capture_listplayers_to_clipboard(timeout_s: float) -> str:
        """Focus Chivalry 2, run listplayers, and wait for clipboard update.

        Parameters
        ----------
        timeout_s:
            Maximum time to wait for clipboard to change.

        Returns
        -------
        str
            Clipboard content after listplayers executes.

        Raises
        ------
        TimeoutError
            If clipboard does not update in time.
        """
        import pyperclip

        original_clip = ""
        try:
            original_clip = pyperclip.paste() or ""
        except Exception:
            original_clip = ""

        try:
            # Put the command into clipboard, then paste it in-game (Ctrl+V) and execute (Enter).
            ChivalryConsoleAutomation.paste_clipboard_and_execute("listplayers", restore_clipboard=False)

            deadline = time.time() + timeout_s
            while time.time() < deadline:
                cur = pyperclip.paste()
                # The game is expected to overwrite the clipboard with listplayers output.
                if cur and cur != "listplayers" and cur != original_clip:
                    return cur
                time.sleep(0.25)

            raise TimeoutError(
                "Timed out waiting for player list to populate the clipboard. "
                "This usually means the console command did not execute."
            )
        finally:
            # Don't leave listplayers in the clipboard if capture fails.
            try:
                cur = pyperclip.paste() or ""
                if cur == "listplayers":
                    pyperclip.copy(original_clip)
            except Exception:
                pass

    def _submit_clipboard_to_web(self, clipboard_text: str) -> None:
        """Fill textarea#listplayerdata and click Submit."""
        self._session.ensure_ready()
        page = self._session.get_or_create_app_page(WEB_APP_CONFIG.base_url)

        page.goto(WEB_APP_CONFIG.base_url, wait_until="domcontentloaded")

        textarea = page.locator(SELECTORS.listplayers_textarea)
        textarea.wait_for(state="visible", timeout=15000)
        textarea.fill(clipboard_text)

        page.locator(SELECTORS.listplayers_submit).click()

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            pass
