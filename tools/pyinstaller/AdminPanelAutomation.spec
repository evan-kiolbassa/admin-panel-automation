# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for AdminPanelAutomation.

Notes
-----
- Uses one-folder build (onedir) because Playwright + browsers are large.
- Expects PLAYWRIGHT_BROWSERS_PATH=0 during `playwright install` so browsers are under the playwright package.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules
from pathlib import Path

spec_dir = Path(globals().get("SPECPATH", Path.cwd())).resolve()

def _find_project_root(start_dir: Path) -> Path:
    for parent in [start_dir, *start_dir.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
        if (parent / "src" / "admin_panel_automation" / "main.py").is_file():
            return parent
    return start_dir


project_root = _find_project_root(spec_dir)
src_root = project_root / "src"
entry_script = src_root / "admin_panel_automation" / "main.py"

# Collect Playwright (driver + data + browsers under .local-browsers when PLAYWRIGHT_BROWSERS_PATH=0)
pw_datas, pw_binaries, pw_hidden = collect_all("playwright")

# pywinauto has optional imports; collect submodules for safety
hiddenimports = pw_hidden + collect_submodules("pywinauto")

a = Analysis(
    [str(entry_script)],
    pathex=[str(project_root), str(src_root)],
    binaries=pw_binaries,
    datas=pw_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AdminPanelAutomation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AdminPanelAutomation",
)
