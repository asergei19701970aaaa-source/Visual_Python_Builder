"""Экспорт: сборка готового PyQt6-проекта из описания окна."""
import os

from python_library.codegen import project_writer, pyqt_generator, uispec
from python_library.nodes._base import flag, library, num, txt

nd = library("Export", "10. Экспорт", color="#7a6a2f")


@nd("Код окна (предпросмотр)", inputs=[("window", "window", None)],
    outputs=[("code", "code"), ("warnings", "text")],
    tags=["code", "preview", "код"])
def preview_code(window):
    """Генерирует исходный код ui_main.py без записи на диск."""
    if not isinstance(window, dict) or window.get("kind") != "window":
        raise ValueError("Нужно подключить ноду 'Окно приложения'")
    result = pyqt_generator.generate_window_module(window)
    return result["code"], "\n".join(result["warnings"])


@nd("Описание интерфейса", inputs=[("window", "window", None)],
    outputs=[("text", "text")], tags=["describe"])
def describe_window(window):
    """Краткое текстовое дерево интерфейса."""
    return uispec.describe(window)


@nd("Собрать приложение (файлы)",
    inputs=[("window", "window", None),
            {"name": "folder", "type": "text", "default": "./export/MyApp",
             "hint": "Куда сохранить готовый проект"},
            ("app_name", "text", ""), ("write", "bool", True),
            ("with_build_scripts", "bool", True)],
    outputs=[("folder", "file"), ("files", "list"), ("report", "text")],
    tags=["export", "build", "pyinstaller", "exe"])
def build_app(window, folder, app_name, write, with_build_scripts):
    """Собирает готовый проект PyQt6 и записывает его в папку."""
    if not isinstance(window, dict) or window.get("kind") != "window":
        raise ValueError("Нужно подключить ноду 'Окно приложения'")
    spec = dict(window)
    if txt(app_name):
        spec["app_name"] = txt(app_name)
    bundle = project_writer.build_project(
        spec, with_build_scripts=flag(with_build_scripts, True))
    target = os.path.abspath(os.path.expanduser(txt(folder) or "./export/MyApp"))
    if flag(write, True):
        project_writer.write_project(target, bundle)
        status = f"Файлы записаны в {target}"
    else:
        status = "Запись отключена (включите флажок write)"
    names = sorted(bundle["files"].keys())
    report = [status, f"Файлов: {len(names)}"]
    report += [f"  • {n}" for n in names]
    if bundle["warnings"]:
        report.append("Предупреждения:")
        report += [f"  ! {w}" for w in bundle["warnings"]]
    report.append("Запуск: python main.py")
    report.append("Сборка .exe: build_exe.bat (Windows) или build_exe.sh")
    return target, names, "\n".join(report)


@nd("Сохранить текст в файл",
    inputs=[("text", "text", ""), ("path", "text", "./export/output.txt"),
            ("append", "bool", False)],
    outputs=[("path", "file"), ("size", "number")], tags=["save", "file"])
def save_text(text, path, append):
    """Записывает любой текст (например, сгенерированный код) в файл."""
    target = os.path.abspath(os.path.expanduser(txt(path) or "./export/output.txt"))
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    with open(target, "a" if flag(append) else "w", encoding="utf-8") as fh:
        fh.write(txt(text))
    return target, float(os.path.getsize(target))


@nd("Скрипт сборки .exe",
    inputs=[("app_name", "text", "MyApp"), ("one_file", "bool", True),
            ("windowed", "bool", True), ("icon", "text", "")],
    outputs=[("text", "text")], tags=["pyinstaller", "exe"])
def pyinstaller_command(app_name, one_file, windowed, icon):
    """Готовая команда PyInstaller для сборки .exe."""
    parts = ["pyinstaller"]
    if flag(one_file, True):
        parts.append("--onefile")
    if flag(windowed, True):
        parts.append("--windowed")
    if txt(icon):
        parts.append(f'--icon "{txt(icon)}"')
    parts.append(f'--name "{txt(app_name) or "MyApp"}"')
    parts.append("main.py")
    return " ".join(parts)


@nd("Папка экспорта", inputs=[("path", "text", "./export")],
    outputs=[("path", "file"), ("exists", "bool")], tags=["folder"])
def export_folder(path):
    """Проверяет и создаёт папку для экспорта."""
    target = os.path.abspath(os.path.expanduser(txt(path) or "./export"))
    existed = os.path.isdir(target)
    os.makedirs(target, exist_ok=True)
    return target, existed