# Admin Panel Automation (Windows)

This project builds a Windows desktop app (Tkinter) that:
- Authenticates to the web app via Playwright (persistent browser profile)
- Parses Chivalry 2 player list (listplayers -> clipboard -> web submit)
- Executes admin actions from clipboard in the Chivalry 2 console

## Build the installer on GitHub Actions
1. Push this folder to a GitHub repository.
2. Run the "Build Windows installer" workflow.
3. Download the `AdminPanelAutomationInstaller.exe` artifact.

## Local Windows build
- Install Python 3.11+
- Run `tools/build_windows.ps1`
