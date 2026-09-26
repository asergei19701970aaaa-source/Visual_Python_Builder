from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class PortSpec:
    name: str
    caption: str
    kind: str  # event_out, work_in, data_out, data_in
    required: bool = False
    description: str = ""
    data_type: str = "any"


@dataclass(frozen=True)
class PropertySpec:
    name: str
    caption: str
    kind: str
    default: Any
    minimum: int | None = None
    maximum: int | None = None
    options: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""


@dataclass(frozen=True)
class ComponentSpec:
    type_name: str
    caption: str
    category: str
    color: str
    ports: tuple[PortSpec, ...] = field(default_factory=tuple)
    properties: tuple[PropertySpec, ...] = field(default_factory=tuple)
    description: str = ""
    source: str = "native"
    implemented: bool = True
    visual: bool = False
    subgroup: str = ""
    hiasm_class: str = ""
    hiasm_inherit: str = ""
    hiasm_interfaces: str = ""
    hiasm_sub: str = ""
    hiasm_edit_class: str = ""
    support_status: str = "работает"


COMPONENTS: dict[str, ComponentSpec] = {
    "Start": ComponentSpec(
        "Start",
        "Старт",
        "Логика",
        "#E8F1EC",
        ports=(PortSpec("onStart", "Запуск", "event_out", required=True),),
    ),
    "Form": ComponentSpec(
        "Form",
        "Форма",
        "Интерфейс",
        "#E5F2FC",
        ports=(
            PortSpec("doShow", "Показать", "work_in"),
            PortSpec("doClose", "Закрыть", "work_in"),
            PortSpec("onCreate", "Создание", "event_out"),
            PortSpec("onClose", "Закрытие", "event_out"),
            PortSpec("Caption", "Заголовок", "data_in"),
        ),
        properties=(
            PropertySpec("title", "Заголовок", "str", "Моя программа"),
            PropertySpec("width", "Ширина", "int", 640, 320, 1920),
            PropertySpec("height", "Высота", "int", 420, 240, 1080),
            PropertySpec("enabled", "Доступна", "bool", True),
            PropertySpec("visible", "Видима", "bool", True),
            PropertySpec("resizable", "Изменяемый размер", "bool", True),
            PropertySpec("always_on_top", "Поверх остальных", "bool", False),
        ),
    ),
    "Button": ComponentSpec(
        "Button",
        "Кнопка",
        "Интерфейс",
        "#E5F2FC",
        ports=(
            PortSpec("doClick", "Нажать", "work_in"),
            PortSpec("doSetText", "Установить текст", "work_in"),
            PortSpec("doEnable", "Разрешить", "work_in"),
            PortSpec("onClick", "Нажатие", "event_out"),
            PortSpec("Text", "Текст", "data_in"),
            PortSpec("Caption", "Надпись", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "button"),
            PropertySpec("text", "Текст", "str", "Нажми меня"),
            PropertySpec("enabled", "Доступна", "bool", True),
            PropertySpec("visible", "Видима", "bool", True),
            PropertySpec("default", "Кнопка по умолчанию", "bool", False),
            PropertySpec("auto_repeat", "Автоповтор", "bool", False),
            PropertySpec("tooltip", "Подсказка", "str", ""),
            PropertySpec("x", "X", "int", 32, 0, 3000),
            PropertySpec("y", "Y", "int", 32, 0, 3000),
            PropertySpec("width", "Ширина", "int", 140, 40, 1000),
            PropertySpec("height", "Высота", "int", 36, 20, 500),
        ),
    ),
    "Label": ComponentSpec(
        "Label",
        "Надпись",
        "Интерфейс",
        "#E5F2FC",
        ports=(
            PortSpec("doSetText", "Установить текст", "work_in"),
            PortSpec("doClear", "Очистить", "work_in"),
            PortSpec("doShow", "Показать", "work_in"),
            PortSpec("doHide", "Скрыть", "work_in"),
            PortSpec("Text", "Текст", "data_in"),
            PortSpec("Caption", "Надпись", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "label"),
            PropertySpec("text", "Текст", "str", "Введите текст"),
            PropertySpec("enabled", "Доступна", "bool", True),
            PropertySpec("visible", "Видима", "bool", True),
            PropertySpec("word_wrap", "Перенос строк", "bool", False),
            PropertySpec("selectable", "Выделение текста", "bool", False),
            PropertySpec("tooltip", "Подсказка", "str", ""),
            PropertySpec("x", "X", "int", 32, 0, 3000),
            PropertySpec("y", "Y", "int", 88, 0, 3000),
            PropertySpec("width", "Ширина", "int", 260, 40, 1000),
            PropertySpec("height", "Высота", "int", 28, 20, 500),
        ),
    ),
    "LineEdit": ComponentSpec(
        "LineEdit",
        "Поле ввода",
        "Интерфейс",
        "#E5F2FC",
        ports=(
            PortSpec("doSetText", "Установить текст", "work_in"),
            PortSpec("doClear", "Очистить", "work_in"),
            PortSpec("doFocus", "Фокус", "work_in"),
            PortSpec("onChange", "Изменение", "event_out"),
            PortSpec("onReturn", "Enter", "event_out"),
            PortSpec("Value", "Новое значение", "data_in"),
            PortSpec("Text", "Текст", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "line_edit"),
            PropertySpec("text", "Текст", "str", ""),
            PropertySpec("placeholder", "Подсказка", "str", "Напишите что-нибудь"),
            PropertySpec("enabled", "Доступно", "bool", True),
            PropertySpec("visible", "Видимо", "bool", True),
            PropertySpec("read_only", "Только чтение", "bool", False),
            PropertySpec("password", "Режим пароля", "bool", False),
            PropertySpec("clear_button", "Кнопка очистки", "bool", False),
            PropertySpec("max_length", "Макс. длина", "int", 32767, 1, 1000000),
            PropertySpec("x", "X", "int", 32, 0, 3000),
            PropertySpec("y", "Y", "int", 132, 0, 3000),
            PropertySpec("width", "Ширина", "int", 260, 40, 1000),
            PropertySpec("height", "Высота", "int", 36, 20, 500),
        ),
    ),
    "TextEdit": ComponentSpec(
        "TextEdit",
        "Многострочный текст",
        "Интерфейс",
        "#E5F2FC",
        ports=(
            PortSpec("doSetText", "Установить текст", "work_in"),
            PortSpec("doAppend", "Добавить строку", "work_in"),
            PortSpec("doClear", "Очистить", "work_in"),
            PortSpec("onChange", "Изменение", "event_out"),
            PortSpec("Value", "Новое значение", "data_in"),
            PortSpec("Text", "Текст", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "text_edit"),
            PropertySpec("text", "Текст", "str", ""),
            PropertySpec("placeholder", "Подсказка", "str", "Введите текст"),
            PropertySpec("enabled", "Доступно", "bool", True),
            PropertySpec("visible", "Видимо", "bool", True),
            PropertySpec("read_only", "Только чтение", "bool", False),
            PropertySpec("accept_rich_text", "Форматированный текст", "bool", False),
            PropertySpec("x", "X", "int", 32, 0, 3000),
            PropertySpec("y", "Y", "int", 184, 0, 3000),
            PropertySpec("width", "Ширина", "int", 300, 40, 1000),
            PropertySpec("height", "Высота", "int", 100, 30, 1000),
        ),
    ),
    "CheckBox": ComponentSpec(
        "CheckBox",
        "Флажок",
        "Интерфейс",
        "#E5F2FC",
        ports=(
            PortSpec("doCheck", "Установить", "work_in"),
            PortSpec("doToggle", "Переключить", "work_in"),
            PortSpec("onChange", "Изменение", "event_out"),
            PortSpec("State", "Новое состояние", "data_in"),
            PortSpec("Checked", "Состояние", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "check_box"),
            PropertySpec("text", "Текст", "str", "Включено"),
            PropertySpec("checked", "Отмечен", "bool", False),
            PropertySpec("enabled", "Доступен", "bool", True),
            PropertySpec("visible", "Видим", "bool", True),
            PropertySpec("tristate", "Три состояния", "bool", False),
            PropertySpec("x", "X", "int", 32, 0, 3000),
            PropertySpec("y", "Y", "int", 300, 0, 3000),
            PropertySpec("width", "Ширина", "int", 160, 40, 1000),
            PropertySpec("height", "Высота", "int", 28, 20, 500),
        ),
    ),
    "ComboBox": ComponentSpec(
        "ComboBox",
        "Выпадающий список",
        "Интерфейс",
        "#E5F2FC",
        ports=(
            PortSpec("doSelect", "Выбрать", "work_in"),
            PortSpec("doAdd", "Добавить", "work_in"),
            PortSpec("doClear", "Очистить", "work_in"),
            PortSpec("onChange", "Изменение", "event_out"),
            PortSpec("Index", "Индекс", "data_in"),
            PortSpec("Item", "Элемент", "data_in"),
            PortSpec("Text", "Текст", "data_out"),
            PortSpec("CurrentIndex", "Текущий индекс", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "combo_box"),
            PropertySpec("items", "Элементы через |", "str", "Первый|Второй|Третий"),
            PropertySpec("current_index", "Текущий индекс", "int", 0, -1, 100000),
            PropertySpec("enabled", "Доступен", "bool", True),
            PropertySpec("visible", "Видим", "bool", True),
            PropertySpec("editable", "Разрешён ввод", "bool", False),
            PropertySpec("x", "X", "int", 32, 0, 3000),
            PropertySpec("y", "Y", "int", 340, 0, 3000),
            PropertySpec("width", "Ширина", "int", 200, 40, 1000),
            PropertySpec("height", "Высота", "int", 34, 20, 500),
        ),
    ),
    "Timer": ComponentSpec(
        "Timer",
        "Таймер",
        "Логика",
        "#FFF3CD",
        ports=(
            PortSpec("doStart", "Запустить", "work_in"),
            PortSpec("doStop", "Остановить", "work_in"),
            PortSpec("onTimer", "Срабатывание", "event_out"),
            PortSpec("Interval", "Интервал", "data_in"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "timer"),
            PropertySpec("interval", "Интервал, мс", "int", 1000, 1, 86400000),
            PropertySpec("active", "Запускать сразу", "bool", False),
            PropertySpec("single_shot", "Однократный", "bool", False),
        ),
    ),
    "Hub": ComponentSpec(
        "Hub",
        "Разветвитель",
        "Логика",
        "#E8F1EC",
        ports=(
            PortSpec("doEvent", "Вход", "work_in"),
            PortSpec("onEvent1", "Выход 1", "event_out"),
            PortSpec("onEvent2", "Выход 2", "event_out"),
            PortSpec("onEvent3", "Выход 3", "event_out"),
        ),
    ),
    "IfElse": ComponentSpec(
        "IfElse",
        "Условие",
        "Логика",
        "#E8F1EC",
        ports=(
            PortSpec("doCompare", "Сравнить", "work_in"),
            PortSpec("onTrue", "Да", "event_out"),
            PortSpec("onFalse", "Нет", "event_out"),
            PortSpec("Op1", "Операнд 1", "data_in"),
            PortSpec("Op2", "Операнд 2", "data_in"),
        ),
        properties=(
            PropertySpec(
                "operator",
                "Операция",
                "enum",
                "==",
                options=("==", "!=", ">", ">=", "<", "<="),
            ),
            PropertySpec("op1", "Операнд 1", "str", ""),
            PropertySpec("op2", "Операнд 2", "str", ""),
        ),
    ),
    "Memory": ComponentSpec(
        "Memory",
        "Память",
        "Данные",
        "#E8F1EC",
        ports=(
            PortSpec("doValue", "Записать", "work_in"),
            PortSpec("doClear", "Очистить", "work_in"),
            PortSpec("onData", "Изменение", "event_out"),
            PortSpec("Data", "Данные", "data_in"),
            PortSpec("Value", "Значение", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "memory"),
            PropertySpec("default", "Начальное значение", "str", ""),
        ),
    ),
    "Math": ComponentSpec(
        "Math",
        "Математика",
        "Данные",
        "#E8F1EC",
        ports=(
            PortSpec("doOperation", "Вычислить", "work_in"),
            PortSpec("onResult", "Результат", "event_out"),
            PortSpec("Op1", "Операнд 1", "data_in"),
            PortSpec("Op2", "Операнд 2", "data_in"),
            PortSpec("Result", "Результат", "data_out"),
        ),
        properties=(
            PropertySpec(
                "operator",
                "Операция",
                "enum",
                "+",
                options=("+", "-", "*", "/", "//", "%", "**"),
            ),
            PropertySpec("op1", "Операнд 1", "real", 0.0),
            PropertySpec("op2", "Операнд 2", "real", 0.0),
        ),
    ),
    "FormatStr": ComponentSpec(
        "FormatStr",
        "Формат строки",
        "Строки",
        "#E8F1EC",
        ports=(
            PortSpec("doFormat", "Сформировать", "work_in"),
            PortSpec("onResult", "Результат", "event_out"),
            PortSpec("Data1", "Данные 1", "data_in"),
            PortSpec("Data2", "Данные 2", "data_in"),
            PortSpec("Data3", "Данные 3", "data_in"),
            PortSpec("Result", "Строка", "data_out"),
        ),
        properties=(
            PropertySpec(
                "template",
                "Шаблон",
                "str",
                "Значение: {0}",
            ),
        ),
    ),
    "FileRead": ComponentSpec(
        "FileRead",
        "Чтение файла",
        "Файлы",
        "#E6F0FA",
        ports=(
            PortSpec("doRead", "Прочитать", "work_in"),
            PortSpec("onRead", "Прочитано", "event_out"),
            PortSpec("onError", "Ошибка", "event_out"),
            PortSpec("Path", "Путь", "data_in"),
            PortSpec("Text", "Текст", "data_out"),
            PortSpec("Error", "Ошибка", "data_out"),
        ),
        properties=(
            PropertySpec("path", "Имя файла", "str", ""),
            PropertySpec("encoding", "Кодировка", "str", "utf-8"),
        ),
    ),
    "FileWrite": ComponentSpec(
        "FileWrite",
        "Запись файла",
        "Файлы",
        "#E6F0FA",
        ports=(
            PortSpec("doWrite", "Записать", "work_in"),
            PortSpec("onWrite", "Записано", "event_out"),
            PortSpec("onError", "Ошибка", "event_out"),
            PortSpec("Path", "Путь", "data_in"),
            PortSpec("Text", "Текст", "data_in"),
            PortSpec("Error", "Ошибка", "data_out"),
        ),
        properties=(
            PropertySpec("path", "Имя файла", "str", ""),
            PropertySpec("text", "Текст", "str", ""),
            PropertySpec("encoding", "Кодировка", "str", "utf-8"),
            PropertySpec("append", "Добавлять в конец", "bool", False),
        ),
    ),
    "DebugPrint": ComponentSpec(
        "DebugPrint",
        "Вывод в консоль",
        "Отладка",
        "#F4E8FF",
        ports=(
            PortSpec("doPrint", "Вывести", "work_in"),
            PortSpec("onPrint", "Готово", "event_out"),
            PortSpec("Data", "Данные", "data_in"),
        ),
        properties=(
            PropertySpec("prefix", "Префикс", "str", ""),
        ),
    ),
    "ListWidget": ComponentSpec(
        "ListWidget",
        "Список",
        "Интерфейс",
        "#E5F2FC",
        ports=(
            PortSpec("doAdd", "Добавить", "work_in"),
            PortSpec("doClear", "Очистить", "work_in"),
            PortSpec("doSelect", "Выбрать", "work_in"),
            PortSpec("onSelect", "Выбор", "event_out"),
            PortSpec("Item", "Элемент", "data_in"),
            PortSpec("Index", "Индекс", "data_in"),
            PortSpec("Text", "Текст", "data_out"),
            PortSpec("CurrentIndex", "Текущий индекс", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "list_widget"),
            PropertySpec("items", "Элементы через |", "str", "Первый|Второй|Третий"),
            PropertySpec("current_index", "Текущий индекс", "int", 0, -1, 100000),
            PropertySpec("sorting", "Сортировка", "bool", False),
            PropertySpec("enabled", "Доступен", "bool", True),
            PropertySpec("visible", "Видим", "bool", True),
            PropertySpec("x", "X", "int", 32, 0, 3000),
            PropertySpec("y", "Y", "int", 390, 0, 3000),
            PropertySpec("width", "Ширина", "int", 220, 40, 1000),
            PropertySpec("height", "Высота", "int", 130, 30, 1000),
        ),
    ),
    "ProgressBar": ComponentSpec(
        "ProgressBar",
        "Индикатор",
        "Интерфейс",
        "#E5F2FC",
        ports=(
            PortSpec("doValue", "Установить", "work_in"),
            PortSpec("Value", "Значение", "data_in"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "progress"),
            PropertySpec("value", "Значение", "int", 0, -1000000, 1000000),
            PropertySpec("minimum", "Минимум", "int", 0, -1000000, 1000000),
            PropertySpec("maximum", "Максимум", "int", 100, -1000000, 1000000),
            PropertySpec("show_text", "Показывать текст", "bool", True),
            PropertySpec("x", "X", "int", 32, 0, 3000),
            PropertySpec("y", "Y", "int", 540, 0, 3000),
            PropertySpec("width", "Ширина", "int", 240, 40, 1000),
            PropertySpec("height", "Высота", "int", 26, 16, 300),
        ),
    ),
    "Slider": ComponentSpec(
        "Slider",
        "Ползунок",
        "Интерфейс",
        "#E5F2FC",
        ports=(
            PortSpec("doValue", "Установить", "work_in"),
            PortSpec("onChange", "Изменение", "event_out"),
            PortSpec("NewValue", "Новое значение", "data_in"),
            PortSpec("Value", "Значение", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "slider"),
            PropertySpec("value", "Значение", "int", 0, -1000000, 1000000),
            PropertySpec("minimum", "Минимум", "int", 0, -1000000, 1000000),
            PropertySpec("maximum", "Максимум", "int", 100, -1000000, 1000000),
            PropertySpec("step", "Шаг", "int", 1, 1, 1000000),
            PropertySpec("x", "X", "int", 32, 0, 3000),
            PropertySpec("y", "Y", "int", 580, 0, 3000),
            PropertySpec("width", "Ширина", "int", 240, 40, 1000),
            PropertySpec("height", "Высота", "int", 28, 16, 300),
        ),
    ),
    "SpinBox": ComponentSpec(
        "SpinBox",
        "Числовое поле",
        "Интерфейс",
        "#E5F2FC",
        ports=(
            PortSpec("doValue", "Установить", "work_in"),
            PortSpec("onChange", "Изменение", "event_out"),
            PortSpec("NewValue", "Новое значение", "data_in"),
            PortSpec("Value", "Значение", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "spin_box"),
            PropertySpec("value", "Значение", "int", 0, -1000000, 1000000),
            PropertySpec("minimum", "Минимум", "int", 0, -1000000, 1000000),
            PropertySpec("maximum", "Максимум", "int", 100, -1000000, 1000000),
            PropertySpec("step", "Шаг", "int", 1, 1, 1000000),
            PropertySpec("x", "X", "int", 300, 0, 3000),
            PropertySpec("y", "Y", "int", 580, 0, 3000),
            PropertySpec("width", "Ширина", "int", 100, 40, 1000),
            PropertySpec("height", "Высота", "int", 28, 16, 300),
        ),
    ),
    "OpenFileDialog": ComponentSpec(
        "OpenFileDialog",
        "Открыть файл",
        "Диалоги",
        "#FBEBDE",
        ports=(
            PortSpec("doOpen", "Открыть", "work_in"),
            PortSpec("onSelect", "Выбрано", "event_out"),
            PortSpec("onCancel", "Отмена", "event_out"),
            PortSpec("FileName", "Имя файла", "data_out"),
        ),
        properties=(
            PropertySpec("title", "Заголовок", "str", "Открыть файл"),
            PropertySpec("directory", "Начальная папка", "str", ""),
            PropertySpec("filter", "Фильтр", "str", "Все файлы (*.*)"),
        ),
    ),
    "SaveFileDialog": ComponentSpec(
        "SaveFileDialog",
        "Сохранить файл",
        "Диалоги",
        "#FBEBDE",
        ports=(
            PortSpec("doSave", "Сохранить", "work_in"),
            PortSpec("onSelect", "Выбрано", "event_out"),
            PortSpec("onCancel", "Отмена", "event_out"),
            PortSpec("FileName", "Имя файла", "data_out"),
        ),
        properties=(
            PropertySpec("title", "Заголовок", "str", "Сохранить файл"),
            PropertySpec("directory", "Начальная папка", "str", ""),
            PropertySpec("filter", "Фильтр", "str", "Все файлы (*.*)"),
        ),
    ),
    "Delay": ComponentSpec(
        "Delay",
        "Задержка",
        "Логика",
        "#FFF3CD",
        ports=(
            PortSpec("doStart", "Запустить", "work_in"),
            PortSpec("onDone", "Завершено", "event_out"),
            PortSpec("Interval", "Интервал", "data_in"),
        ),
        properties=(
            PropertySpec("interval", "Задержка, мс", "int", 1000, 0, 86400000),
        ),
    ),
    "Counter": ComponentSpec(
        "Counter",
        "Счётчик",
        "Данные",
        "#E8F1EC",
        ports=(
            PortSpec("doNext", "Следующее", "work_in"),
            PortSpec("doReset", "Сбросить", "work_in"),
            PortSpec("onValue", "Значение", "event_out"),
            PortSpec("Value", "Значение", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "counter"),
            PropertySpec("start", "Начало", "int", 0, -1000000, 1000000),
            PropertySpec("step", "Шаг", "int", 1, -1000000, 1000000),
        ),
    ),
    "Random": ComponentSpec(
        "Random",
        "Случайное число",
        "Данные",
        "#E8F1EC",
        ports=(
            PortSpec("doRandom", "Получить", "work_in"),
            PortSpec("onResult", "Результат", "event_out"),
            PortSpec("Minimum", "Минимум", "data_in"),
            PortSpec("Maximum", "Максимум", "data_in"),
            PortSpec("Result", "Результат", "data_out"),
        ),
        properties=(
            PropertySpec("minimum", "Минимум", "int", 0, -1000000, 1000000),
            PropertySpec("maximum", "Максимум", "int", 100, -1000000, 1000000),
        ),
    ),
    "HTTPGet": ComponentSpec(
        "HTTPGet",
        "HTTP-запрос",
        "Интернет",
        "#E6F0FA",
        ports=(
            PortSpec("doRequest", "Выполнить", "work_in"),
            PortSpec("onSuccess", "Успешно", "event_out"),
            PortSpec("onError", "Ошибка", "event_out"),
            PortSpec("URL", "Адрес", "data_in"),
            PortSpec("Text", "Ответ", "data_out"),
            PortSpec("Status", "Код", "data_out"),
            PortSpec("Error", "Ошибка", "data_out"),
        ),
        properties=(
            PropertySpec("url", "URL", "str", "https://example.com"),
            PropertySpec("timeout", "Тайм-аут, с", "int", 15, 1, 600),
            PropertySpec("encoding", "Кодировка", "str", "utf-8"),
        ),
    ),
    "RunProcess": ComponentSpec(
        "RunProcess",
        "Запуск процесса",
        "Система",
        "#E6F0FA",
        ports=(
            PortSpec("doRun", "Запустить", "work_in"),
            PortSpec("onDone", "Завершён", "event_out"),
            PortSpec("onError", "Ошибка", "event_out"),
            PortSpec("Program", "Программа", "data_in"),
            PortSpec("Arguments", "Аргументы", "data_in"),
            PortSpec("Output", "Вывод", "data_out"),
            PortSpec("ExitCode", "Код выхода", "data_out"),
            PortSpec("Error", "Ошибка", "data_out"),
        ),
        properties=(
            PropertySpec("program", "Программа", "str", ""),
            PropertySpec("arguments", "Аргументы", "str", ""),
            PropertySpec("timeout", "Тайм-аут, с", "int", 30, 1, 3600),
        ),
    ),
    "TableWidget": ComponentSpec(
        "TableWidget", "Таблица", "Интерфейс", "#E5F2FC",
        ports=(PortSpec("doSetCell", "Установить ячейку", "work_in"), PortSpec("doClear", "Очистить", "work_in"), PortSpec("onSelect", "Выбор", "event_out"), PortSpec("Row", "Строка", "data_in"), PortSpec("Column", "Столбец", "data_in"), PortSpec("Value", "Значение", "data_in"), PortSpec("CellText", "Текст ячейки", "data_out"), PortSpec("CurrentRow", "Текущая строка", "data_out"), PortSpec("CurrentColumn", "Текущий столбец", "data_out")),
        properties=(PropertySpec("name", "Имя", "str", "table"), PropertySpec("columns", "Заголовки через |", "str", "Колонка 1|Колонка 2"), PropertySpec("rows", "Число строк", "int", 5, 0, 10000), PropertySpec("editable", "Разрешить изменение", "bool", True), PropertySpec("enabled", "Доступна", "bool", True), PropertySpec("visible", "Видима", "bool", True), PropertySpec("x", "X", "int", 32, 0, 3000), PropertySpec("y", "Y", "int", 390, 0, 3000), PropertySpec("width", "Ширина", "int", 360, 80, 1600), PropertySpec("height", "Высота", "int", 180, 60, 1200)),
    ),
    "TreeWidget": ComponentSpec(
        "TreeWidget", "Дерево", "Интерфейс", "#E5F2FC",
        ports=(PortSpec("doAdd", "Добавить", "work_in"), PortSpec("doClear", "Очистить", "work_in"), PortSpec("onSelect", "Выбор", "event_out"), PortSpec("Item", "Элемент", "data_in"), PortSpec("Text", "Текст", "data_out")),
        properties=(PropertySpec("name", "Имя", "str", "tree"), PropertySpec("items", "Элементы через |", "str", "Первый|Второй|Третий"), PropertySpec("header", "Заголовок", "str", "Элементы"), PropertySpec("enabled", "Доступно", "bool", True), PropertySpec("visible", "Видимо", "bool", True), PropertySpec("x", "X", "int", 410, 0, 3000), PropertySpec("y", "Y", "int", 390, 0, 3000), PropertySpec("width", "Ширина", "int", 220, 80, 1600), PropertySpec("height", "Высота", "int", 180, 60, 1200)),
    ),
    "DateEdit": ComponentSpec(
        "DateEdit", "Дата", "Интерфейс", "#E5F2FC",
        ports=(PortSpec("doSetDate", "Установить дату", "work_in"), PortSpec("onChange", "Изменение", "event_out"), PortSpec("Date", "Дата", "data_in"), PortSpec("Text", "Дата", "data_out")),
        properties=(PropertySpec("name", "Имя", "str", "date_edit"), PropertySpec("date", "Дата YYYY-MM-DD", "str", "2026-01-01"), PropertySpec("format", "Формат", "str", "dd.MM.yyyy"), PropertySpec("calendar_popup", "Календарь", "bool", True), PropertySpec("enabled", "Доступно", "bool", True), PropertySpec("visible", "Видимо", "bool", True), PropertySpec("x", "X", "int", 32, 0, 3000), PropertySpec("y", "Y", "int", 590, 0, 3000), PropertySpec("width", "Ширина", "int", 140, 40, 1000), PropertySpec("height", "Высота", "int", 30, 20, 500)),
    ),
    "Calendar": ComponentSpec(
        "Calendar", "Календарь", "Интерфейс", "#E5F2FC",
        ports=(PortSpec("doSetDate", "Установить дату", "work_in"), PortSpec("onSelect", "Выбор", "event_out"), PortSpec("Date", "Дата", "data_in"), PortSpec("Text", "Дата", "data_out")),
        properties=(PropertySpec("name", "Имя", "str", "calendar"), PropertySpec("date", "Дата YYYY-MM-DD", "str", "2026-01-01"), PropertySpec("grid", "Сетка", "bool", True), PropertySpec("enabled", "Доступен", "bool", True), PropertySpec("visible", "Видим", "bool", True), PropertySpec("x", "X", "int", 190, 0, 3000), PropertySpec("y", "Y", "int", 590, 0, 3000), PropertySpec("width", "Ширина", "int", 300, 100, 1200), PropertySpec("height", "Высота", "int", 200, 100, 1000)),
    ),
    "LCDNumber": ComponentSpec(
        "LCDNumber", "Цифровой индикатор", "Интерфейс", "#E5F2FC",
        ports=(PortSpec("doValue", "Установить", "work_in"), PortSpec("Value", "Значение", "data_in")),
        properties=(PropertySpec("name", "Имя", "str", "lcd"), PropertySpec("value", "Значение", "real", 0.0, -1000000, 1000000), PropertySpec("digits", "Число цифр", "int", 5, 1, 20), PropertySpec("enabled", "Доступен", "bool", True), PropertySpec("visible", "Видим", "bool", True), PropertySpec("x", "X", "int", 510, 0, 3000), PropertySpec("y", "Y", "int", 590, 0, 3000), PropertySpec("width", "Ширина", "int", 120, 40, 1000), PropertySpec("height", "Высота", "int", 50, 25, 500)),
    ),
    "JSONParse": ComponentSpec(
        "JSONParse", "Разбор JSON", "Данные", "#E8F1EC",
        ports=(PortSpec("doParse", "Разобрать", "work_in"), PortSpec("onSuccess", "Успешно", "event_out"), PortSpec("onError", "Ошибка", "event_out"), PortSpec("Text", "JSON", "data_in"), PortSpec("Value", "Объект", "data_out"), PortSpec("Error", "Ошибка", "data_out")),
        properties=(PropertySpec("text", "JSON", "multiline", "{}"),),
    ),
    "JSONStringify": ComponentSpec(
        "JSONStringify", "Создание JSON", "Данные", "#E8F1EC",
        ports=(PortSpec("doEncode", "Преобразовать", "work_in"), PortSpec("onResult", "Результат", "event_out"), PortSpec("Data", "Объект", "data_in"), PortSpec("Text", "JSON", "data_out")),
        properties=(PropertySpec("indent", "Отступ", "int", 2, 0, 16), PropertySpec("ensure_ascii", "ASCII", "bool", False)),
    ),
    "SQLiteQuery": ComponentSpec(
        "SQLiteQuery", "SQLite-запрос", "Базы данных", "#F0E7FA",
        ports=(PortSpec("doQuery", "Выполнить", "work_in"), PortSpec("onSuccess", "Успешно", "event_out"), PortSpec("onError", "Ошибка", "event_out"), PortSpec("Database", "База данных", "data_in"), PortSpec("SQL", "SQL", "data_in"), PortSpec("Rows", "Строки", "data_out"), PortSpec("Error", "Ошибка", "data_out")),
        properties=(PropertySpec("database", "Файл базы", "str", "data.db"), PropertySpec("sql", "SQL", "multiline", "SELECT 1"), PropertySpec("commit", "Фиксировать изменения", "bool", True)),
    ),
    "Clipboard": ComponentSpec(
        "Clipboard", "Буфер обмена", "Система", "#E6F0FA",
        ports=(PortSpec("doSet", "Записать", "work_in"), PortSpec("doGet", "Прочитать", "work_in"), PortSpec("doClear", "Очистить", "work_in"), PortSpec("onText", "Текст получен", "event_out"), PortSpec("Text", "Текст", "data_in"), PortSpec("Value", "Значение", "data_out")),
        properties=(PropertySpec("text", "Текст", "str", ""),),
    ),
    "MessageBox": ComponentSpec(
        "MessageBox",
        "Сообщение",
        "Диалоги",
        "#FBEBDE",
        ports=(
            PortSpec("doShow", "Показать", "work_in"),
            PortSpec("onResult", "Результат", "event_out"),
            PortSpec("Text", "Текст", "data_in"),
            PortSpec("Title", "Заголовок", "data_in"),
            PortSpec("Result", "Кнопка", "data_out"),
        ),
        properties=(
            PropertySpec("title", "Заголовок", "str", "Сообщение"),
            PropertySpec("text", "Текст", "str", "Готово"),
        ),
    ),
}



# Additional native Qt controls for 6.0. They use the same four-side model.
COMPONENTS.update({
    "RadioButton": ComponentSpec("RadioButton", "Переключатель", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doCheck","Установить","work_in"),PortSpec("doToggle","Переключить","work_in"),PortSpec("onClick","Нажатие","event_out"),PortSpec("onToggle","Изменение","event_out"),PortSpec("State","Состояние","data_in"),PortSpec("Checked","Отмечен","data_out")),
        properties=(PropertySpec("name","Имя","str","radio_button"),PropertySpec("text","Текст","str","Переключатель"),PropertySpec("checked","Отмечен","bool",False),PropertySpec("x","X","int",32,0,3000),PropertySpec("y","Y","int",250,0,3000),PropertySpec("width","Ширина","int",180,40,1000),PropertySpec("height","Высота","int",32,20,500))),
    "GroupBox": ComponentSpec("GroupBox", "Группа", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doSetTitle","Установить заголовок","work_in"),PortSpec("doCheck","Установить флаг","work_in"),PortSpec("onToggle","Изменение","event_out"),PortSpec("Title","Заголовок","data_in"),PortSpec("State","Состояние","data_in"),PortSpec("Checked","Отмечена","data_out")),
        properties=(PropertySpec("name","Имя","str","group_box"),PropertySpec("title","Заголовок","str","Группа"),PropertySpec("checkable","Переключаемая","bool",False),PropertySpec("checked","Отмечена","bool",True),PropertySpec("x","X","int",30,0,3000),PropertySpec("y","Y","int",300,0,3000),PropertySpec("width","Ширина","int",320,80,1600),PropertySpec("height","Высота","int",180,60,1200))),
    "Dial": ComponentSpec("Dial", "Регулятор", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doValue","Установить значение","work_in"),PortSpec("onChange","Изменение","event_out"),PortSpec("onPressed","Нажат","event_out"),PortSpec("onReleased","Отпущен","event_out"),PortSpec("NewValue","Новое значение","data_in"),PortSpec("Value","Значение","data_out")),
        properties=(PropertySpec("name","Имя","str","dial"),PropertySpec("minimum","Минимум","int",0,-1000000,1000000),PropertySpec("maximum","Максимум","int",100,-1000000,1000000),PropertySpec("value","Значение","int",50,-1000000,1000000),PropertySpec("step","Шаг","int",1,1,1000000),PropertySpec("wrapping","Зацикливание","bool",False),PropertySpec("notches","Деления","bool",True),PropertySpec("x","X","int",380,0,3000),PropertySpec("y","Y","int",300,0,3000),PropertySpec("width","Ширина","int",100,40,1000),PropertySpec("height","Высота","int",100,40,1000))),
    "ToolButton": ComponentSpec("ToolButton", "Кнопка инструмента", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doClick","Нажать","work_in"),PortSpec("doSetText","Установить текст","work_in"),PortSpec("onClick","Нажатие","event_out"),PortSpec("onPressed","Нажата","event_out"),PortSpec("onReleased","Отпущена","event_out"),PortSpec("Text","Текст","data_in"),PortSpec("Caption","Текст","data_out")),
        properties=(PropertySpec("name","Имя","str","tool_button"),PropertySpec("text","Текст","str","Инструмент"),PropertySpec("checkable","Переключаемая","bool",False),PropertySpec("checked","Нажата","bool",False),PropertySpec("x","X","int",500,0,3000),PropertySpec("y","Y","int",300,0,3000),PropertySpec("width","Ширина","int",120,30,1000),PropertySpec("height","Высота","int",36,20,500))),
    "PlainTextEdit": ComponentSpec("PlainTextEdit", "Редактор обычного текста", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doSetText","Установить текст","work_in"),PortSpec("doAppend","Добавить строку","work_in"),PortSpec("doClear","Очистить","work_in"),PortSpec("onChange","Изменение","event_out"),PortSpec("onCursor","Курсор","event_out"),PortSpec("Value","Новый текст","data_in"),PortSpec("Text","Текст","data_out")),
        properties=(PropertySpec("name","Имя","str","plain_text"),PropertySpec("text","Текст","multiline",""),PropertySpec("placeholder","Подсказка","str","Введите текст"),PropertySpec("read_only","Только чтение","bool",False),PropertySpec("line_wrap","Перенос строк","bool",True),PropertySpec("x","X","int",32,0,3000),PropertySpec("y","Y","int",430,0,3000),PropertySpec("width","Ширина","int",420,80,1600),PropertySpec("height","Высота","int",180,60,1200))),
})

# Native Python library from NodeFlow. Delphi metadata/runtime is intentionally
# not loaded in the 4.0 trial; original ICO assets remain available.
try:
    from python_catalog import load_python_components
    _python_components, PYTHON_CATALOG_ERRORS = load_python_components(
        PortSpec, PropertySpec, ComponentSpec
    )
    COMPONENTS.update(_python_components)
except (OSError, ValueError, KeyError, ImportError) as exc:
    PYTHON_CATALOG_ERRORS = [str(exc)]


# Visual Python Builder 8.0: another large family of native Qt controls.
# Each component follows the current four-side model: methods left, events
# right, input data above and current values below.
COMPONENTS.update({
    "DoubleSpinBox": ComponentSpec("DoubleSpinBox", "Дробное числовое поле", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doValue","Установить значение","work_in"),PortSpec("onChange","Изменение","event_out"),PortSpec("onEditingFinished","Ввод завершён","event_out"),PortSpec("NewValue","Новое значение","data_in"),PortSpec("Value","Значение","data_out")),
        properties=(PropertySpec("name","Имя","str","double_spin"),PropertySpec("value","Значение","real",0.0,-1000000,1000000),PropertySpec("minimum","Минимум","real",0.0,-1000000,1000000),PropertySpec("maximum","Максимум","real",100.0,-1000000,1000000),PropertySpec("step","Шаг","real",0.1,0,1000000),PropertySpec("decimals","Знаков после запятой","int",2,0,12),PropertySpec("x","X","int",32,0,3000),PropertySpec("y","Y","int",650,0,3000),PropertySpec("width","Ширина","int",140,40,1000),PropertySpec("height","Высота","int",32,20,500))),
    "ScrollBar": ComponentSpec("ScrollBar", "Полоса прокрутки", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doValue","Установить значение","work_in"),PortSpec("onChange","Изменение","event_out"),PortSpec("onMoved","Перемещение","event_out"),PortSpec("NewValue","Новое значение","data_in"),PortSpec("Value","Значение","data_out")),
        properties=(PropertySpec("name","Имя","str","scroll_bar"),PropertySpec("value","Значение","int",0,-1000000,1000000),PropertySpec("minimum","Минимум","int",0,-1000000,1000000),PropertySpec("maximum","Максимум","int",100,-1000000,1000000),PropertySpec("step","Шаг","int",1,1,1000000),PropertySpec("page_step","Шаг страницы","int",10,1,1000000),PropertySpec("orientation","Ориентация","choice","Horizontal",options=("Horizontal","Vertical")),PropertySpec("x","X","int",190,0,3000),PropertySpec("y","Y","int",650,0,3000),PropertySpec("width","Ширина","int",260,20,1200),PropertySpec("height","Высота","int",28,20,500))),
    "TimeEdit": ComponentSpec("TimeEdit", "Время", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doSetTime","Установить время","work_in"),PortSpec("onChange","Изменение","event_out"),PortSpec("Time","Новое время","data_in"),PortSpec("Text","Текущее время","data_out")),
        properties=(PropertySpec("name","Имя","str","time_edit"),PropertySpec("time","Время HH:mm:ss","str","12:00:00"),PropertySpec("format","Формат","str","HH:mm:ss"),PropertySpec("calendar_popup","Календарь","bool",False),PropertySpec("x","X","int",470,0,3000),PropertySpec("y","Y","int",650,0,3000),PropertySpec("width","Ширина","int",130,40,1000),PropertySpec("height","Высота","int",32,20,500))),
    "DateTimeEdit": ComponentSpec("DateTimeEdit", "Дата и время", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doSetDateTime","Установить дату и время","work_in"),PortSpec("onChange","Изменение","event_out"),PortSpec("DateTime","Новое значение","data_in"),PortSpec("Text","Дата и время","data_out")),
        properties=(PropertySpec("name","Имя","str","date_time_edit"),PropertySpec("datetime","Дата и время ISO","str","2026-09-22T12:00:00"),PropertySpec("format","Формат","str","dd.MM.yyyy HH:mm:ss"),PropertySpec("calendar_popup","Календарь","bool",True),PropertySpec("x","X","int",620,0,3000),PropertySpec("y","Y","int",650,0,3000),PropertySpec("width","Ширина","int",210,40,1000),PropertySpec("height","Высота","int",32,20,500))),
    "TextBrowser": ComponentSpec("TextBrowser", "Просмотр HTML", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doSetHtml","Установить HTML","work_in"),PortSpec("doSetText","Установить текст","work_in"),PortSpec("doClear","Очистить","work_in"),PortSpec("onAnchor","Переход по ссылке","event_out"),PortSpec("Value","Содержимое","data_in"),PortSpec("Text","Текст","data_out")),
        properties=(PropertySpec("name","Имя","str","text_browser"),PropertySpec("html","HTML","multiline","<h3>Visual Python Builder</h3><p>Просмотр HTML</p>"),PropertySpec("open_external_links","Открывать внешние ссылки","bool",True),PropertySpec("x","X","int",32,0,3000),PropertySpec("y","Y","int",700,0,3000),PropertySpec("width","Ширина","int",420,80,1600),PropertySpec("height","Высота","int",180,60,1200))),
    "FontComboBox": ComponentSpec("FontComboBox", "Выбор шрифта", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doSetFont","Выбрать шрифт","work_in"),PortSpec("onChange","Изменение","event_out"),PortSpec("Family","Семейство","data_in"),PortSpec("CurrentFamily","Текущий шрифт","data_out")),
        properties=(PropertySpec("name","Имя","str","font_combo"),PropertySpec("family","Семейство","str","Segoe UI"),PropertySpec("x","X","int",470,0,3000),PropertySpec("y","Y","int",700,0,3000),PropertySpec("width","Ширина","int",240,60,1200),PropertySpec("height","Высота","int",32,20,500))),
    "KeySequenceEdit": ComponentSpec("KeySequenceEdit", "Горячая клавиша", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doSetSequence","Установить сочетание","work_in"),PortSpec("doClear","Очистить","work_in"),PortSpec("onChange","Изменение","event_out"),PortSpec("Sequence","Сочетание","data_in"),PortSpec("CurrentSequence","Текущее сочетание","data_out")),
        properties=(PropertySpec("name","Имя","str","key_sequence"),PropertySpec("sequence","Сочетание","str","Ctrl+Shift+S"),PropertySpec("x","X","int",730,0,3000),PropertySpec("y","Y","int",700,0,3000),PropertySpec("width","Ширина","int",180,60,1000),PropertySpec("height","Высота","int",32,20,500))),
    "CommandLinkButton": ComponentSpec("CommandLinkButton", "Командная кнопка", "Интерфейс", "#E5F2FC", visual=True,
        ports=(PortSpec("doClick","Нажать","work_in"),PortSpec("doSetText","Установить текст","work_in"),PortSpec("doSetDescription","Установить описание","work_in"),PortSpec("onClick","Нажатие","event_out"),PortSpec("Text","Текст","data_in"),PortSpec("Description","Описание","data_in"),PortSpec("Caption","Текущий текст","data_out")),
        properties=(PropertySpec("name","Имя","str","command_link"),PropertySpec("text","Текст","str","Продолжить"),PropertySpec("description","Описание","str","Выполнить выбранное действие"),PropertySpec("x","X","int",32,0,3000),PropertySpec("y","Y","int",900,0,3000),PropertySpec("width","Ширина","int",300,100,1200),PropertySpec("height","Высота","int",70,40,500))),
    "DialogButtonBox": ComponentSpec(
        "DialogButtonBox", "Кнопки диалога", "Интерфейс", "#E5F2FC",
        visual=True,
        description=(
            "Стандартная панель кнопок диалога. Qt сам выбирает правильный "
            "порядок кнопок для Windows, Linux и macOS."
        ),
        ports=(
            PortSpec("onAccepted", "Принято", "event_out",
                     description="Срабатывает для ОК, Сохранить, Да и других подтверждающих кнопок."),
            PortSpec("onRejected", "Отменено", "event_out",
                     description="Срабатывает для Отмена, Закрыть и других отменяющих кнопок."),
            PortSpec("onHelp", "Справка", "event_out",
                     description="Срабатывает при нажатии стандартной кнопки Справка."),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "dialog_buttons"),
            PropertySpec(
                "buttons", "Стандартные кнопки", "str", "Ok|Cancel",
                description=(
                    "Кнопки через |: Ok, Cancel, Save, Open, Yes, No, "
                    "Close, Apply, Reset, Help и другие стандартные кнопки Qt."
                ),
            ),
            PropertySpec(
                "orientation", "Ориентация", "choice", "Horizontal",
                options=("Horizontal", "Vertical"),
            ),
            PropertySpec("center_buttons", "Кнопки по центру", "bool", False),
            PropertySpec("enabled", "Доступна", "bool", True),
            PropertySpec("visible", "Видима", "bool", True),
            PropertySpec("tooltip", "Подсказка", "str", ""),
            PropertySpec("style", "Дополнительный QSS", "code", ""),
            PropertySpec("x", "X", "int", 32, 0, 3000),
            PropertySpec("y", "Y", "int", 980, 0, 3000),
            PropertySpec("width", "Ширина", "int", 180, 40, 1600),
            PropertySpec("height", "Высота", "int", 36, 20, 1200),
        ),
    ),
    "TableView": ComponentSpec(
        "TableView", "Табличное представление", "Интерфейс", "#E5F2FC",
        visual=True,
        description=(
            "Представление таблицы Qt без встроенных данных. Данные должны "
            "поступать из модели; пустой QTableView остаётся пустым."
        ),
        ports=(
            PortSpec("onClick", "Щелчок", "event_out",
                     description="Срабатывает при щелчке по ячейке модели."),
            PortSpec("onDoubleClick", "Двойной щелчок", "event_out",
                     description="Срабатывает при двойном щелчке по ячейке модели."),
            PortSpec("onActivated", "Активация", "event_out",
                     description="Срабатывает при активации элемента клавиатурой или мышью."),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "table_view"),
            PropertySpec("editable", "Разрешить изменение", "bool", True),
            PropertySpec("sorting_enabled", "Сортировка", "bool", False),
            PropertySpec("alternating_rows", "Чередовать цвет строк", "bool", False),
            PropertySpec("grid_visible", "Показывать сетку", "bool", True),
            PropertySpec("horizontal_header", "Горизонтальный заголовок", "bool", True),
            PropertySpec("vertical_header", "Вертикальный заголовок", "bool", True),
            PropertySpec("enabled", "Доступно", "bool", True),
            PropertySpec("visible", "Видимо", "bool", True),
            PropertySpec("tooltip", "Подсказка", "str", ""),
            PropertySpec("style", "Дополнительный QSS", "code", ""),
            PropertySpec("x", "X", "int", 32, 0, 3000),
            PropertySpec("y", "Y", "int", 1020, 0, 3000),
            PropertySpec("width", "Ширина", "int", 360, 80, 1600),
            PropertySpec("height", "Высота", "int", 180, 60, 1200),
        ),
    ),
    "Frame": ComponentSpec("Frame", "Рамка", "Интерфейс", "#E5F2FC", visual=True,
        ports=(), properties=(PropertySpec("name","Имя","str","frame"),PropertySpec("shape","Форма","choice","StyledPanel",options=("NoFrame","Box","Panel","StyledPanel","HLine","VLine","WinPanel")),PropertySpec("shadow","Тень","choice","Sunken",options=("Plain","Raised","Sunken")),PropertySpec("line_width","Толщина","int",1,0,20),PropertySpec("x","X","int",360,0,3000),PropertySpec("y","Y","int",900,0,3000),PropertySpec("width","Ширина","int",260,20,1600),PropertySpec("height","Высота","int",120,10,1200))),
    "HorizontalLine": ComponentSpec("HorizontalLine", "Горизонтальная линия", "Интерфейс", "#E5F2FC", visual=True,
        ports=(), properties=(PropertySpec("name","Имя","str","horizontal_line"),PropertySpec("line_width","Толщина","int",1,1,20),PropertySpec("x","X","int",650,0,3000),PropertySpec("y","Y","int",920,0,3000),PropertySpec("width","Ширина","int",260,20,1600),PropertySpec("height","Высота","int",8,2,100))),
})

# Version 9.0: custom QPainter instruments beyond Qt Designer.
def _instrument_spec(type_name, caption, unit="", maximum=100.0):
    ports=(PortSpec("doValue","Установить значение","work_in"),PortSpec("doSetRange","Установить диапазон","work_in"),PortSpec("doSetTitle","Установить заголовок","work_in"),PortSpec("doAddValue","Добавить точку","work_in"),PortSpec("doReset","Сбросить","work_in"),PortSpec("onChange","Значение изменено","event_out"),PortSpec("onAlarm","Тревога изменилась","event_out"),PortSpec("NewValue","Новое значение","data_in"),PortSpec("Minimum","Новый минимум","data_in"),PortSpec("Maximum","Новый максимум","data_in"),PortSpec("Title","Новый заголовок","data_in"),PortSpec("Sample","Точка графика","data_in"),PortSpec("Value","Текущее значение","data_out"),PortSpec("IsAlarm","Тревога","data_out"))
    props=(PropertySpec("name","Имя","str",type_name.lower()),PropertySpec("title","Заголовок","str",caption),PropertySpec("unit","Единица","str",unit),PropertySpec("value","Значение","real",0.0,-1000000,1000000),PropertySpec("minimum","Минимум","real",0.0,-1000000,1000000),PropertySpec("maximum","Максимум","real",maximum,-1000000,1000000),PropertySpec("warning","Предупреждение","real",maximum*.7,-1000000,1000000),PropertySpec("critical","Тревога","real",maximum*.9,-1000000,1000000),PropertySpec("precision","Точность","int",1,0,6),PropertySpec("history_size","История","int",80,5,1000),PropertySpec("primary_color","Основной цвет","color","#35C2FF"),PropertySpec("secondary_color","Фоновая шкала","color","#26364A"),PropertySpec("needle_color","Стрелка","color","#FF5252"),PropertySpec("background_color","Фон","color","#101820"),PropertySpec("text_color","Текст","color","#F4F7FB"),PropertySpec("warning_color","Предупреждение","color","#FFB020"),PropertySpec("alarm_color","Тревога","color","#FF3B30"),PropertySpec("border_color","Рамка","color","#52667A"),PropertySpec("x","X","int",32,0,5000),PropertySpec("y","Y","int",32,0,5000),PropertySpec("width","Ширина","int",180,40,2000),PropertySpec("height","Высота","int",180,30,2000),PropertySpec("min_width","Мин. ширина","int",40,0,2000),PropertySpec("min_height","Мин. высота","int",30,0,2000),PropertySpec("max_width","Макс. ширина","int",16777215,1,16777215),PropertySpec("max_height","Макс. высота","int",16777215,1,16777215),PropertySpec("enabled","Доступен","bool",True),PropertySpec("visible","Видим","bool",True),PropertySpec("tooltip","Подсказка","str",""),PropertySpec("accessible_name","Доступность","str",caption),PropertySpec("font_family","Шрифт","str","Segoe UI"),PropertySpec("font_size","Размер","int",10,6,72),PropertySpec("font_bold","Полужирный","bool",False),PropertySpec("font_italic","Курсив","bool",False),PropertySpec("font_underline","Подчёркнутый","bool",False),PropertySpec("style","QSS","code",""))
    return ComponentSpec(type_name,caption,"Приборы и графика","#DDEBFA",ports=ports,properties=props,description="Рабочий рисуемый прибор с данными и тревогой.",visual=True)

COMPONENTS.update({
 "Gauge":_instrument_spec("Gauge","Круговой индикатор","%"),
 "Speedometer":_instrument_spec("Speedometer","Спидометр","км/ч",240.0),
 "Tachometer":_instrument_spec("Tachometer","Тахометр","об/мин",8000.0),
 "Thermometer":_instrument_spec("Thermometer","Термометр","°C",120.0),
 "LevelMeter":_instrument_spec("LevelMeter","Уровень","%"),
 "LEDIndicator":_instrument_spec("LEDIndicator","Светодиод",""),
 "Compass":_instrument_spec("Compass","Компас","°",360.0),
 "BatteryIndicator":_instrument_spec("BatteryIndicator","Батарея","%"),
 "SignalIndicator":_instrument_spec("SignalIndicator","Сигнал","%"),
 "Sparkline":_instrument_spec("Sparkline","Мини-график",""),
 "AnalogClock":_instrument_spec("AnalogClock","Аналоговые часы","",86400.0),
 "Knob":_instrument_spec("Knob","Поворотный регулятор","%"),
})

# Version 10.0: charts, oscilloscope and digital displays.
COMPONENTS.update({
 "LineChart":_instrument_spec("LineChart","Линейный график",""),
 "BarChart":_instrument_spec("BarChart","Столбчатая диаграмма",""),
 "PieChart":_instrument_spec("PieChart","Круговая диаграмма","%"),
 "RadarChart":_instrument_spec("RadarChart","Радарная диаграмма",""),
 "Oscilloscope":_instrument_spec("Oscilloscope","Осциллограф",""),
 "VUMeter":_instrument_spec("VUMeter","VU-индикатор","дБ"),
 "SevenSegmentDisplay":_instrument_spec("SevenSegmentDisplay","Семисегментный дисплей",""),
 "LEDMatrix":_instrument_spec("LEDMatrix","Светодиодная матрица",""),
})

# Version 12.0: advanced visualization laboratory.
def _advanced_instrument_spec(type_name, caption, mode, extra_ports=(), extra_properties=()):
    base = _instrument_spec(type_name, caption, "")
    return ComponentSpec(
        type_name, caption, "Приборы и графика", base.color,
        ports=base.ports + (
            PortSpec("doAddSeriesPoint", "Добавить точку серии", "work_in"),
            PortSpec("doSetSeriesData", "Загрузить серию", "work_in"),
            PortSpec("doClearSeries", "Очистить серии", "work_in"),
            PortSpec("doExportImage", "Экспорт изображения", "work_in"),
            PortSpec("onExport", "Изображение сохранено", "event_out"),
            PortSpec("SeriesName", "Имя серии", "data_in"),
            PortSpec("SeriesX", "X серии", "data_in"),
            PortSpec("SeriesY", "Y серии", "data_in"),
            PortSpec("SeriesData", "Массив серии", "data_in"),
            PortSpec("ExportPath", "Путь изображения", "data_in"),
            PortSpec("SeriesCount", "Количество серий", "data_out"),
        ) + tuple(extra_ports),
        properties=base.properties + (
            PropertySpec("render_mode", "Режим отрисовки", "str", mode),
            PropertySpec("show_grid", "Показывать сетку", "bool", True),
            PropertySpec("grid_rows", "Строк сетки", "int", 8, 2, 64),
            PropertySpec("grid_columns", "Столбцов сетки", "int", 12, 2, 128),
            PropertySpec("line_width", "Толщина линии", "int", 2, 1, 12),
            PropertySpec("fill_opacity", "Прозрачность заливки", "int", 90, 0, 255),
            PropertySpec("x_axis_title", "Подпись оси X", "str", "X"),
            PropertySpec("y_axis_title", "Подпись оси Y", "str", "Y"),
            PropertySpec("show_legend", "Показывать легенду", "bool", True),
            PropertySpec("auto_scale", "Автомасштаб", "bool", True),
            PropertySpec("legend_position", "Положение легенды", "choice", "TopRight", options=("TopLeft","TopRight","BottomLeft","BottomRight")),
            PropertySpec("series_palette", "Цвета серий", "str", "#35C2FF|#FFB020|#59FF88|#FF5FA2|#B18CFF|#FFFFFF"),
            PropertySpec("initial_series", "Начальные серии JSON", "code", '{"Серия A":[[0,15],[1,42],[2,28],[3,75]],"Серия B":[[0,65],[1,35],[2,58],[3,44]]}'),
            PropertySpec("initial_series", "Начальные серии JSON", "code", '{"Серия A":[[0,15],[1,42],[2,28],[3,75]],"Серия B":[[0,65],[1,35],[2,58],[3,44]]}'),
        ) + tuple(extra_properties),
        description=(f"Рабочий компонент «{caption}»: виден в редакторе формы, "
                     "генерируется в PySide6, принимает данные и хранит историю."),
        visual=True, subgroup="Расширенная визуализация",
    )

COMPONENTS.update({
    "XYPlot": _advanced_instrument_spec("XYPlot", "XY-график", "xyplot", (
        PortSpec("doAddPoint", "Добавить XY-точку", "work_in"),
        PortSpec("XValue", "Координата X", "data_in"), PortSpec("YValue", "Координата Y", "data_in"),
        PortSpec("LastX", "Последний X", "data_out"), PortSpec("LastY", "Последний Y", "data_out"),
    ), (PropertySpec("x_minimum", "X минимум", "real", 0.0, -1000000, 1000000), PropertySpec("x_maximum", "X максимум", "real", 100.0, -1000000, 1000000))),
    "HeatMap": _advanced_instrument_spec("HeatMap", "Тепловая карта", "heatmap", (
        PortSpec("doSetCell", "Установить ячейку", "work_in"), PortSpec("Row", "Строка", "data_in"),
        PortSpec("Column", "Столбец", "data_in"), PortSpec("Intensity", "Интенсивность", "data_in"),
    )),
    "Timeline": _advanced_instrument_spec("Timeline", "Временная шкала", "timeline", (
        PortSpec("doAddEvent", "Добавить событие", "work_in"), PortSpec("Timestamp", "Время", "data_in"),
        PortSpec("EventText", "Подпись", "data_in"),
    )),
    "WaterfallChart": _advanced_instrument_spec("WaterfallChart", "Водопад", "waterfall"),
    "GeoMap": _advanced_instrument_spec("GeoMap", "Карта координат", "geomap", (
        PortSpec("doSetPosition", "Установить координаты", "work_in"),
        PortSpec("Latitude", "Широта", "data_in"), PortSpec("Longitude", "Долгота", "data_in"),
        PortSpec("Zoom", "Масштаб", "data_in"), PortSpec("CurrentLatitude", "Текущая широта", "data_out"),
        PortSpec("CurrentLongitude", "Текущая долгота", "data_out"),
    ), (PropertySpec("latitude", "Широта", "real", 55.7558, -90, 90), PropertySpec("longitude", "Долгота", "real", 37.6173, -180, 180), PropertySpec("zoom", "Масштаб карты", "int", 8, 1, 20))),
    "Waveform": _advanced_instrument_spec("Waveform", "Форма сигнала", "waveform"),
    "SpectrumAnalyzer": _advanced_instrument_spec("SpectrumAnalyzer", "Анализатор спектра", "spectrum", (), (PropertySpec("bands", "Полос", "int", 24, 4, 128),)),
    "MultiSegmentDisplay": _advanced_instrument_spec("MultiSegmentDisplay", "Многосегментный дисплей", "multisegment", (), (PropertySpec("segments", "Сегментов", "int", 14, 7, 32), PropertySpec("digits", "Разрядов", "int", 8, 1, 32))),
    "CustomInstrument": _advanced_instrument_spec("CustomInstrument", "Пользовательский прибор", "custom", (
        PortSpec("doSetDesign", "Применить дизайн", "work_in"), PortSpec("Design", "JSON дизайна", "data_in"),
    ), (PropertySpec("design", "Описание прибора JSON", "code", '{"shape":"dial","show_value":true,"ticks":10}'), PropertySpec("template", "Шаблон", "choice", "Dial", options=("Dial","Bar","Ring","Digital","Graph")))),
})

# Version 13.0: layer-based Canvas and dashboard designer runtime.
COMPONENTS["DashboardCanvas"] = ComponentSpec(
    "DashboardCanvas", "Холст приборной панели", "Приборы и графика", "#DDEBFA",
    ports=(
        PortSpec("doSetScene", "Загрузить сцену JSON", "work_in"),
        PortSpec("doAddShape", "Добавить фигуру", "work_in"),
        PortSpec("doRemoveLast", "Удалить последнюю", "work_in"),
        PortSpec("doClear", "Очистить холст", "work_in"),
        PortSpec("doSetZoom", "Установить масштаб", "work_in"),
        PortSpec("doExportImage", "Экспорт PNG", "work_in"),
        PortSpec("onChange", "Сцена изменена", "event_out"),
        PortSpec("onExport", "Изображение сохранено", "event_out"),
        PortSpec("Scene", "Сцена JSON", "data_in"),
        PortSpec("ShapeType", "Тип фигуры", "data_in"),
        PortSpec("ShapeText", "Текст", "data_in"),
        PortSpec("ShapeColor", "Цвет", "data_in"),
        PortSpec("ShapeX", "X фигуры", "data_in"), PortSpec("ShapeY", "Y фигуры", "data_in"),
        PortSpec("ShapeWidth", "Ширина", "data_in"), PortSpec("ShapeHeight", "Высота", "data_in"),
        PortSpec("ShapeRotation", "Поворот", "data_in"), PortSpec("ShapeLayer", "Слой", "data_in"),
        PortSpec("Zoom", "Масштаб", "data_in"), PortSpec("ExportPath", "Путь PNG", "data_in"),
        PortSpec("SceneJson", "Текущая сцена", "data_out"), PortSpec("ItemCount", "Объектов", "data_out"),
    ),
    properties=(
        PropertySpec("name", "Имя", "str", "dashboard_canvas"),
        PropertySpec("scene", "Внутренние данные сцены", "code", '[{"type":"rect","x":20,"y":24,"w":180,"h":90,"color":"#22577A","layer":0},{"type":"ellipse","x":235,"y":35,"w":90,"h":90,"color":"#35C2FF","layer":1},{"type":"text","x":30,"y":48,"w":150,"h":40,"text":"Панель 13.0","color":"#FFFFFF","layer":2}]'),
        PropertySpec("background_color", "Фон", "color", "#101820"),
        PropertySpec("grid_color", "Сетка", "color", "#26364A"),
        PropertySpec("show_grid", "Показывать сетку", "bool", True),
        PropertySpec("grid_size", "Шаг сетки", "int", 20, 5, 200),
        PropertySpec("zoom", "Масштаб", "real", 1.0, 0, 10),
        PropertySpec("antialiasing", "Сглаживание", "bool", True),
        PropertySpec("x", "X", "int", 32, 0, 5000), PropertySpec("y", "Y", "int", 32, 0, 5000),
        PropertySpec("width", "Ширина", "int", 620, 80, 3000), PropertySpec("height", "Высота", "int", 360, 60, 2000),
        PropertySpec("enabled", "Доступен", "bool", True), PropertySpec("visible", "Видим", "bool", True),
        PropertySpec("tooltip", "Подсказка", "str", "Холст с фигурами, слоями и экспортом"),
    ),
    description="Холст для приборных панелей: фигуры, текст, слои, масштаб, поворот, JSON-сцена и экспорт PNG.",
    visual=True, subgroup="Холст и панели",
)

# Version 16.2.57: a domain-neutral view for any two-dimensional state.
COMPONENTS["GridCanvas"] = ComponentSpec(
    "GridCanvas", "Холст двумерного поля", "Приборы и графика", "#DDEBFA",
    ports=(
        PortSpec(
            "doSetGrid", "Показать поле", "work_in",
            description="Читает вход «Поле» и сразу перерисовывает клетки.",
        ),
        PortSpec(
            "doSetPalette", "Изменить палитру", "work_in",
            description="Применяет словарь цветов из входа «Палитра».",
        ),
        PortSpec("doClear", "Очистить изображение", "work_in"),
        PortSpec("doRefresh", "Перерисовать", "work_in"),
        PortSpec(
            "onCellClick", "Щелчок по клетке", "event_out",
            description="Срабатывает при щелчке; координаты доступны снизу.",
        ),
        PortSpec("Grid", "Поле", "data_in", description="Список строк: [[0,1],[1,0]]."),
        PortSpec(
            "Palette", "Палитра", "data_in",
            description='Словарь «значение → цвет», например {"1":"#35C2FF"}.',
        ),
        PortSpec("Column", "Столбец", "data_out"),
        PortSpec("Row", "Строка", "data_out"),
        PortSpec("CellValue", "Значение клетки", "data_out"),
        PortSpec("CurrentGrid", "Текущее поле", "data_out"),
        PortSpec("ColumnCount", "Число столбцов", "data_out"),
        PortSpec("RowCount", "Число строк", "data_out"),
    ),
    properties=(
        PropertySpec("name", "Имя", "str", "grid_canvas"),
        PropertySpec("columns", "Столбцов до загрузки", "int", 10, 1, 500),
        PropertySpec("rows", "Строк до загрузки", "int", 20, 1, 500),
        PropertySpec("cell_size", "Размер клетки", "int", 24, 2, 200),
        PropertySpec("fit_to_widget", "Вписывать поле", "bool", True),
        PropertySpec("show_grid", "Показывать линии", "bool", True),
        PropertySpec("show_values", "Показывать значения", "bool", False),
        PropertySpec("interactive", "Разрешить щелчки", "bool", True),
        PropertySpec("empty_value", "Пустое значение", "str", "0"),
        PropertySpec(
            "palette", "Палитра значений", "code",
            '{"1":"#35C2FF","2":"#FFB020","3":"#59FF88","4":"#FF5FA2"}',
            description="JSON-словарь, где ключ — значение клетки, а значение — цвет.",
        ),
        PropertySpec("background_color", "Цвет пустых клеток", "color", "#101820"),
        PropertySpec("grid_color", "Цвет линий", "color", "#26364A"),
        PropertySpec(
            "initial_grid", "Начальное поле", "code", "",
            description="Необязательный JSON-массив строк. Обычно поле приходит нитью.",
        ),
        PropertySpec("x", "X", "int", 32, 0, 5000),
        PropertySpec("y", "Y", "int", 32, 0, 5000),
        PropertySpec("width", "Ширина", "int", 300, 80, 3000),
        PropertySpec("height", "Высота", "int", 540, 80, 3000),
        PropertySpec("enabled", "Доступен", "bool", True),
        PropertySpec("visible", "Видим", "bool", True),
        PropertySpec(
            "tooltip", "Подсказка", "str",
            "Универсальное отображение двумерного массива",
        ),
    ),
    description=(
        "Показывает любое двумерное поле цветными клетками и сообщает координаты "
        "щелчка. Подходит для игр, карт, редакторов уровней, матриц и тепловых схем."
    ),
    visual=True,
    subgroup="Холст и панели",
)

# Version 11.0: real four-side branching nodes.  Counts are instance
# properties, so users can add/remove ports without creating fake components.
COMPONENTS.update({
    "EventHub": ComponentSpec(
        "EventHub", "Хаб событий", "Логика", "#E8F1EC",
        properties=(
            PropertySpec("input_count", "Входов действий", "int", 1, 1, 64),
            PropertySpec("output_count", "Выходов событий", "int", 4, 1, 64),
        ),
        description=("Разветвляет любое входное событие на все выходы. "
                     "Количество входов и выходов можно менять в свойствах; "
                     "новая точка также создаётся перетаскиванием нити на корпус."),
        subgroup="Управление событиями",
        hiasm_sub="input_count|doInput,output_count|onOutput,,",
    ),
    "TwoWayBinding": ComponentSpec(
        "TwoWayBinding", "Двусторонняя привязка", "Данные", "#DDEBFA",
        ports=(
            PortSpec("doSet", "Модель → интерфейс", "work_in"),
            PortSpec("doRefresh", "Интерфейс → модель", "work_in"),
            PortSpec("onChange", "Значение изменено", "event_out"),
            PortSpec("Value", "Новое значение", "data_in"),
            PortSpec("CurrentValue", "Текущее значение", "data_out"),
        ),
        properties=(
            PropertySpec("target", "Имя компонента", "str", "line_edit"),
            PropertySpec("property", "Свойство", "choice", "text",
                         options=("text", "value", "checked", "currentIndex")),
            PropertySpec("initial", "Начальное значение", "code", ""),
        ),
        description=("Синхронизирует модель с text/value/checked/currentIndex "
                     "визуального компонента в обе стороны. Защищена от "
                     "повторного входа и циклических сигналов."),
        subgroup="Связывание данных",
    ),
    "DataHub": ComponentSpec(
        "DataHub", "Хаб данных", "Данные", "#E7F0FA",
        properties=(
            PropertySpec("input_count", "Входов данных", "int", 1, 1, 64),
            PropertySpec("output_count", "Выходов данных", "int", 4, 1, 64),
        ),
        description=("Аккуратно разветвляет данные. Выход N читает вход N, "
                     "а если такого входа нет — вход 1. Один выход можно "
                     "подключать к нескольким потребителям через отдельные точки."),
        subgroup="Маршрутизация данных",
        hiasm_sub=",,output_count|DataOut,input_count|DataIn",
    ),
})


# Version 16.1: reusable building blocks for games and stateful applications.
COMPONENTS.update({
    "RepeatLoop": ComponentSpec(
        "RepeatLoop", "Цикл с повторением", "Логика", "#FCE8D5",
        ports=(
            PortSpec("doLoop", "Выполнить цикл", "work_in"),
            PortSpec("doBreak", "Прервать", "work_in"),
            PortSpec("onIteration", "Итерация", "event_out"),
            PortSpec("onDone", "Цикл завершён", "event_out"),
            PortSpec("Count", "Количество", "data_in"),
            PortSpec("Index", "Индекс", "data_out"),
        ),
        properties=(PropertySpec("count", "Количество", "int", 10, 0, 100000),),
        description="Синхронно повторяет цепочку событий. doBreak безопасно завершает текущий цикл.",
        subgroup="Циклы",
    ),
    "ListStore": ComponentSpec(
        "ListStore", "Список данных", "Данные", "#E7F0FA",
        ports=(
            PortSpec("doAdd", "Добавить", "work_in"),
            PortSpec("doSet", "Записать по индексу", "work_in"),
            PortSpec("doRemove", "Удалить по индексу", "work_in"),
            PortSpec("doClear", "Очистить", "work_in"),
            PortSpec("onChange", "Список изменён", "event_out"),
            PortSpec("Value", "Значение", "data_in"),
            PortSpec("Index", "Индекс", "data_in"),
            PortSpec("Items", "Список", "data_out"),
            PortSpec("Count", "Количество", "data_out"),
            PortSpec("Item", "Элемент", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "list_store"),
            PropertySpec("initial", "Начальный JSON-массив", "code", "[]"),
        ),
        description="Изменяемый список для очередей, фигур, рекордов и игровых объектов.",
        subgroup="Коллекции",
    ),
    "GridState": ComponentSpec(
        "GridState", "Двумерное поле", "Данные", "#E7F0FA",
        ports=(
            PortSpec("doSetCell", "Записать ячейку", "work_in"),
            PortSpec("doClearCell", "Очистить ячейку", "work_in"),
            PortSpec("doClear", "Очистить поле", "work_in"),
            PortSpec("doClearLines", "Удалить заполненные строки", "work_in"),
            PortSpec("onChange", "Поле изменено", "event_out"),
            PortSpec("onLines", "Строки удалены", "event_out"),
            PortSpec("Column", "Столбец", "data_in"),
            PortSpec("Row", "Строка", "data_in"),
            PortSpec("Value", "Значение", "data_in"),
            PortSpec("Cell", "Ячейка", "data_out"),
            PortSpec("Grid", "Поле", "data_out"),
            PortSpec("RowsJson", "Поле JSON", "data_out"),
            PortSpec("ClearedLines", "Удалено строк", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "grid"),
            PropertySpec("columns", "Столбцов", "int", 10, 1, 200),
            PropertySpec("rows", "Строк", "int", 20, 1, 200),
            PropertySpec("empty", "Пустое значение", "code", "0"),
        ),
        description="Двумерный массив с безопасным доступом и удалением заполненных строк.",
        subgroup="Коллекции",
    ),
    "GridBatchWriter": ComponentSpec(
        "GridBatchWriter", "Запись набора клеток", "Данные", "#E7F0FA",
        ports=(
            PortSpec("doWrite", "Записать клетки", "work_in"),
            PortSpec("doClear", "Очистить клетки", "work_in"),
            PortSpec("onDone", "Запись завершена", "event_out"),
            PortSpec("onError", "Ошибка данных", "event_out"),
            PortSpec("Grid", "Поле", "data_in"),
            PortSpec("Points", "Набор координат", "data_in"),
            PortSpec("OffsetColumn", "Смещение по столбцам", "data_in"),
            PortSpec("OffsetRow", "Смещение по строкам", "data_in"),
            PortSpec("Value", "Записываемое значение", "data_in"),
            PortSpec("CurrentGrid", "Изменённое поле", "data_out"),
            PortSpec("ChangedCells", "Изменено клеток", "data_out"),
            PortSpec("Error", "Описание ошибки", "data_out"),
        ),
        properties=(
            PropertySpec("empty", "Пустое значение", "code", "0"),
        ),
        description=(
            "Записывает или очищает произвольный набор координат в переданном "
            "двумерном поле. Нода не содержит правил конкретной игры."
        ),
        subgroup="Коллекции",
    ),
    "KeyboardInput": ComponentSpec(
        "KeyboardInput", "Клавиатура", "События", "#FCE8D5",
        ports=(
            PortSpec("onPress", "Клавиша нажата", "event_out"),
            PortSpec("onRelease", "Клавиша отпущена", "event_out"),
            PortSpec("Key", "Клавиша", "data_out"),
            PortSpec("IsAutoRepeat", "Автоповтор", "data_out"),
        ),
        properties=(
            PropertySpec("name", "Имя", "str", "keyboard"),
            PropertySpec("keys", "Разрешённые клавиши", "str", "Left,Right,Up,Down,Space,P,R,A,D,S,W"),
            PropertySpec("accept_auto_repeat", "Принимать автоповтор", "bool", True),
        ),
        description="Глобальные события нажатия и отпускания клавиш с фильтром по именам.",
        subgroup="Ввод",
    ),
})

# Version 16.1: additional universal primitives.
COMPONENTS.update({
 "ForRange": ComponentSpec("ForRange","Цикл по диапазону","Логика","#FCE8D5",ports=(PortSpec("doLoop","Выполнить","work_in"),PortSpec("doBreak","Прервать","work_in"),PortSpec("onIteration","Итерация","event_out"),PortSpec("onDone","Завершено","event_out"),PortSpec("Start","Начало","data_in"),PortSpec("Stop","Конец","data_in"),PortSpec("Step","Шаг","data_in"),PortSpec("Index","Индекс","data_out")),properties=(PropertySpec("start","Начало","int",0,-1000000,1000000),PropertySpec("stop","Конец","int",10,-1000000,1000000),PropertySpec("step","Шаг","int",1,-1000000,1000000)),description="Универсальный range с досрочным выходом.",subgroup="Циклы"),
 "ForEach": ComponentSpec("ForEach","Для каждого","Логика","#FCE8D5",ports=(PortSpec("doLoop","Выполнить","work_in"),PortSpec("doBreak","Прервать","work_in"),PortSpec("onIteration","Элемент","event_out"),PortSpec("onDone","Завершено","event_out"),PortSpec("Items","Коллекция","data_in"),PortSpec("Item","Элемент","data_out"),PortSpec("Index","Индекс или ключ","data_out")),properties=(PropertySpec("items","Коллекция JSON","code","[]"),),description="Перебирает список, строку или словарь.",subgroup="Циклы"),
 "WhileLoop": ComponentSpec("WhileLoop","Цикл пока","Логика","#FCE8D5",ports=(PortSpec("doLoop","Выполнить","work_in"),PortSpec("doBreak","Прервать","work_in"),PortSpec("onIteration","Итерация","event_out"),PortSpec("onDone","Завершено","event_out"),PortSpec("Condition","Условие","data_in"),PortSpec("Index","Индекс","data_out"),PortSpec("LimitReached","Достигнут предел","data_out")),properties=(PropertySpec("condition","Начальное условие","bool",True),PropertySpec("max_iterations","Защитный предел","int",1000,1,1000000)),description="While с обязательным защитным пределом.",subgroup="Циклы"),
 "Sequence": ComponentSpec("Sequence","Последовательность","Логика","#FCE8D5",ports=(PortSpec("doRun","Запустить","work_in"),PortSpec("onStep1","Шаг 1","event_out"),PortSpec("onStep2","Шаг 2","event_out"),PortSpec("onStep3","Шаг 3","event_out"),PortSpec("onStep4","Шаг 4","event_out"),PortSpec("onDone","Завершено","event_out")),description="Запускает ветви строго по порядку.",subgroup="Поток событий"),
 "EventGate": ComponentSpec("EventGate","Шлюз событий","Логика","#FCE8D5",ports=(PortSpec("doInput","Событие","work_in"),PortSpec("doOpen","Открыть","work_in"),PortSpec("doClose","Закрыть","work_in"),PortSpec("doToggle","Переключить","work_in"),PortSpec("onPass","Пропущено","event_out"),PortSpec("IsOpen","Открыт","data_out")),properties=(PropertySpec("open","Открыт при запуске","bool",True),),description="Разрешает или блокирует события.",subgroup="Поток событий"),
 "Once": ComponentSpec("Once","Один раз","Логика","#FCE8D5",ports=(PortSpec("doInput","Событие","work_in"),PortSpec("doReset","Сбросить","work_in"),PortSpec("onFirst","Первый раз","event_out"),PortSpec("onRepeat","Повтор","event_out"),PortSpec("HasFired","Уже сработал","data_out")),description="Разделяет первое и повторные события.",subgroup="Поток событий"),
 "Debounce": ComponentSpec("Debounce","Антидребезг","Логика","#FFF3CD",ports=(PortSpec("doInput","Импульс","work_in"),PortSpec("doCancel","Отменить","work_in"),PortSpec("onEvent","После паузы","event_out"),PortSpec("Interval","Интервал","data_in")),properties=(PropertySpec("name","Имя","str","debounce"),PropertySpec("interval","Интервал, мс","int",250,1,600000)),description="Выдаёт последнее событие после периода тишины.",subgroup="Поток событий"),
 "Throttle": ComponentSpec("Throttle","Ограничитель частоты","Логика","#FFF3CD",ports=(PortSpec("doInput","Импульс","work_in"),PortSpec("doReset","Сбросить","work_in"),PortSpec("onEvent","Разрешено","event_out"),PortSpec("onSkipped","Пропущено","event_out"),PortSpec("Interval","Интервал","data_in")),properties=(PropertySpec("interval","Интервал, мс","int",100,1,600000),),description="Ограничивает частоту событий.",subgroup="Поток событий"),
 "DictStore": ComponentSpec("DictStore","Словарь","Данные","#E7F0FA",ports=(PortSpec("doSet","Записать","work_in"),PortSpec("doRemove","Удалить","work_in"),PortSpec("doClear","Очистить","work_in"),PortSpec("onChange","Изменено","event_out"),PortSpec("Key","Ключ","data_in"),PortSpec("Value","Значение","data_in"),PortSpec("Dictionary","Словарь","data_out"),PortSpec("Item","Значение","data_out"),PortSpec("Keys","Ключи","data_out"),PortSpec("Values","Значения","data_out"),PortSpec("Count","Количество","data_out"),PortSpec("ContainsKey","Есть ключ","data_out")),properties=(PropertySpec("name","Имя","str","dict_store"),PropertySpec("initial","Начальный JSON","code","{}")),description="Изменяемый словарь общего назначения.",subgroup="Коллекции"),
 "ConvertValue": ComponentSpec("ConvertValue","Преобразование типа","Данные","#E7F0FA",ports=(PortSpec("doConvert","Преобразовать","work_in"),PortSpec("onResult","Готово","event_out"),PortSpec("onError","Ошибка","event_out"),PortSpec("Value","Значение","data_in"),PortSpec("Result","Результат","data_out"),PortSpec("Error","Ошибка","data_out")),properties=(PropertySpec("target_type","Тип","choice","string",options=("string","integer","float","boolean","list","dictionary","json")),PropertySpec("default","При ошибке","code","None")),description="Безопасно преобразует типы и JSON.",subgroup="Преобразования"),
 "Geometry2D": ComponentSpec("Geometry2D","Геометрия 2D","Данные","#E7F0FA",ports=(PortSpec("doCalculate","Вычислить","work_in"),PortSpec("onResult","Готово","event_out"),PortSpec("AX","A X","data_in"),PortSpec("AY","A Y","data_in"),PortSpec("AWidth","A ширина","data_in"),PortSpec("AHeight","A высота","data_in"),PortSpec("BX","B X","data_in"),PortSpec("BY","B Y","data_in"),PortSpec("BWidth","B ширина","data_in"),PortSpec("BHeight","B высота","data_in"),PortSpec("Result","Результат","data_out"),PortSpec("Distance","Расстояние","data_out"),PortSpec("X","X","data_out"),PortSpec("Y","Y","data_out")),properties=(PropertySpec("operation","Операция","choice","intersects",options=("intersects","contains","distance","clamp_point")),),description="Пересечение, попадание, расстояние и ограничение точки.",subgroup="Геометрия"),
 "MouseInput": ComponentSpec("MouseInput","Мышь","События","#FCE8D5",ports=(PortSpec("onPress","Нажатие","event_out"),PortSpec("onRelease","Отпускание","event_out"),PortSpec("onMove","Перемещение","event_out"),PortSpec("X","X","data_out"),PortSpec("Y","Y","data_out"),PortSpec("Button","Кнопка","data_out")),properties=(PropertySpec("track_move","Отслеживать движение","bool",True),),description="Глобальные координаты и кнопки мыши.",subgroup="Ввод"),
})

# Version 16.1: user-defined static graph containers.
COMPONENTS.update({
 "UserContainer": ComponentSpec("UserContainer","Контейнер пользователя","Контейнеры","#E9E1F8",properties=(PropertySpec("name","Имя блока","str","Мой блок"),PropertySpec("description","Назначение","multiline",""),PropertySpec("version","Версия контейнера","str","1.0"),PropertySpec("category","Категория библиотеки","str","Мои контейнеры"),PropertySpec("subgroup","Подкатегория библиотеки","str","Основные"),PropertySpec("tags","Метки через запятую","str",""),PropertySpec("subgraph","Внутренняя схема","code",{"format":1,"nodes":[],"connections":[]}),PropertySpec("interface","Внешний интерфейс","code",[])),description="Сворачивает внутреннюю схему в одну ноду. Двойной щелчок открывает содержимое; паспорт и внешний интерфейс редактируются без JSON.",subgroup="Пользовательские блоки"),
 "ContainerEventInput": ComponentSpec("ContainerEventInput","Вход события контейнера","Контейнеры","#EFE8FA",ports=(PortSpec("onEvent","Внутреннее событие","event_out"),),properties=(PropertySpec("name","Имя внешней точки","str","doInput"),),description="Создаёт внешний вход действия.",subgroup="Интерфейс контейнера"),
 "ContainerDataInput": ComponentSpec("ContainerDataInput","Вход данных контейнера","Контейнеры","#EFE8FA",ports=(PortSpec("Data","Внутренние данные","data_out"),),properties=(PropertySpec("name","Имя внешней точки","str","Value"),),description="Создаёт внешний вход данных.",subgroup="Интерфейс контейнера"),
 "ContainerEventOutput": ComponentSpec("ContainerEventOutput","Выход события контейнера","Контейнеры","#EFE8FA",ports=(PortSpec("doEvent","Внутреннее действие","work_in"),),properties=(PropertySpec("name","Имя внешней точки","str","onResult"),),description="Создаёт внешний выход события.",subgroup="Интерфейс контейнера"),
 "ContainerDataOutput": ComponentSpec("ContainerDataOutput","Выход данных контейнера","Контейнеры","#EFE8FA",ports=(PortSpec("Data","Внутренние данные","data_in"),),properties=(PropertySpec("name","Имя внешней точки","str","Result"),),description="Создаёт внешний выход данных.",subgroup="Интерфейс контейнера"),
})

# Rich Qt properties for the editor's native visual controls. Every property is
# also available as an optional top data point, following the current four-side
# convention rather than the old all-on-top NodeFlow layout.
def _enrich_native_qt_components() -> None:
    try:
        from python_library.gui_properties import property_definitions_for
    except ImportError:
        return
    mapping = {
        "Button": ("Gui.button", "QPushButton"),
        "Label": ("Gui.label", "QLabel"),
        "LineEdit": ("Gui.line_edit", "QLineEdit"),
        "TextEdit": ("Gui.text_edit", "QTextEdit"),
        "CheckBox": ("Gui.checkbox", "QCheckBox"),
        "ComboBox": ("Gui.combo_box", "QComboBox"),
        "ListWidget": ("Gui.list_widget", "QListWidget"),
        "ProgressBar": ("Gui.progress_bar", "QProgressBar"),
        "Slider": ("Gui.slider", "QSlider"),
        "SpinBox": ("Gui.spin_box", "QSpinBox"),
        "TableWidget": ("Gui.table", "QTableWidget"),
        "TreeWidget": ("Gui.tree", "QTreeWidget"),
        "DateEdit": ("Gui.date_edit", "QDateEdit"),
        "Calendar": ("Gui.calendar", "QCalendarWidget"),
        "LCDNumber": ("GuiQt.lcd_number", "QLCDNumber"),
        "RadioButton": ("Gui.radio_button", "QRadioButton"),
        "GroupBox": ("Gui.group_box", "QGroupBox"),
        "Dial": ("Gui.dial", "QDial"),
        "ToolButton": ("Gui.tool_button", "QToolButton"),
        "PlainTextEdit": ("Gui.plain_text_edit", "QPlainTextEdit"),
        "DoubleSpinBox": ("GuiQt.double_spin_box", "QDoubleSpinBox"),
        "ScrollBar": ("GuiQt.scroll_bar", "QScrollBar"),
        "TimeEdit": ("GuiQt.time_edit", "QTimeEdit"),
        "DateTimeEdit": ("GuiQt.date_time_edit", "QDateTimeEdit"),
        "TextBrowser": ("GuiQt.text_browser", "QTextBrowser"),
        "FontComboBox": ("GuiQt.font_combo_box", "QFontComboBox"),
        "KeySequenceEdit": ("GuiQt.key_sequence_edit", "QKeySequenceEdit"),
        "CommandLinkButton": ("GuiQt.command_link_button", "QCommandLinkButton"),
        "Frame": ("GuiQt.frame", "QFrame"),
        "HorizontalLine": ("GuiQt.line", "QFrame"),
    }
    aliases = {"geometry_x": "x", "geometry_y": "y"}
    for type_name, (key, class_name) in mapping.items():
        old = COMPONENTS.get(type_name)
        if old is None:
            continue
        ports = list(old.ports)
        properties = list(old.properties)
        port_names = {item.name for item in ports}
        prop_names = {item.name for item in properties}
        for raw in property_definitions_for(key, class_name):
            raw_name = str(raw["name"])
            name = aliases.get(raw_name, raw_name)
            if name not in prop_names:
                ptype = str(raw.get("type") or "text")
                kind = {
                    "number": "real", "bool": "bool", "color": "color",
                    "font": "font", "style": "code", "code": "code",
                    "list": "multiline", "dict": "multiline",
                    "file": "str", "text": "multiline" if raw.get("multiline") else "str",
                }.get(ptype, "str")
                minimum = raw.get("minimum")
                maximum = raw.get("maximum")
                properties.append(PropertySpec(
                    name, str(raw.get("label") or name), kind,
                    raw.get("default"),
                    int(minimum) if minimum is not None else None,
                    int(maximum) if maximum is not None else None,
                    tuple(str(v) for v in (raw.get("choices") or ())),
                    str(raw.get("hint") or ""),
                ))
                prop_names.add(name)
            if name not in port_names:
                ports.append(PortSpec(
                    name, str(raw.get("label") or name), "data_in",
                    description=str(raw.get("hint") or "")
                ))
                port_names.add(name)
        COMPONENTS[type_name] = ComponentSpec(
            old.type_name, old.caption, old.category, old.color,
            ports=tuple(ports), properties=tuple(properties),
            description=old.description, source=old.source,
            implemented=old.implemented, visual=old.visual,
            subgroup=old.subgroup, hiasm_class=old.hiasm_class,
            hiasm_inherit=old.hiasm_inherit,
            hiasm_interfaces=old.hiasm_interfaces,
            hiasm_sub=old.hiasm_sub,
            hiasm_edit_class=old.hiasm_edit_class,
            support_status=old.support_status,
        )


_enrich_native_qt_components()


def _upgrade_components_v6() -> None:
    visual_names = ("Button","Label","LineEdit","TextEdit","CheckBox","ComboBox","ListWidget","ProgressBar","Slider","SpinBox","TableWidget","TableView","TreeWidget","DateEdit","Calendar","LCDNumber","RadioButton","GroupBox","Dial","ToolButton","PlainTextEdit","DoubleSpinBox","ScrollBar","TimeEdit","DateTimeEdit","TextBrowser","FontComboBox","KeySequenceEdit","CommandLinkButton","DialogButtonBox","Frame","HorizontalLine","Gauge","Speedometer","Tachometer","Thermometer","LevelMeter","LEDIndicator","Compass","BatteryIndicator","SignalIndicator","Sparkline","AnalogClock","Knob","LineChart","BarChart","PieChart","RadarChart","Oscilloscope","VUMeter","SevenSegmentDisplay","LEDMatrix","GridCanvas")
    common = (
        PortSpec("doShow","Показать","work_in"), PortSpec("doHide","Скрыть","work_in"),
        PortSpec("doEnable","Разрешить","work_in"), PortSpec("doDisable","Запретить","work_in"),
        PortSpec("doFocus","Передать фокус","work_in"), PortSpec("doRaise","На передний план","work_in"),
        PortSpec("doLower","На задний план","work_in"), PortSpec("doMove","Переместить","work_in"),
        PortSpec("doResize","Изменить размер","work_in"), PortSpec("doSetStyle","Изменить стиль","work_in"),
        PortSpec("X","Новая X","data_in"), PortSpec("Y","Новая Y","data_in"),
        PortSpec("Width","Новая ширина","data_in"), PortSpec("Height","Новая высота","data_in"),
        PortSpec("StyleValue","Новый QSS","data_in"),
        PortSpec("CurrentX","Текущая X","data_out"), PortSpec("CurrentY","Текущая Y","data_out"),
        PortSpec("CurrentWidth","Текущая ширина","data_out"), PortSpec("CurrentHeight","Текущая высота","data_out"),
        PortSpec("IsVisible","Видим","data_out"), PortSpec("IsEnabled","Доступен","data_out"),
    )
    extra_events = {
        "Button": (("onPressed","Нажата","event_out"),("onReleased","Отпущена","event_out"),("onToggle","Переключена","event_out")),
        "LineEdit": (("onEditingFinished","Ввод завершён","event_out"),("onSelection","Выделение","event_out")),
        "TextEdit": (("onCursor","Курсор","event_out"),("onSelection","Выделение","event_out")),
        "CheckBox": (("onClick","Нажатие","event_out"),("onToggle","Переключение","event_out")),
        "ComboBox": (("onTextChange","Изменение текста","event_out"),("onActivated","Активация","event_out")),
        "ListWidget": (("onClick","Щелчок","event_out"),("onDoubleClick","Двойной щелчок","event_out")),
        "Slider": (("onPressed","Нажат","event_out"),("onReleased","Отпущен","event_out"),("onMoved","Перемещение","event_out")),
        "SpinBox": (("onEditingFinished","Ввод завершён","event_out"),),
        "TableWidget": (("onClick","Щелчок ячейки","event_out"),("onDoubleClick","Двойной щелчок","event_out"),("onCellChange","Ячейка изменена","event_out")),
        "TreeWidget": (("onClick","Щелчок","event_out"),("onDoubleClick","Двойной щелчок","event_out")),
    }
    for name in visual_names:
        old=COMPONENTS[name]; ports=list(old.ports); names={p.name for p in ports}
        for port in common:
            if port.name not in names: ports.append(port); names.add(port.name)
        for raw in extra_events.get(name,()):
            if raw[0] not in names: ports.append(PortSpec(*raw)); names.add(raw[0])
        COMPONENTS[name]=ComponentSpec(old.type_name,old.caption,old.category,old.color,tuple(ports),old.properties,old.description,old.source,old.implemented,True,old.subgroup,old.hiasm_class,old.hiasm_inherit,old.hiasm_interfaces,old.hiasm_sub,old.hiasm_edit_class,old.support_status)
    # Bring the main window to the same level of completeness.
    old=COMPONENTS["Form"]; props=list(old.properties); pn={p.name for p in props}
    additions=(
        PropertySpec("minimum_width","Мин. ширина","int",240,0,3840),PropertySpec("minimum_height","Мин. высота","int",160,0,2160),
        PropertySpec("maximum_width","Макс. ширина","int",3840,1,10000),PropertySpec("maximum_height","Макс. высота","int",2160,1,10000),
        PropertySpec("viewport_width","Ширина окна на экране","int",1050,480,3840),PropertySpec("viewport_height","Высота окна на экране","int",650,320,2160),PropertySpec("scrollable","Прокручиваемое содержимое","bool",True),
        PropertySpec("center","Центрировать","bool",True),PropertySpec("frameless","Без рамки","bool",False),
        PropertySpec("background_color","Цвет фона","color","#F4F8FF"),PropertySpec("text_color","Цвет текста","color","#17243A"),
        PropertySpec("border_color","Цвет рамки","color","#477DC2"),PropertySpec("border_width","Толщина рамки","int",0,0,30),
        PropertySpec("border_radius","Скругление","int",0,0,100),PropertySpec("opacity","Прозрачность","real",1.0,0,1),
        PropertySpec("style","Дополнительный QSS","code",""),PropertySpec("font","Шрифт","font","Segoe UI,10,0,0,0,0"),
        PropertySpec("icon","Значок окна","str",""),
        PropertySpec("menu_bar","Строка меню","bool",False),
        PropertySpec(
            "menus","Меню и действия","table","[]",
            description=(
                "JSON-массив меню главного окна. Сохраняет вложенные меню, "
                "действия, разделители, горячие клавиши и флажки."
            ),
        ),
        PropertySpec("statusbar_enabled","Строка состояния","bool",True),
        PropertySpec("statusbar","Текст строки состояния","str","Готово"),
        PropertySpec("tool_tip","Подсказка","str",""),PropertySpec("accessible_name","Имя доступности","str","Главное окно"),
    )
    for prop in additions:
        if prop.name not in pn: props.append(prop); pn.add(prop.name)
    ports=list(old.ports); names={p.name for p in ports}
    window_ports=(PortSpec("doHide","Скрыть","work_in"),PortSpec("doSetTitle","Изменить заголовок","work_in"),PortSpec("doMinimize","Свернуть","work_in"),PortSpec("doMaximize","Развернуть","work_in"),PortSpec("doFullScreen","Полный экран","work_in"),PortSpec("onShow","Показано","event_out"),PortSpec("onHide","Скрыто","event_out"),PortSpec("Title","Новый заголовок","data_in"),PortSpec("CurrentTitle","Текущий заголовок","data_out"),PortSpec("CurrentWidth","Ширина","data_out"),PortSpec("CurrentHeight","Высота","data_out"))
    for port in window_ports:
        if port.name not in names: ports.append(port); names.add(port.name)
    COMPONENTS["Form"]=ComponentSpec(old.type_name,"Главное окно",old.category,old.color,tuple(ports),tuple(props),"Расширенное окно PySide6.",old.source,old.implemented,old.visual,old.subgroup,old.hiasm_class,old.hiasm_inherit,old.hiasm_interfaces,old.hiasm_sub,old.hiasm_edit_class,old.support_status)

_upgrade_components_v6()


def default_properties(type_name: str) -> dict[str, Any]:
    return {item.name: item.default for item in COMPONENTS[type_name].properties}


_PROPERTY_DATA_TYPES = {
    "int": "number",
    "real": "number",
    "bool": "bool",
    "str": "text",
    "multiline": "text",
    "choice": "text",
    "enum": "text",
    "color": "color",
    "font": "font",
}

_SEMANTIC_PORT_DATA_TYPES = {
    # Coordinates, dimensions and counters are unambiguously numeric.
    "x": "number", "y": "number",
    "width": "number", "height": "number",
    "currentx": "number", "currenty": "number",
    "currentwidth": "number", "currentheight": "number",
    "column": "number", "row": "number",
    "columncount": "number", "rowcount": "number",
    "count": "number", "index": "number", "currentindex": "number",
    "changedcells": "number", "clearedlines": "number",
    "interval": "number", "minimum": "number", "maximum": "number",
    "angle": "number", "radius": "number", "progress": "number",
    # Names that always carry readable text in the native runtime.
    "text": "text", "caption": "text", "title": "text",
    "currenttitle": "text", "error": "text", "path": "text",
    "file": "text", "folder": "text", "key": "text",
    "message": "text", "rowsjson": "text", "scenejson": "text",
    "exportpath": "text",
    # Stable boolean status outputs.
    "checked": "bool", "isvisible": "bool", "isenabled": "bool",
    "isautorepeat": "bool", "isalarm": "bool", "ok": "bool",
    "exists": "bool",
    # Domain-neutral collections used by the grid and list primitives.
    "grid": "list", "currentgrid": "list", "points": "list",
    "items": "list", "palette": "dict",
}

_COMPONENT_PORT_DATA_TYPES = {
    ("Math", "Result"): "number",
    ("Random", "Result"): "number",
    ("Counter", "Value"): "number",
    ("FormatStr", "Result"): "text",
    ("LineEdit", "Value"): "text",
    ("TextEdit", "Value"): "text",
    ("PlainTextEdit", "Value"): "text",
    ("TextBrowser", "Value"): "text",
    ("CheckBox", "State"): "bool",
    ("RadioButton", "State"): "bool",
    ("ComboBox", "Item"): "text",
    ("MouseInput", "Button"): "text",
    ("GridBatchWriter", "OffsetColumn"): "number",
    ("GridBatchWriter", "OffsetRow"): "number",
}


def infer_port_data_type(spec: ComponentSpec, port: PortSpec) -> str:
    """Infer only safe native port types; unknown values deliberately stay any."""
    if port.kind not in {"data_in", "data_out"}:
        return "any"
    declared = str(port.data_type or "any").strip().lower()
    if declared != "any":
        return declared
    name = port.name.strip().lower()
    explicit = _COMPONENT_PORT_DATA_TYPES.get((spec.type_name, port.name))
    if explicit:
        return explicit
    property_names = [name]
    for prefix in ("new", "current"):
        if name.startswith(prefix) and len(name) > len(prefix):
            property_names.append(name[len(prefix):])
    matching_property = next(
        (
            item for item in spec.properties
            if item.name.strip().lower() in property_names
        ),
        None,
    )
    if matching_property is not None:
        inferred = _PROPERTY_DATA_TYPES.get(matching_property.kind)
        if inferred:
            return inferred
    return _SEMANTIC_PORT_DATA_TYPES.get(name, "any")


def effective_ports(
    type_name: str, properties: dict[str, Any] | None = None
) -> tuple[PortSpec, ...]:
    """Return static and instance-specific HiAsm points.

    The original package stores count-driven points in ``[Type] Sub`` rather
    than ``[Methods]``.  They must therefore be rebuilt for every instance.
    """
    from hiasm_support import dynamic_port_names

    spec = COMPONENTS[type_name]
    values = default_properties(type_name)
    values.update(properties or {})
    result = [
        replace(port, data_type=infer_port_data_type(spec, port))
        for port in spec.ports
    ]
    if type_name == "UserContainer":
        raw = values.get("interface", [])
        for item in raw if isinstance(raw, list) else []:
            if isinstance(item, dict) and str(item.get("kind")) in {"work_in","event_out","data_in","data_out"}:
                result.append(PortSpec(
                    str(item.get("port")),
                    str(item.get("caption") or item.get("port")),
                    str(item.get("kind")),
                    description=str(
                        item.get("description")
                        or "Точка пользовательского контейнера."
                    ),
                    data_type=str(item.get("data_type") or "any"),
                ))
    elif type_name in {
        "ContainerDataInput", "ContainerDataOutput",
    }:
        proxy_type = str(values.get("data_type") or "any")
        result = [
            replace(port, data_type=proxy_type)
            if port.kind in {"data_in", "data_out"} else port
            for port in result
        ]
    existing = {port.name for port in result}
    for name, caption, kind in dynamic_port_names(spec.hiasm_sub, values):
        if name in existing:
            continue
        result.append(
            PortSpec(
                name,
                caption,
                kind,
                description=(
                    f"Динамическая точка HiAsm. Количество задаётся "
                    f"декларацией Sub: {spec.hiasm_sub}."
                ),
            )
        )
        existing.add(name)
    # 14.1: every effective port exposes useful built-in documentation.
    # Imported and legacy catalogs often omit tooltip text; keeping the
    # fallback here makes the editor help, passports and tests consistent.
    kind_help = {
        "work_in": "Вход действия",
        "event_out": "Выход события",
        "data_in": "Вход данных",
        "data_out": "Результат",
    }
    documented = []
    for port in result:
        if port.description.strip():
            documented.append(port)
            continue
        requirement = " Обязательное подключение." if port.required else ""
        text = f"{kind_help.get(port.kind, 'Порт')}: {port.caption or port.name}.{requirement}"
        documented.append(replace(port, description=text))
    return tuple(documented)
