"""GUI: логика приложения — сигналы, действия, диалоги."""
from python_library.codegen import uispec as u
from python_library.nodes._base import flag, library, lst, num, txt

nd = library("Signal", "13. GUI: Логика", color="#8f5a2f")

SIGNALS = ["clicked", "toggled", "textChanged", "valueChanged",
           "currentIndexChanged", "currentTextChanged", "returnPressed",
           "itemSelectionChanged", "stateChanged", "editingFinished"]


def _name_of(widget, fallback="widget"):
    if isinstance(widget, dict):
        return widget.get("name") or fallback
    return u.ident(widget, fallback)


@nd("Связь: сигнал → действия",
    inputs=[("widget", "widget", None),
            {"name": "signal", "type": "text", "default": "clicked",
             "choices": SIGNALS},
            ("actions", "actions", None)],
    outputs=[("binding", "binding")], tags=["signal", "connect", "событие"])
def on_signal(widget, signal, actions):
    """Подключает сигнал виджета к списку действий."""
    acts = [a for a in lst(actions) if isinstance(a, dict)]
    return u.binding(widget if isinstance(widget, dict) else txt(widget),
                     txt(signal) or "clicked", acts)


@nd("Действие: показать сообщение",
    inputs=[("title", "text", "Сообщение"), ("text", "text", "Готово!"),
            {"name": "kind", "type": "text", "default": "information",
             "choices": ["information", "warning", "critical", "question"]}],
    outputs=[("action", "action")], tags=["messagebox", "диалог"])
def act_message(title, text, kind):
    """Показывает всплывающее окно с сообщением."""
    fn = txt(kind) or "information"
    if fn not in ("information", "warning", "critical", "question"):
        fn = "information"
    return u.action(
        f"QtWidgets.QMessageBox.{fn}(self, {txt(title)!r}, {txt(text)!r})",
        label="сообщение")


@nd("Действие: задать текст виджета",
    inputs=[("target", "widget", None), ("text", "text", "Новый текст")],
    outputs=[("action", "action")], tags=["settext"])
def act_set_text(target, text):
    """Устанавливает текст у указанного виджета."""
    name = _name_of(target)
    return u.action(f"self.{name}.setText({txt(text)!r})", label="текст")


@nd("Действие: скопировать текст между виджетами",
    inputs=[("source", "widget", None), ("target", "widget", None),
            ("prefix", "text", "")],
    outputs=[("action", "action")], tags=["copy"])
def act_copy_text(source, target, prefix):
    """Берёт текст из одного виджета и кладёт в другой."""
    src, dst = _name_of(source, "source"), _name_of(target, "target")
    code = (f"value = get_text(self.{src})\n"
            f"self.{dst}.setText({txt(prefix)!r} + value)")
    return u.action(code, label="копирование текста")


@nd("Действие: очистить виджет", inputs=[("target", "widget", None)],
    outputs=[("action", "action")], tags=["clear"])
def act_clear(target):
    """Очищает содержимое виджета."""
    return u.action(f"self.{_name_of(target)}.clear()", label="очистка")


@nd("Действие: добавить строку в журнал",
    inputs=[("target", "widget", None), ("text", "text", "Событие"),
            ("with_time", "bool", True)],
    outputs=[("action", "action")], tags=["append", "log"])
def act_append(target, text, with_time):
    """Добавляет строку в текстовое поле."""
    name = _name_of(target, "editor")
    if flag(with_time, True):
        code = ("stamp = datetime.datetime.now().strftime('%H:%M:%S')\n"
                f"self.{name}.append(f'[{{stamp}}] ' + {txt(text)!r})")
        return u.action(code, imports=["import datetime"], label="журнал")
    return u.action(f"self.{name}.append({txt(text)!r})", label="журнал")


@nd("Действие: статус-строка", inputs=[("text", "text", "Готово"),
                                  ("timeout", "number", 3000)],
    outputs=[("action", "action")], tags=["statusbar"])
def act_status(text, timeout):
    """Пишет сообщение в статус-строку окна."""
    return u.action(
        f"self.statusBar().showMessage({txt(text)!r}, {int(num(timeout, 3000))})",
        label="статус")


@nd("Действие: открыть файл",
    inputs=[("target", "widget", None), ("filter", "text", "Все файлы (*.*)")],
    outputs=[("action", "action")], tags=["file", "dialog"])
def act_open_file(target, filter):
    """Открывает диалог выбора файла и выводит содержимое."""
    name = _name_of(target, "editor")
    code = ("path, _ = QtWidgets.QFileDialog.getOpenFileName("
            f"self, 'Открыть файл', '', {txt(filter)!r})\n"
            "if path:\n"
            "    with open(path, 'r', encoding='utf-8', errors='replace') as fh:\n"
            f"        set_text(self.{name}, fh.read())")
    return u.action(code, label="открытие файла")


@nd("Действие: сохранить файл",
    inputs=[("source", "widget", None), ("filter", "text", "Текст (*.txt)")],
    outputs=[("action", "action")], tags=["file", "dialog"])
def act_save_file(source, filter):
    """Сохраняет текст виджета в файл."""
    name = _name_of(source, "editor")
    code = ("path, _ = QtWidgets.QFileDialog.getSaveFileName("
            f"self, 'Сохранить файл', '', {txt(filter)!r})\n"
            "if path:\n"
            "    with open(path, 'w', encoding='utf-8') as fh:\n"
            f"        fh.write(get_text(self.{name}))")
    return u.action(code, label="сохранение файла")


@nd("Действие: вычислить выражение",
    inputs=[("source", "widget", None), ("target", "widget", None),
            ("prefix", "text", "= ")],
    outputs=[("action", "action")], tags=["calc"])
def act_calc(source, target, prefix):
    """Берёт выражение из поля и считает результат."""
    src, dst = _name_of(source, "input"), _name_of(target, "result")
    code = (f"expression = get_text(self.{src})\n"
            "try:\n"
            "    value = safe_eval(expression)\n"
            f"    self.{dst}.setText({txt(prefix)!r} + str(value))\n"
            "except Exception as exc:\n"
            f"    self.{dst}.setText('Ошибка: ' + str(exc))")
    return u.action(code, label="вычисление")


@nd("Действие: включить/выключить виджет",
    inputs=[("target", "widget", None), ("enabled", "bool", True)],
    outputs=[("action", "action")], tags=["enable"])
def act_enable(target, enabled):
    """Делает виджет активным или неактивным."""
    return u.action(f"self.{_name_of(target)}.setEnabled({bool(flag(enabled))})",
                    label="доступность")


@nd("Действие: показать/скрыть виджет",
    inputs=[("target", "widget", None), ("visible", "bool", True)],
    outputs=[("action", "action")], tags=["visible"])
def act_visible(target, visible):
    """Показывает или скрывает виджет."""
    return u.action(f"self.{_name_of(target)}.setVisible({bool(flag(visible))})",
                    label="видимость")


@nd("Действие: закрыть окно", inputs=[],
    outputs=[("action", "action")], tags=["close", "exit"])
def act_close():
    """Закрывает окно приложения."""
    return u.action("self.close()", label="закрыть")


@nd("Действие: таймер",
    inputs=[("target", "widget", None), ("interval", "number", 1000)],
    outputs=[("action", "action")], tags=["timer"])
def act_timer(target, interval):
    """Запускает таймер, который обновляет виджет временем."""
    name = _name_of(target, "label")
    code = ("if getattr(self, '_timer', None) is None:\n"
            "    self._timer = QtCore.QTimer(self)\n"
            f"    self._timer.setInterval({int(num(interval, 1000))})\n"
            "    self._timer.timeout.connect(\n"
            f"        lambda: self.{name}.setText(\n"
            "            datetime.datetime.now().strftime('%H:%M:%S')))\n"
            "self._timer.start()")
    return u.action(code, imports=["import datetime"], label="таймер")


@nd("Действие: произвольный код",
    inputs=[{"name": "code", "type": "code",
             "default": "print('Привет из слота')", "multiline": True,
             "hint": "Код вставляется в тело метода, доступен self"},
            {"name": "imports", "type": "text", "default": "", "multiline": True,
             "hint": "Дополнительные import-строки"}],
    outputs=[("action", "action")], tags=["code", "custom"])
def act_code(code, imports):
    """Произвольный Python-код в обработчике события."""
    lines = [i.strip() for i in txt(imports).splitlines() if i.strip()]
    return u.action(txt(code) or "pass", imports=lines, label="код")


@nd("Собрать действия",
    inputs=[("a", "action", None), ("b", "action", None), ("c", "action", None),
            ("d", "action", None), ("e", "action", None)],
    outputs=[("actions", "actions")], tags=["pack"])
def collect_actions(a, b, c, d, e):
    """Собирает несколько действий в один список (выполняются по порядку)."""
    out = []
    for v in (a, b, c, d, e):
        if isinstance(v, dict):
            out.append(v)
        elif isinstance(v, (list, tuple)):
            out.extend(x for x in v if isinstance(x, dict))
    return out


@nd("Собрать связи",
    inputs=[("a", "binding", None), ("b", "binding", None),
            ("c", "binding", None), ("d", "binding", None),
            ("e", "binding", None), ("f", "binding", None)],
    outputs=[("bindings", "events")], tags=["pack"])
def collect_bindings(a, b, c, d, e, f):
    """Собирает связи сигналов в список для окна."""
    out = []
    for v in (a, b, c, d, e, f):
        if isinstance(v, dict):
            out.append(v)
        elif isinstance(v, (list, tuple)):
            out.extend(x for x in v if isinstance(x, dict))
    return out