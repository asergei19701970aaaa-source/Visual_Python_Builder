"""Эталонные событийные элементы NodeFlow 18.0.

Это не копия старого Delphi-кода HiAsm. Ноды фиксируют современную модель
методов, событий, ленивых данных, свойств и постоянного состояния.
"""
from __future__ import annotations

from python_library.nodes._base import flag, library, num, txt
from python_library.runtime import MethodResult


nd = library("EventCore", "0. Событийное ядро", color="#6d4f8d")


def p(name, ptype="any", default=None, label="", kind="data", **extra):
    return {
        "name": name, "type": ptype, "default": default,
        "label": label or name, "kind": kind, **extra,
    }


def _emit(name, payload=None, properties=None, state=None):
    return MethodResult(
        properties=dict(properties or {}),
        events=[(name, payload)],
        state=dict(state or {}),
    )


def _hub(ctx, payload):
    return MethodResult(events=[
        ("onEvent1", payload), ("onEvent2", payload), ("onEvent3", payload)])


@nd("Разветвитель событий",
    inputs=[p("doEvent", "any", label="Выполнить", kind="method")],
    outputs=[
        p("onEvent1", "any", label="Событие 1", kind="event"),
        p("onEvent2", "any", label="Событие 2", kind="event"),
        p("onEvent3", "any", label="Событие 3", kind="event"),
    ],
    tags=["hub", "события", "последовательно"],
    method_handlers={"doEvent": _hub})
def hub():
    """Синхронно вызывает три события сверху вниз."""


def _branch(ctx, payload):
    event = "onTrue" if flag(ctx.data("Condition")) else "onFalse"
    return _emit(event, payload)


@nd("Ветвление события",
    inputs=[
        p("doCompare", "any", label="Проверить", kind="method"),
        p("Condition", "bool", False, "Условие"),
    ],
    outputs=[
        p("onTrue", "any", label="Да", kind="event"),
        p("onFalse", "any", label="Нет", kind="event"),
    ],
    tags=["if", "ветвление"],
    method_handlers={"doCompare": _branch})
def branch(Condition=False):
    """Вызывает одно из двух событий по лениво запрошенному условию."""
    return bool(flag(Condition))


def _counter_next(ctx, payload):
    value = num(ctx.state.get("count", ctx.data("Initial")))
    value += num(ctx.data("Step"), 1)
    return _emit("onChange", value, {"Count": value}, {"count": value})


def _counter_reset(ctx, payload):
    value = num(ctx.data("Initial"))
    return _emit("onChange", value, {"Count": value}, {"count": value})


def _counter_value(ctx):
    return num(ctx.state.get("count", ctx.data("Initial")))


@nd("Счётчик",
    inputs=[
        p("doNext", "any", label="Следующее", kind="method"),
        p("doReset", "any", label="Сбросить", kind="method"),
        p("Initial", "number", 0, "Начальное значение"),
        p("Step", "number", 1, "Шаг"),
    ],
    outputs=[
        p("onChange", "number", label="Изменилось", kind="event"),
        p("Count", "number", label="Текущее значение", kind="property"),
    ],
    tags=["counter", "состояние"],
    method_handlers={"doNext": _counter_next, "doReset": _counter_reset},
    property_handlers={"Count": _counter_value})
def counter(Initial=0, Step=1):
    """Состояние хранится в экземпляре, а не в глобальном словаре."""
    return num(Initial)


def _message(ctx, payload):
    value = ctx.data("Text")
    return _emit(
        "onMessage", value, {"LastMessage": value}, {"last": value})


def _last_message(ctx):
    return ctx.state.get("last", "")


@nd("Сообщение",
    inputs=[
        p("doMessage", "any", label="Показать", kind="method"),
        p("Text", "text", "", "Текст"),
    ],
    outputs=[
        p("onMessage", "text", label="Показано", kind="event"),
        p("LastMessage", "text", label="Последний текст", kind="property"),
    ],
    tags=["message", "пример метода"],
    method_handlers={"doMessage": _message},
    property_handlers={"LastMessage": _last_message})
def message(Text=""):
    """Эталон действия; GUI-хост может заменить показ своим обработчиком."""
    return txt(Text)


def _calculate(ctx, payload):
    a, b = num(ctx.data("A")), num(ctx.data("B"))
    operation = txt(ctx.data("Operation"))
    try:
        if operation == "-":
            value = a - b
        elif operation == "*":
            value = a * b
        elif operation == "/":
            if b == 0:
                raise ZeroDivisionError("деление на ноль")
            value = a / b
        else:
            value = a + b
        return _emit(
            "onResult", value, {"Result": value}, {"result": value})
    except Exception as exc:
        return _emit("onError", str(exc))


def _calculated(ctx):
    return ctx.state.get("result", 0)


@nd("Вычисление по событию",
    inputs=[
        p("doCalc", "any", label="Вычислить", kind="method"),
        p("A", "number", 0), p("B", "number", 0),
        p("Operation", "text", "+", "Операция",
          choices=["+", "-", "*", "/"]),
    ],
    outputs=[
        p("onResult", "number", label="Результат", kind="event"),
        p("onError", "text", label="Ошибка", kind="event"),
        p("Result", "number", label="Последний результат", kind="property"),
    ],
    tags=["math", "event"],
    method_handlers={"doCalc": _calculate},
    property_handlers={"Result": _calculated})
def calculate(A=0, B=0, Operation="+"):
    """Входы A и B запрашиваются только при вызове doCalc."""
    return num(A) + num(B)


def _data_to_event(ctx, payload):
    value = ctx.data("Data")
    return _emit("onEvent", value, {"GetData": value}, {"value": value})


def _event_to_data(ctx):
    value = ctx.state.get("value", ctx.data("Data"))
    # Как в EventFromData: запрос нижней точки также вызывает событие.
    ctx.emit("onEvent", value)
    return value


@nd("Событие из данных",
    inputs=[
        p("doData", "any", label="Передать", kind="method"),
        p("Data", "any", None, "Данные"),
    ],
    outputs=[
        p("onEvent", "any", label="Событие", kind="event"),
        p("GetData", "any", label="Получить данные", kind="property"),
    ],
    tags=["EventFromData", "данные", "события"],
    method_handlers={"doData": _data_to_event},
    property_handlers={"GetData": _event_to_data})
def event_from_data(Data=None):
    """Преобразует синхронный запрос значения в событие и обратно."""
    return Data


def _timer_start(ctx, payload):
    interval = max(1, int(num(ctx.data("Interval"), 1000)))
    return _emit(
        "onState", True, {"Active": True, "IntervalValue": interval},
        {"active": True, "interval": interval})


def _timer_stop(ctx, payload):
    return _emit(
        "onState", False, {"Active": False}, {"active": False})


def _timer_tick(ctx, payload):
    if not ctx.state.get("active"):
        return MethodResult()
    return _emit("onTimer", payload)


@nd("Таймер (модель runtime)",
    inputs=[
        p("doStart", "any", label="Запустить", kind="method"),
        p("doStop", "any", label="Остановить", kind="method"),
        p("doTick", "any", label="Тик хоста", kind="method"),
        p("Interval", "number", 1000, "Интервал, мс"),
    ],
    outputs=[
        p("onTimer", "any", label="Таймер", kind="event"),
        p("onState", "bool", label="Состояние изменилось", kind="event"),
        p("Active", "bool", label="Активен", kind="property"),
        p("IntervalValue", "number", label="Интервал", kind="property"),
    ],
    tags=["timer", "state"],
    method_handlers={
        "doStart": _timer_start, "doStop": _timer_stop,
        "doTick": _timer_tick,
    })
def timer(Interval=1000):
    """Планирование делает GUI-хост; runtime хранит состояние и события."""
    return (False, max(1, int(num(Interval, 1000))))


def _button_caption(ctx, payload):
    value = txt(ctx.data("Caption"))
    return _emit(
        "onCaption", value, {"CurrentCaption": value}, {"caption": value})


def _button_enabled(ctx, payload):
    value = flag(ctx.data("Enabled"), True)
    return _emit(
        "onEnabled", value, {"IsEnabled": value}, {"enabled": value})


@nd("Кнопка (событийная модель)",
    inputs=[
        p("doCaption", "any", label="Задать текст", kind="method"),
        p("doEnabled", "any", label="Доступность", kind="method"),
        p("Caption", "text", "Кнопка", "Текст"),
        p("Enabled", "bool", True, "Доступна"),
    ],
    outputs=[
        p("onClick", "any", label="Нажатие", kind="event"),
        p("onCaption", "text", label="Текст изменён", kind="event"),
        p("onEnabled", "bool", label="Доступность изменена", kind="event"),
        p("CurrentCaption", "text", label="Текущий текст", kind="property"),
        p("IsEnabled", "bool", label="Доступна", kind="property"),
    ],
    tags=["button", "gui", "reference"],
    method_handlers={
        "doCaption": _button_caption, "doEnabled": _button_enabled})
def button_model(Caption="Кнопка", Enabled=True):
    """Независимая от Qt модель кнопки для runtime и тестов."""
    return (txt(Caption), flag(Enabled, True))


def _multi_in(ctx, payload):
    return _emit("onWork", payload)


@nd("Интерфейс контейнера",
    inputs=[
        p("doWork", "any", label="Внешний метод", kind="method"),
        p("Data", "any", None, "Внешние данные"),
    ],
    outputs=[
        p("onWork", "any", label="Внешнее событие", kind="event"),
        p("Value", "any", label="Внешнее свойство", kind="property"),
    ],
    tags=["MultiElement", "EditMulti", "container"],
    method_handlers={"doWork": _multi_in})
def multi_interface(Data=None):
    """Эталон четырёх независимых интерфейсов контейнера."""
    return Data


def _start(ctx, payload):
    return _emit("onStart", payload)


@nd("Запуск схемы",
    inputs=[p("doStart", "any", label="Запустить", kind="method")],
    outputs=[p("onStart", "any", label="Запуск", kind="event")],
    tags=["start", "entry"],
    method_handlers={"doStart": _start})
def start():
    """Явная точка входа для headless-схем и тестов."""