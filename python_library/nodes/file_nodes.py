"""Файлы и пути."""
import os

from python_library.nodes._base import flag, library, lst, txt

nd = library("File", "7. Файлы", color="#6a5a3a")


@nd("Путь к файлу",
    inputs=[{"name": "path", "type": "file", "default": "",
             "hint": "Абсолютный или относительный путь"}],
    outputs=[("path", "file"), ("exists", "bool")], tags=["path", "файл"])
def file_path(path):
    """Константа-путь и проверка существования."""
    p = txt(path)
    return p, bool(p) and os.path.exists(p)


@nd("Собрать путь",
    inputs=[("folder", "text", ""), ("name", "text", "file.txt")],
    outputs=[("path", "file")], tags=["join", "path"])
def join_path(folder, name):
    """Склеивает папку и имя файла."""
    return os.path.join(txt(folder), txt(name))


@nd("Разобрать путь", inputs=[("path", "file", "")],
    outputs=[("folder", "text"), ("name", "text"), ("ext", "text")],
    tags=["split", "basename"])
def split_path(path):
    """Папка, имя и расширение."""
    p = txt(path)
    folder, name = os.path.split(p)
    stem, ext = os.path.splitext(name)
    return folder, stem, ext


@nd("Прочитать текстовый файл",
    inputs=[("path", "file", ""), ("encoding", "text", "utf-8")],
    outputs=[("text", "text"), ("lines", "list")],
    tags=["read", "чтение"])
def read_text(path, encoding):
    """Читает содержимое текстового файла."""
    p = txt(path)
    if not p:
        raise ValueError("Не задан путь")
    with open(p, "r", encoding=txt(encoding) or "utf-8") as fh:
        data = fh.read()
    return data, data.splitlines()


@nd("Записать текстовый файл",
    inputs=[("path", "file", ""), ("text", "text", ""),
            ("append", "bool", False), ("encoding", "text", "utf-8")],
    outputs=[("path", "file"), ("bytes", "number")],
    tags=["write", "запись", "save"])
def write_text(path, text, append, encoding):
    """Записывает текст в файл."""
    p = txt(path)
    if not p:
        raise ValueError("Не задан путь")
    folder = os.path.dirname(os.path.abspath(p))
    os.makedirs(folder, exist_ok=True)
    data = txt(text)
    with open(p, "a" if flag(append) else "w",
              encoding=txt(encoding) or "utf-8") as fh:
        fh.write(data)
    return p, float(len(data.encode("utf-8")))


@nd("Список файлов папки",
    inputs=[("folder", "text", "."), ("pattern", "text", "*")],
    outputs=[("files", "list"), ("count", "number")],
    tags=["glob", "папка"])
def list_dir(folder, pattern):
    """Список файлов по маске."""
    import glob
    base = txt(folder) or "."
    found = sorted(glob.glob(os.path.join(base, txt(pattern) or "*")))
    return found, float(len(found))


@nd("Информация о файле", inputs=[("path", "file", "")],
    outputs=[("size", "number"), ("is_dir", "bool"), ("modified", "text")],
    tags=["stat", "info"])
def file_info(path):
    """Размер, тип и дата изменения."""
    import datetime as dt
    p = txt(path)
    if not p or not os.path.exists(p):
        raise ValueError("Файл не найден")
    st = os.stat(p)
    stamp = dt.datetime.fromtimestamp(st.st_mtime).strftime("%d.%m.%Y %H:%M")
    return float(st.st_size), os.path.isdir(p), stamp


@nd("Создать папку", inputs=[("folder", "text", "")],
    outputs=[("folder", "text")], tags=["mkdir"])
def make_dir(folder):
    """Создаёт папку (вместе с родительскими)."""
    p = txt(folder)
    if not p:
        raise ValueError("Не задана папка")
    os.makedirs(p, exist_ok=True)
    return p


@nd("Записать строки",
    inputs=[("path", "file", ""), ("lines", "list", None)],
    outputs=[("path", "file")], tags=["write", "lines"])
def write_lines(path, lines):
    """Записывает список строк в файл."""
    return write_text.fn(path, "\n".join(txt(v) for v in lst(lines)),
                         False, "utf-8")[0]