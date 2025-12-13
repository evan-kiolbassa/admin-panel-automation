"""Package entrypoint."""

from __future__ import annotations

from admin_panel_automation.gui.main_window import AdminPanelGUI


def main() -> None:
    """Start the Tkinter application."""
    app = AdminPanelGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
