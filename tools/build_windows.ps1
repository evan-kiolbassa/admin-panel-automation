
<#
.SYNOPSIS
    Builds the Windows executable with PyInstaller and compiles an installer.exe via Inno Setup.

.DESCRIPTION
    - Creates a virtual environment
    - Installs build dependencies
    - Installs Playwright browsers in a bundle-friendly location
    - Runs PyInstaller (onedir)
    - Compiles installer via Inno Setup (ISCC)

.NOTES
    Requires:
    - Python 3.11+
    - Inno Setup installed (ISCC on PATH)
#>

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements-build.txt

# Install browsers into the playwright package directory so they can be bundled
$env:PLAYWRIGHT_BROWSERS_PATH = "0"
python -m playwright install chromium firefox

# Build app
pyinstaller --noconfirm --clean tools\pyinstaller\AdminPanelAutomation.spec

# Compile installer (Inno Setup)
iscc installer\AdminPanelAutomation.iss

Write-Host "Done. Installer output is in installer\output"
