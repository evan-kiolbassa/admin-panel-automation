"""Background worker that runs automation tasks off the Tkinter UI thread."""

from __future__ import annotations

import queue
import threading
from concurrent.futures import Future
from typing import Callable, Dict, Tuple

from admin_panel_automation.browser.session import AppPaths, BrowserSession
from admin_panel_automation.models import BrowserType, AdminActionResult, AuthResult, ParseResult
from admin_panel_automation.services.admin_action import AdminActionService
from admin_panel_automation.services.auth import AuthService
from admin_panel_automation.services.player_list import PlayerListService
from admin_panel_automation.config import WEB_APP_CONFIG


class AutomationWorker(threading.Thread):
    """Single-threaded worker to keep Playwright off the Tk GUI thread."""

    def __init__(self, paths: AppPaths) -> None:
        """Create the worker.

        Parameters
        ----------
        paths:
            App paths used for persistent browser profiles.
        """
        super().__init__(daemon=True)
        self._paths = paths
        self._tasks: "queue.Queue[tuple[Callable[[], object], Future]]" = queue.Queue()
        self._stop = threading.Event()
        self._sessions: Dict[Tuple[BrowserType, str], BrowserSession] = {}

    def run(self) -> None:
        """Execute submitted tasks sequentially."""
        while not self._stop.is_set():
            try:
                fn, fut = self._tasks.get(timeout=0.2)
            except queue.Empty:
                continue

            if fut.set_running_or_notify_cancel():
                try:
                    fut.set_result(fn())
                except Exception as e:
                    fut.set_exception(e)

    def shutdown(self) -> None:
        """Stop the worker and close all sessions."""
        self._stop.set()
        for session in self._sessions.values():
            try:
                session.close()
            except Exception:
                pass

    def submit_auth(self, browser_type: BrowserType, username: str, password: str) -> Future:
        """Submit an authentication task.

        Returns
        -------
        Future
            Resolves to AuthResult.
        """

        def _task() -> AuthResult:
            key = (browser_type, username.casefold())
            session = self._sessions.get(key)
            if session is None:
                session = BrowserSession(browser_type=browser_type, username=username, paths=self._paths)
                self._sessions[key] = session
            return AuthService(session).authenticate(username=username, password=password)

        fut: Future = Future()
        self._tasks.put((_task, fut))
        return fut

    def submit_parse_player_list(self, browser_type: BrowserType, username: str) -> Future:
        """Submit a Parse Player List task.

        Returns
        -------
        Future
            Resolves to ParseResult.
        """

        def _task() -> ParseResult:
            key = (browser_type, username.casefold())
            session = self._sessions.get(key)
            if session is None:
                return ParseResult(False, "No active authenticated session found. Authenticate first.", 0)

            return PlayerListService(session).parse_and_submit()

        fut: Future = Future()
        self._tasks.put((_task, fut))
        return fut

    def submit_execute_admin_action(self, browser_type: BrowserType, username: str) -> Future:
        """Submit an Execute Admin Action task.

        Returns
        -------
        Future
            Resolves to AdminActionResult.
        """

        def _task() -> AdminActionResult:
            key = (browser_type, username.casefold())
            session = self._sessions.get(key)
            if session is None:
                return AdminActionResult(False, "No active authenticated session found. Authenticate first.", None)

            return AdminActionService().execute_from_clipboard()

        fut: Future = Future()
        self._tasks.put((_task, fut))
        return fut
