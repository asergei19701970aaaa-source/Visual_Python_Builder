"""Понятные правила соединения портов и подбор прозрачных адаптеров."""
from __future__ import annotations

from dataclasses import dataclass


_TYPE_ALIASES = {
    "": "any",
    "object": "any",
    "variant": "any",
    "str": "text",
    "string": "text",
    "integer": "number",
    "int": "number",
    "float": "number",
    "real": "number",
    "boolean": "bool",
    "flag": "bool",
}

_TYPE_NAMES = {
    "any": "любые данные",
    "text": "текст",
    "number": "число",
    "bool": "да/нет",
    "list": "список",
    "dict": "словарь",
    "file": "файл или путь",
    "color": "цвет",
}

_CONVERTERS = {
    "number": ("Python::Data.to_number", "В число"),
    "text": ("Python::Data.to_text", "В текст"),
    "bool": ("Python::Data.to_bool", "В флаг"),
    "list": ("Python::Data.to_list", "В список"),
    "dict": ("Python::Data.to_dict", "В словарь"),
    "color": ("Python::Data.to_color", "В цвет"),
    "file": ("Python::Data.to_file", "В путь к файлу"),
}


@dataclass(frozen=True)
class ConnectionAdvice:
    allowed: bool
    message: str
    adapter_type: str | None = None
    adapter_caption: str = ""

    @property
    def needs_adapter(self) -> bool:
        return bool(self.adapter_type)


def normalize_data_type(value: str | None) -> str:
    raw = str(value or "").strip().lower()
    return _TYPE_ALIASES.get(raw, raw or "any")


def data_type_name(value: str | None) -> str:
    value = normalize_data_type(value)
    return _TYPE_NAMES.get(value, value)


def advise_connection(
    source_kind: str,
    target_kind: str,
    source_type: str = "any",
    target_type: str = "any",
    *,
    same_node: bool = False,
) -> ConnectionAdvice:
    """Explain whether two ports connect and which general adapter can help."""
    if same_node:
        return ConnectionAdvice(
            False,
            "Нельзя соединить точки одной и той же ноды: получится скрытая петля.",
        )
    if source_kind == "event_out" and target_kind == "work_in":
        return ConnectionAdvice(True, "Событие запускает действие.")
    if source_kind == "data_out" and target_kind == "data_in":
        source_type = normalize_data_type(source_type)
        target_type = normalize_data_type(target_type)
        if (
            source_type == target_type
            or "any" in {source_type, target_type}
        ):
            return ConnectionAdvice(True, "Типы данных совместимы.")
        converter = _CONVERTERS.get(target_type)
        if converter:
            return ConnectionAdvice(
                False,
                (
                    f"Здесь получаются данные типа «{data_type_name(source_type)}», "
                    f"а следующей ноде нужен тип «{data_type_name(target_type)}»."
                ),
                adapter_type=converter[0],
                adapter_caption=converter[1],
            )
        return ConnectionAdvice(
            False,
            (
                f"Типы данных различаются: «{data_type_name(source_type)}» → "
                f"«{data_type_name(target_type)}». Подходящего безопасного "
                "преобразователя пока нет."
            ),
        )
    if source_kind == "event_out":
        return ConnectionAdvice(
            False,
            "Это событие (правая точка). Его можно соединить только со входом "
            "действия слева, а не со входом данных сверху.",
        )
    if source_kind == "data_out":
        return ConnectionAdvice(
            False,
            "Это результат с данными (нижняя точка). Его можно соединить только "
            "со входом данных сверху, а не со входом действия слева.",
        )
    return ConnectionAdvice(
        False,
        "Связь нужно начинать с выхода: события справа или результата снизу.",
    )


def connection_passport(
    source_node: str,
    source_port: str,
    source_kind: str,
    source_type: str,
    target_node: str,
    target_port: str,
    target_kind: str,
    target_type: str,
) -> str:
    """Return a compact human-readable description of one saved wire."""
    advice = advise_connection(
        source_kind, target_kind, source_type, target_type
    )
    signal = (
        "Событие → действие"
        if source_kind == "event_out" else "Передача данных"
    )
    lines = [
        signal,
        f"Откуда: {source_node} · {source_port}",
        f"Куда: {target_node} · {target_port}",
    ]
    if source_kind == "data_out":
        lines.append(
            f"Тип: {data_type_name(source_type)} → "
            f"{data_type_name(target_type)}"
        )
    if advice.allowed:
        lines.append("Совместимость: прямое соединение")
    elif advice.needs_adapter:
        lines.append(
            f"Совместимость: нужен преобразователь "
            f"«{advice.adapter_caption}»"
        )
    else:
        lines.append(f"Проблема: {advice.message}")
    return "\n".join(lines)