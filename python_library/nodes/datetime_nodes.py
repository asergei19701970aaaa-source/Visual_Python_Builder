"""Дата и время."""
import datetime as dt

from python_library.nodes._base import library, num, txt

nd = library("Date", "6. Дата и время", color="#4a5f7a")


@nd("Сейчас", inputs=[{"name": "format", "type": "text",
                         "default": "%d.%m.%Y %H:%M:%S"}],
    outputs=[("text", "text"), ("timestamp", "number")],
    tags=["now", "время"])
def now(format):
    """Текущая дата и время."""
    moment = dt.datetime.now()
    return moment.strftime(txt(format) or "%d.%m.%Y %H:%M:%S"), moment.timestamp()


@nd("Собрать дату",
    inputs=[("year", "number", 2026), ("month", "number", 1),
            ("day", "number", 1)],
    outputs=[("date", "text")], tags=["date", "дата"])
def make_date(year, month, day):
    """Собирает дату в формате ГГГГ-ММ-ДД."""
    d = dt.date(int(num(year, 2026)), max(1, min(12, int(num(month, 1)))),
                max(1, min(31, int(num(day, 1)))))
    return d.isoformat()


@nd("Разобрать дату",
    inputs=[("value", "text", "2026-01-01"),
            {"name": "format", "type": "text", "default": "%Y-%m-%d"}],
    outputs=[("year", "number"), ("month", "number"), ("day", "number"),
             ("weekday", "text")],
    tags=["parse", "дата"])
def parse_date(value, format):
    """Разбирает текстовую дату на части."""
    names = ["понедельник", "вторник", "среда", "четверг",
             "пятница", "суббота", "воскресенье"]
    moment = dt.datetime.strptime(txt(value), txt(format) or "%Y-%m-%d")
    return (float(moment.year), float(moment.month), float(moment.day),
            names[moment.weekday()])


@nd("Формат даты",
    inputs=[("value", "text", "2026-01-01"),
            {"name": "input_format", "type": "text", "default": "%Y-%m-%d"},
            {"name": "output_format", "type": "text", "default": "%d.%m.%Y"}],
    outputs=[("text", "text")], tags=["format", "strftime"])
def format_date(value, input_format, output_format):
    """Переводит дату из одного формата в другой."""
    moment = dt.datetime.strptime(txt(value), txt(input_format) or "%Y-%m-%d")
    return moment.strftime(txt(output_format) or "%d.%m.%Y")


@nd("Сдвинуть дату",
    inputs=[("value", "text", "2026-01-01"), ("days", "number", 1),
            ("hours", "number", 0)],
    outputs=[("date", "text")], tags=["shift", "timedelta"])
def shift_date(value, days, hours):
    """Прибавляет дни и часы к дате."""
    base = txt(value) or dt.date.today().isoformat()
    try:
        moment = dt.datetime.fromisoformat(base)
    except ValueError:
        raise ValueError("Ожидается дата в виде 2026-01-01 или 2026-01-01T10:00")
    moment += dt.timedelta(days=num(days, 1), hours=num(hours))
    return moment.isoformat(sep=" ")


@nd("Разница дат",
    inputs=[("first", "text", "2026-01-01"), ("second", "text", "2026-12-31")],
    outputs=[("days", "number"), ("hours", "number")], tags=["diff"])
def date_diff(first, second):
    """Сколько дней и часов между датами."""
    a = dt.datetime.fromisoformat(txt(first))
    b = dt.datetime.fromisoformat(txt(second))
    delta = b - a
    return float(delta.days), delta.total_seconds() / 3600.0


@nd("Метка времени → текст",
    inputs=[("timestamp", "number", 0),
            {"name": "format", "type": "text", "default": "%d.%m.%Y %H:%M"}],
    outputs=[("text", "text")], tags=["timestamp"])
def from_timestamp(timestamp, format):
    """Превращает unix-время в текст."""
    moment = dt.datetime.fromtimestamp(num(timestamp))
    return moment.strftime(txt(format) or "%d.%m.%Y %H:%M")


@nd("Секунды → часы:минуты", inputs=[("seconds", "number", 3600)],
    outputs=[("text", "text")], tags=["duration", "длительность"])
def duration(seconds):
    """Форматирует длительность как ЧЧ:ММ:СС."""
    total = int(abs(num(seconds, 0)))
    return f"{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}"