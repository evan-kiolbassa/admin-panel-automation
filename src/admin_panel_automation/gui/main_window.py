"""Main Tkinter window for the Admin Panel Automation app."""

from __future__ import annotations

from concurrent.futures import Future
from typing import Optional

import tkinter as tk
from tkinter import messagebox, ttk

from admin_panel_automation.browser.session import AppPaths
from admin_panel_automation.models import AdminActionResult, AuthResult, BrowserType, ParseResult
from admin_panel_automation.worker import AutomationWorker


class AdminPanelGUI(tk.Tk):
    """Tkinter GUI containing browser selection, authentication, and action buttons."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Admin Panel Automation")
        self.geometry("900x480")
        self.resizable(False, False)

        self._paths = AppPaths.default()
        self._worker = AutomationWorker(paths=self._paths)
        self._worker.start()

        self._browser_var = tk.StringVar(value=BrowserType.CHROME.value)
        self._username_var = tk.StringVar()
        self._password_var = tk.StringVar()
        self._auth_status_var = tk.StringVar(value="Inactive")

        self._pending_future: Optional[Future] = None
        self._active_browser: Optional[BrowserType] = None
        self._active_username: Optional[str] = None

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        """Construct the GUI widgets."""
        pad = {"padx": 10, "pady": 6}

        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=16, pady=16)

        ttk.Label(root, text="Admin Panel Automation GUI", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", **pad
        )

        ttk.Label(root, text="Browser Type", font=("Segoe UI", 11, "bold")).grid(
            row=1, column=0, sticky="w", **pad
        )

        browsers = ttk.Frame(root)
        browsers.grid(row=2, column=0, columnspan=2, sticky="w", **pad)

        for i, b in enumerate((BrowserType.CHROME, BrowserType.EDGE, BrowserType.FIREFOX)):
            ttk.Radiobutton(
                browsers,
                text=b.name.title(),
                value=b.value,
                variable=self._browser_var,
            ).grid(row=0, column=i, padx=12, sticky="w")

        ttk.Label(root, text="Username").grid(row=3, column=0, sticky="e", **pad)
        ttk.Entry(root, textvariable=self._username_var, width=34).grid(row=3, column=1, sticky="w", **pad)

        ttk.Label(root, text="Password").grid(row=4, column=0, sticky="e", **pad)
        ttk.Entry(root, textvariable=self._password_var, width=34, show="•").grid(
            row=4, column=1, sticky="w", **pad
        )

        self._auth_btn = ttk.Button(root, text="Authenticate", command=self._on_authenticate_clicked)
        self._auth_btn.grid(row=5, column=1, sticky="w", **pad)

        status_box = ttk.LabelFrame(root, text="Auth Status")
        status_box.grid(row=2, column=2, rowspan=4, columnspan=2, sticky="nsew", padx=18, pady=6)

        ttk.Label(status_box, textvariable=self._auth_status_var, font=("Segoe UI", 14, "bold")).pack(
            anchor="w", padx=12, pady=10
        )
        ttk.Label(status_box, text="Active = logged in\nInactive = not logged in", justify="left").pack(
            anchor="w", padx=12, pady=6
        )

        ttk.Separator(root).grid(row=6, column=0, columnspan=4, sticky="ew", pady=14)

        self._parse_btn = ttk.Button(
            root,
            text="Parse Player List",
            command=self._on_parse_clicked,
            state="disabled",
        )
        self._parse_btn.grid(row=7, column=0, padx=18, pady=10)

        self._exec_btn = ttk.Button(
            root,
            text="Execute Admin Action",
            command=self._on_execute_clicked,
            state="disabled",
        )
        self._exec_btn.grid(row=7, column=2, padx=18, pady=10)

    def _set_auth_active(self, browser_type: BrowserType, username: str) -> None:
        """Mark authentication active and enable gated UI actions."""
        self._active_browser = browser_type
        self._active_username = username
        self._auth_status_var.set("Active")
        self._parse_btn.configure(state="normal")
        self._exec_btn.configure(state="normal")

    def _set_auth_inactive(self) -> None:
        """Mark authentication inactive and disable gated UI actions."""
        self._active_browser = None
        self._active_username = None
        self._auth_status_var.set("Inactive")
        self._parse_btn.configure(state="disabled")
        self._exec_btn.configure(state="disabled")

    def _lock_buttons_working(self) -> None:
        """Disable buttons while a worker task is running."""
        self._auth_btn.configure(state="disabled")
        self._parse_btn.configure(state="disabled")
        self._exec_btn.configure(state="disabled")

    def _unlock_buttons_post_task(self) -> None:
        """Re-enable buttons based on auth state after task."""
        self._auth_btn.configure(state="normal")
        if self._active_browser and self._active_username:
            self._parse_btn.configure(state="normal")
            self._exec_btn.configure(state="normal")

    def _on_authenticate_clicked(self) -> None:
        """Start authentication without blocking the GUI thread."""
        if self._pending_future is not None and not self._pending_future.done():
            return

        username = self._username_var.get().strip()
        password = self._password_var.get()

        if not username or not password:
            messagebox.showwarning("Missing fields", "Please provide both username and password.")
            return

        browser_type = BrowserType(self._browser_var.get())

        self._auth_status_var.set("Working…")
        self._lock_buttons_working()

        self._pending_future = self._worker.submit_auth(browser_type, username, password)
        self.after(150, lambda: self._poll_future(kind="auth", browser_type=browser_type, username=username))

    def _on_parse_clicked(self) -> None:
        """Run Parse Player List: game -> clipboard -> web submit."""
        if self._pending_future is not None and not self._pending_future.done():
            return
        if self._active_browser is None or self._active_username is None:
            messagebox.showwarning("Not authenticated", "Authenticate first.")
            return

        self._auth_status_var.set("Working…")
        self._lock_buttons_working()

        self._pending_future = self._worker.submit_parse_player_list(self._active_browser, self._active_username)
        self.after(
            150,
            lambda: self._poll_future(kind="parse", browser_type=self._active_browser, username=self._active_username),
        )

    def _on_execute_clicked(self) -> None:
        """Execute admin action: clipboard -> Chivalry 2 console."""
        if self._pending_future is not None and not self._pending_future.done():
            return
        if self._active_browser is None or self._active_username is None:
            messagebox.showwarning("Not authenticated", "Authenticate first.")
            return

        self._auth_status_var.set("Working…")
        self._lock_buttons_working()

        self._pending_future = self._worker.submit_execute_admin_action(self._active_browser, self._active_username)
        self.after(
            150,
            lambda: self._poll_future(kind="exec", browser_type=self._active_browser, username=self._active_username),
        )

    def _poll_future(self, kind: str, browser_type: BrowserType, username: str) -> None:
        """Poll worker future and update UI when complete."""
        fut = self._pending_future
        if fut is None:
            return
        if not fut.done():
            self.after(150, lambda: self._poll_future(kind=kind, browser_type=browser_type, username=username))
            return

        self._pending_future = None
        self._unlock_buttons_post_task()

        try:
            result = fut.result()
        except Exception as e:
            self._set_auth_inactive()
            messagebox.showerror("Automation error", str(e))
            return

        if kind == "auth":
            auth: AuthResult = result
            if auth.success:
                self._set_auth_active(browser_type, username)
                messagebox.showinfo("Authentication", f"{auth.message}\nProfile: {auth.detected_profile or 'Unknown'}")
                self._password_var.set("")
            else:
                self._set_auth_inactive()
                messagebox.showwarning("Authentication", auth.message)
            return

        if kind == "parse":
            parse: ParseResult = result
            if parse.success:
                self._auth_status_var.set("Active")
                messagebox.showinfo(
                    "Parse Player List",
                    f"{parse.message}\nClipboard chars: {parse.clipboard_chars}",
                )
            else:
                if "Not authenticated" in parse.message:
                    self._set_auth_inactive()
                else:
                    self._auth_status_var.set("Active")
                messagebox.showwarning("Parse Player List", parse.message)
            return

        if kind == "exec":
            exec_res: AdminActionResult = result
            if exec_res.success:
                self._auth_status_var.set("Active")
                messagebox.showinfo(
                    "Execute Admin Action",
                    f"{exec_res.message}\n\n{exec_res.executed_command}",
                )
            else:
                if "Not authenticated" in exec_res.message:
                    self._set_auth_inactive()
                else:
                    self._auth_status_var.set("Active")
                messagebox.showwarning("Execute Admin Action", exec_res.message)
            return

    def _on_close(self) -> None:
        """Shutdown worker and close."""
        try:
            self._worker.shutdown()
        finally:
            self.destroy()
