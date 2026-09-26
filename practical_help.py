"""Practical, action-oriented help for Visual Python Builder.

This module is deliberately independent from Qt. The canvas, palette,
property panel and diagnostics can use the same explanations. It avoids
explaining a point merely as an "input" or an "output". Instead, each point
is described by the effect a creator gets from connecting it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from components import COMPONENTS, effective_ports


@dataclass(frozen=True)
class HelpEntry:
    """A complete explanation shown beside a selected item."""

    title: str
    purpose: str
    when_to_use: str
    action: str
    result: str
    next_step: str
    example: str
    common_mistake: str
    advanced_note: str = ""


_PORT_ACTIONS = {
    "work_in": (
        "Запускает это действие.",
        "Протяните сюда линию от действия, после которого этот шаг должен выполниться.",
    ),
    "event_out": (
        "Сообщает, что это действие уже произошло.",
        "Протяните линию к следующему действию, которое должно начаться после него.",
    ),
    "data_in": (
        "Принимает значение для работы элемента.",
        "Подайте сюда результат элемента, который создаёт нужный текст, число, выбор или список.",
    ),
    "data_out": (
        "Отдаёт текущее или вычисленное значение.",
        "Протяните линию к настройке или действию, которому это значение требуется.",
    ),
}

_COMPONENT_OVERRIDES: dict[str, dict[str, str]] = {
    "Start": {
        "purpose": "Начинает сценарий при запуске программы.",
        "when": "Используйте один раз для действий, которые должны случиться сразу после старта.",
        "example": "Подключите «Запуск» к показу главного окна или к загрузке начальных данных.",
        "mistake": "Не используйте его для реакции на нажатие кнопки. Для этого начните линию от самой кнопки.",
    },
    "Button": {
        "purpose": "Показывает кнопку, по которой человек запускает действие.",
        "when": "Используйте, когда программа должна ждать явного нажатия: отправить, посчитать, сохранить, начать игру.",
        "example": "Соедините «Нажатие» с «Вычислить», а результат вычисления подайте в надпись.",
        "mistake": "Текст кнопки сам по себе ничего не запускает. Нужна линия от «Нажатие» к нужному действию.",
    },
    "LineEdit": {
        "purpose": "Даёт человеку место для ввода короткого текста или числа.",
        "when": "Используйте для имени, суммы, поиска, пароля или другого одного значения.",
        "example": "Подайте «Текст» в вычисление или в форматирование сообщения после нажатия кнопки.",
        "mistake": "Не ожидайте автоматического расчёта. Соедините «Изменение» или кнопку с действием обработки.",
    },
    "Label": {
        "purpose": "Показывает текст, который формирует программа.",
        "when": "Используйте для результата, подсказки, статуса или сообщения об ошибке.",
        "example": "Подайте сформированную строку в «Текст», затем запустите «Установить текст».",
        "mistake": "Не используйте надпись для ввода. Для ввода добавьте «Поле ввода».",
    },
    "IfElse": {
        "purpose": "Выбирает один из двух путей по заданному сравнению.",
        "when": "Используйте, когда результат должен зависеть от условия: сумма больше нуля, поле заполнено, пароль верен.",
        "example": "После «Сравнить» ведите «Да» к сообщению об успехе, а «Нет» к подсказке, что исправить.",
        "mistake": "Сначала задайте оба сравниваемых значения. Пустые значения часто дают неожиданный путь.",
    },
    "Memory": {
        "purpose": "Хранит значение, чтобы использовать его позже.",
        "when": "Используйте для счётчика, выбранного имени, результата предыдущего шага или текущего состояния игры.",
        "example": "Запишите число после вычисления, затем подайте «Значение» в надпись или следующее вычисление.",
        "mistake": "Память не меняется сама. Соедините действие с «Записать».",
    },
    "Timer": {
        "purpose": "Повторяет действие через заданные промежутки времени.",
        "when": "Используйте для часов, анимации, периодической проверки или шага игры.",
        "example": "Подключите «Срабатывание» к обновлению счётчика и показу нового значения.",
        "mistake": "Проверьте интервал. Значение задаётся в миллисекундах: 1000 означает одну секунду.",
    },
    "Math": {
        "purpose": "Вычисляет сумму, разность, произведение, деление или другую выбранную операцию.",
        "when": "Используйте, когда программе нужно получить новое число из двух значений.",
        "example": "Подайте два числа в «Первое число» и «Второе число», затем используйте «Результат» в надписи.",
        "mistake": "При делении второе число не должно быть нулём.",
    },
    "FormatStr": {
        "purpose": "Собирает понятный текст из постоянных слов и значений программы.",
        "when": "Используйте для сообщений, чеков, подписей, статуса заказа и результатов расчёта.",
        "example": "Шаблон «Итого: {0} руб.» вместе с числом создаёт готовую надпись для окна.",
        "mistake": "Номер в фигурных скобках должен совпадать с поданным значением: {0} для первого, {1} для второго.",
    },
}


def _default_component_help(type_name: str) -> HelpEntry:
    spec = COMPONENTS[type_name]
    title = spec.caption
    description = spec.description.strip()
    purpose = description or f"Добавляет в программу элемент «{title}»."
    return HelpEntry(
        title=title,
        purpose=purpose,
        when_to_use=f"Используйте «{title}», когда это действие или элемент нужен в вашей программе.",
        action="Выберите элемент, настройте видимые свойства и соедините его с соседними шагами сценария.",
        result=f"Программа использует «{title}» при запуске созданного проекта.",
        next_step="Выберите одну из точек элемента. Справка для точки покажет, что можно сделать дальше.",
        example=f"Добавьте «{title}» на схему и проверьте результат запуском программы.",
        common_mistake="Не оставляйте элемент без связи, если он должен реагировать на действие или передавать результат дальше.",
        advanced_note=f"Технический тип: {spec.type_name}.",
    )


def component_help(type_name: str) -> HelpEntry:
    """Return a full practical explanation for a component."""
    entry = _default_component_help(type_name)
    override = _COMPONENT_OVERRIDES.get(type_name, {})
    return HelpEntry(
        title=entry.title,
        purpose=override.get("purpose", entry.purpose),
        when_to_use=override.get("when", entry.when_to_use),
        action=override.get("action", entry.action),
        result=override.get("result", entry.result),
        next_step=override.get("next", entry.next_step),
        example=override.get("example", entry.example),
        common_mistake=override.get("mistake", entry.common_mistake),
        advanced_note=entry.advanced_note,
    )


def port_help(type_name: str, port_name: str) -> HelpEntry:
    """Explain exactly what a connection point does and how to use it."""
    spec = COMPONENTS[type_name]
    port = next(item for item in effective_ports(type_name) if item.name == port_name)
    action, next_step = _PORT_ACTIONS.get(port.kind, ("Используется этим элементом.", "Проверьте совместимые точки."))
    detail = port.description.strip() or action
    data_note = ""
    if port.kind in {"data_in", "data_out"}:
        data_note = f" Здесь используется значение типа: {port.data_type}."
    required = " Эта точка обязательна для работы элемента." if port.required else ""
    return HelpEntry(
        title=f"{spec.caption}: {port.caption}",
        purpose=detail + data_note,
        when_to_use=f"Используйте, когда нужно {port.caption.lower()} в работе «{spec.caption}».",
        action=action + required,
        result=f"После соединения «{port.caption}» участвует в поведении элемента «{spec.caption}».",
        next_step=next_step,
        example=f"Выберите подходящую линию на схеме и соедините её с точкой «{port.caption}».",
        common_mistake="Не соединяйте действие со значением. Если линия не принимается, выберите подсказанный совместимый элемент.",
        advanced_note=f"Техническое имя: {port.name}; категория связи: {port.kind}.",
    )


def property_help(type_name: str, property_name: str) -> HelpEntry:
    """Explain a setting in terms of an observable change."""
    spec = COMPONENTS[type_name]
    prop = next(item for item in spec.properties if item.name == property_name)
    description = prop.description.strip() or f"Меняет настройку «{prop.caption}» у элемента «{spec.caption}»."
    range_note = ""
    if prop.minimum is not None or prop.maximum is not None:
        range_note = f" Допустимый диапазон: от {prop.minimum if prop.minimum is not None else 'без минимума'} до {prop.maximum if prop.maximum is not None else 'без максимума'}."
    return HelpEntry(
        title=f"{spec.caption}: {prop.caption}",
        purpose=description + range_note,
        when_to_use=f"Меняйте эту настройку, когда хотите изменить поведение или вид «{spec.caption}».",
        action=f"Выберите нужное значение. Значение по умолчанию: {prop.default!r}.",
        result=f"Следующий запуск применит новое значение «{prop.caption}».",
        next_step="Запустите проект и проверьте видимый результат изменения.",
        example=f"Оставьте значение по умолчанию, если ещё не знаете, как эта настройка влияет на программу.",
        common_mistake="Не меняйте несколько незнакомых настроек одновременно. Иначе трудно понять причину результата.",
        advanced_note=f"Техническое имя: {prop.name}; вид значения: {prop.kind}.",
    )


def render_help(entry: HelpEntry, show_advanced: bool = False) -> str:
    """Render a help entry for plain-text panes and tooltips."""
    lines = [
        entry.title,
        "",
        "Что делает: " + entry.purpose,
        "Когда применять: " + entry.when_to_use,
        "Как использовать: " + entry.action,
        "Что получится: " + entry.result,
        "Следующий шаг: " + entry.next_step,
        "Пример: " + entry.example,
        "Частая ошибка: " + entry.common_mistake,
    ]
    if show_advanced and entry.advanced_note:
        lines.extend(("", "Для расширенного режима: " + entry.advanced_note))
    return "\n".join(lines)


def audit_help_coverage() -> list[str]:
    """Return missing-help problems for release checks and tests."""
    problems: list[str] = []
    for type_name, spec in COMPONENTS.items():
        if not render_help(component_help(type_name)).strip():
            problems.append(f"{type_name}: нет справки элемента")
        for port in effective_ports(type_name):
            if not render_help(port_help(type_name, port.name)).strip():
                problems.append(f"{type_name}.{port.name}: нет справки точки")
        for prop in spec.properties:
            if not render_help(property_help(type_name, prop.name)).strip():
                problems.append(f"{type_name}.{prop.name}: нет справки настройки")
    return problems
