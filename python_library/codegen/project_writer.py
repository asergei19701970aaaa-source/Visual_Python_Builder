"""Сборка папки готового PyQt6-проекта из описания окна."""
import os

from python_library.codegen import pyqt_generator

BUILD_BAT = """@echo off
rem Сборка исполняемого файла Windows (.exe)
chcp 65001 >nul
pyinstaller --noconfirm --onefile --windowed --name "{app}" main.py
echo.
echo Готово! Смотрите папку dist\\
pause
"""

BUILD_SH = """#!/usr/bin/env bash
# Сборка исполняемого файла (Linux / macOS)
set -e
pyinstaller --noconfirm --onefile --windowed --name "{app}" main.py
echo "Готово! Смотрите папку dist/"
"""

SPEC_FILE = """# -*- mode: python ; coding: utf-8 -*-
# Файл сборки PyInstaller. Запуск: pyinstaller app.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('style.qss', '.')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='{app}',
    debug=False,
    strip=False,
    upx=True,
    console=False,
)
"""


def _readme(app_name, warnings, files):
    lines = [
        f"# {app_name}",
        "",
        "Проект собран автоматически в **NodeFlow Studio 18.0**.",
        "",
        "## Запуск",
        "",
        "```bash",
        "python main.py",
        "```",
        "",
        "## Сборка .exe",
        "",
        "Windows: запустите `build_exe.bat`", "",
        "Linux/macOS: `bash build_exe.sh`", "",
        "Или вручную:",
        "",
        "```bash",
        f'pyinstaller --onefile --windowed --name "{app_name}" main.py',
        "```",
        "",
        "Готовый файл появится в папке `dist/`.",
        "",
        "## Состав проекта",
        "",
    ]
    lines += [f"- `{name}`" for name in sorted(files)]
    lines += [
        "",
        "- `ui_main.py` — интерфейс и обработчики событий (можно править вручную)",
        "- `main.py` — точка входа",
        "- `style.qss` — таблица стилей приложения",
        "",
    ]
    if warnings:
        lines.append("## Предупреждения сборки")
        lines.append("")
        lines += [f"- {w}" for w in warnings]
        lines.append("")
    return "\n".join(lines)


def build_project(spec, with_build_scripts=True):
    """Готовит словарь {имя файла: содержимое} без записи на диск."""
    result = pyqt_generator.generate_window_module(spec)
    app_name = str(spec.get("app_name") or spec.get("title") or "MyApp").strip()
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_"
                        for ch in app_name) or "MyApp"
    files = {
        "ui_main.py": result["code"],
        "main.py": pyqt_generator.generate_main_module(spec),
        "style.qss": str(spec.get("stylesheet") or "") + "\n",
    }
    if with_build_scripts:
        files["build_exe.bat"] = BUILD_BAT.format(app=safe_name)
        files["build_exe.sh"] = BUILD_SH.format(app=safe_name)
        files["app.spec"] = SPEC_FILE.format(app=safe_name)
    files["README.md"] = _readme(app_name, result["warnings"], files.keys())
    return {"files": files, "warnings": result["warnings"], "app_name": safe_name}


def write_project(folder, bundle):
    """Записывает собранные файлы в указанную папку."""
    os.makedirs(folder, exist_ok=True)
    written = []
    for name, content in bundle["files"].items():
        path = os.path.join(folder, name)
        os.makedirs(os.path.dirname(path) or folder, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        if name.endswith(".sh"):
            try:
                os.chmod(path, 0o755)
            except OSError:
                pass
        written.append(path)
    return written


def export_window(spec, folder, with_build_scripts=True):
    """Собирает и сразу записывает проект."""
    bundle = build_project(spec, with_build_scripts=with_build_scripts)
    bundle["written"] = write_project(folder, bundle)
    return bundle