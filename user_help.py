"""Понятная справка для пользователя без опыта программирования."""
from __future__ import annotations

from typing import Any

from components import COMPONENTS, ComponentSpec, effective_ports
from point_help import point_help


KIND_NAMES = {
    "work_in": "Действие — вход слева",
    "event_out": "Событие — выход справа",
    "data_in": "Данные — вход сверху",
    "data_out": "Результат — выход снизу",
}

DATA_TYPE_NAMES = {
    "any": "любые данные",
    "text": "текст",
    "number": "число",
    "bool": "да / нет",
    "list": "список",
    "dict": "словарь",
    "file": "файл или путь",
    "color": "цвет",
}

PROPERTY_KIND_NAMES = {
    "str": "текст",
    "multiline": "многострочный текст",
    "code": "структурированное значение",
    "int": "целое число",
    "real": "число",
    "bool": "да / нет",
    "choice": "выбор из списка",
    "enum": "выбор из списка",
    "color": "цвет",
    "font": "шрифт",
}


def component_search_text(spec: ComponentSpec) -> str:
    """Единый поисковый индекс палитры, включая человеческие описания."""
    values = [
        spec.caption,
        spec.type_name,
        spec.category,
        spec.subgroup,
        spec.description,
        spec.source,
        spec.support_status,
    ]
    for prop in spec.properties:
        values.extend(
            [prop.name, prop.caption, prop.kind, prop.description, str(prop.default)]
        )
        values.extend(str(option) for option in prop.options)
    for port in effective_ports(spec.type_name):
        values.extend(
            [
                port.name,
                port.caption,
                port.kind,
                port.data_type,
                KIND_NAMES.get(port.kind, ""),
                port.description,
            ]
        )
    return " ".join(str(value) for value in values if str(value).strip()).lower()


def node_instance_search_text(model: dict[str, Any]) -> str:
    """Search index for an installed node, including its current values."""
    spec = COMPONENTS.get(str(model.get("type", "")))
    values = [
        str(model.get("id", "")),
        str(model.get("type", "")),
    ]
    if spec is not None:
        values.append(component_search_text(spec))
    properties = model.get("properties", {})
    if isinstance(properties, dict):
        for name, value in properties.items():
            if str(name).startswith("_") or name == "subgraph":
                continue
            text = str(value)
            values.extend((str(name), text[:500]))
    return " ".join(
        value for value in values if value.strip()
    ).lower()


def node_instance_label(model: dict[str, Any]) -> str:
    """Human label that distinguishes several instances of the same node."""
    spec = COMPONENTS.get(str(model.get("type", "")))
    caption = spec.caption if spec is not None else str(model.get("type", "Нода"))
    properties = model.get("properties", {})
    name = (
        str(properties.get("name", "")).strip()
        if isinstance(properties, dict) else ""
    )
    return f"{caption} · {name}" if name and name != caption else caption


def project_node_records(
    project: dict[str, Any],
    path_names: tuple[str, ...] = (),
    path_ids: tuple[str, ...] = (),
    *,
    max_depth: int = 32,
) -> list[dict[str, Any]]:
    """Flatten nested container nodes while preserving an openable path."""
    records: list[dict[str, Any]] = []
    if not isinstance(project, dict) or max_depth < 0:
        return records
    for model in project.get("nodes", []):
        if not isinstance(model, dict):
            continue
        records.append({
            "model": model,
            "path_names": path_names,
            "path_ids": path_ids,
        })
        if str(model.get("type")) != "UserContainer":
            continue
        properties = model.get("properties", {})
        inner = (
            properties.get("subgraph")
            if isinstance(properties, dict) else None
        )
        if not isinstance(inner, dict):
            continue
        title = node_instance_label(model)
        records.extend(project_node_records(
            inner,
            path_names + (title,),
            path_ids + (str(model.get("id", "")),),
            max_depth=max_depth - 1,
        ))
    return records


def _value_text(value: Any) -> str:
    if value is True:
        return "Да"
    if value is False:
        return "Нет"
    if value in (None, ""):
        return "не задано"
    text = str(value)
    return text if len(text) <= 100 else text[:97] + "…"


def _property_help(prop) -> str:
    details = [PROPERTY_KIND_NAMES.get(prop.kind, prop.kind)]
    if prop.options:
        details.append("варианты: " + ", ".join(str(item) for item in prop.options))
    if prop.minimum is not None or prop.maximum is not None:
        details.append(
            f"диапазон: {prop.minimum if prop.minimum is not None else 'без минимума'}"
            f" … {prop.maximum if prop.maximum is not None else 'без максимума'}"
        )
    description = prop.description.strip() or (
        f"Настраивает «{prop.caption.lower()}». "
        "Изменение сразу сохраняется в проекте."
    )
    return (
        f"• {prop.caption} [{prop.name}] — {description}\n"
        f"  Тип: {'; '.join(details)}. По умолчанию: {_value_text(prop.default)}."
    )


def format_component_help(type_name: str) -> str:
    """Полная практическая справка вместо окна с одним счётчиком точек."""
    spec = COMPONENTS[type_name]
    ports = effective_ports(type_name)
    lines = [
        spec.caption,
        "=" * len(spec.caption),
        "",
        spec.description.strip()
        or "Универсальный элемент схемы. Его назначение определяется точками и свойствами ниже.",
        "",
        f"Раздел: {spec.category}"
        + (f" → {spec.subgroup}" if spec.subgroup else ""),
        f"Техническое имя: {spec.type_name}",
        f"Поддержка: {spec.support_status}. Источник: {spec.source}.",
        "",
        "КАК ЧИТАТЬ НОДУ",
        "Слева находятся команды, которые запускают действие. Справа — события, "
        "возникающие после действия. Сверху нода получает данные, снизу отдаёт результат.",
        "",
        "ТОЧКИ ПОДКЛЮЧЕНИЯ",
    ]
    if not ports:
        lines.append("• У этой ноды нет точек подключения: она настраивается свойствами.")
    for port in ports:
        required = " Обязательное подключение." if port.required else ""
        type_text = (
            f"Тип: {DATA_TYPE_NAMES.get(port.data_type, port.data_type)}. "
            if port.kind in {"data_in", "data_out"} else ""
        )
        lines.append(
            f"• {port.caption} [{port.name}]\n"
            f"  {KIND_NAMES.get(port.kind, port.kind)}. "
            f"{type_text}"
            f"{point_help(type_name, port.name, port.caption, port.kind, port.description)}"
            f"{required}"
        )
    lines.extend(["", "СВОЙСТВА"])
    if not spec.properties:
        lines.append("• Настраиваемых свойств нет.")
    else:
        lines.extend(_property_help(prop) for prop in spec.properties)
    lines.extend(
        [
            "",
            "ПРОВЕРКА",
            "После соединения нод нажмите F7. Двойной щелчок по найденной ошибке "
            "покажет проблемный элемент. F5 запускает программу, F6 — пошаговую отладку.",
        ]
    )
    return "\n".join(lines)


BEGINNER_GUIDE = """КАК СОБИРАТЬ ПРОГРАММУ ИЗ ОБЩИХ НОД
========================================

1. Сначала опишите поведение словами
Разделите замысел на четыре части:
• события: что запускает работу;
• состояние: что программа должна помнить;
• правила: как состояние меняется;
• отображение: что увидит пользователь.

2. Подберите общие ноды
• События: Старт, Таймер, Клавиатура, Мышь, Кнопка.
• Состояние: Память, Список данных, Словарь, Двумерное поле.
• Правила: Условие, Математика, Геометрия 2D, циклы, шлюз событий.
• Отображение: обычные элементы формы, Холст двумерного поля и Холст приборной панели.

3. Собирайте маленькими работающими шагами
Не стройте сразу всю схему. Соедините одно событие с одним действием, нажмите
F7, затем F5. После успешной проверки добавляйте следующий законченный кусок.

4. Используйте контейнеры
Когда фрагмент заработал, выделите его и упакуйте в пользовательский контейнер.
Называйте контейнер по задаче: «Ввод», «Движение», «Проверка столкновения»,
«Очистка линий», «Отрисовка». Это не специальная нода: внутри остаются обычные
универсальные элементы, которые можно открыть и изменить.
Готовый контейнер сохраните через его контекстное меню. Он появится на вкладке
«Контейнеры» в выбранной категории и подкатегории. Там же находятся встроенные
учебные решения, которые можно открыть и разобрать по частям.

5. Правило соединений
Оранжевая цепочка отвечает на вопрос «когда и что выполнить». Синяя цепочка
отвечает на вопрос «какое значение использовать». Не пытайтесь заменить
событие данными или данные событием. Пока вы тянете нить, зелёная обводка
означает прямое соединение, янтарная — соединение через преобразователь.
Если вместо текста нужно число или флаг, Builder объяснит различие и предложит
добавить обычную видимую ноду-преобразователь. Без вашего согласия схема не
изменится.
Чтобы не искать следующую ноду в большой палитре, отпустите новую нить на
пустом месте. Откроется поиск только по совместимым нодам и их подходящим
точкам. После выбора Builder поставит ноду и соединит её сам. Этот быстрый
выбор не срабатывает при переподключении старой нити: там отпускание на пустом
месте, как и раньше, удаляет связь.
Для внешних точек собственного контейнера задавайте тип данных в его паспорте.
Используйте «Любые данные» только когда контейнер действительно может принимать
разные значения. Точный тип помогает Builder раньше обнаружить ошибку и
предложить правильную следующую ноду.
Если типы не совпали, соглашайтесь на преобразователь только после проверки его
свойств. У нод «В список» и «В словарь» задаются разделители и способ чтения
словаря; «В цвет» проверяет формат и диапазон каналов; «В путь к файлу» не
проверяет существование файла, а только формирует путь.
В большой схеме задержите указатель над нитью: паспорт покажет обе ноды, обе
точки и тип передаваемых данных. Щёлкните нить правой кнопкой, чтобы открыть
полный паспорт или мгновенно перейти к её началу либо концу.
Нажмите Ctrl+F, если нужно найти уже установленную ноду. Ищите по видимому
названию, имени экземпляра, разделу или значению свойства. Двойной щелчок по
результату переносит холст к ноде. Снимите флажок поиска внутри контейнеров,
если хотите видеть результаты только на текущем уровне.
Включите «Искать внутри вложенных контейнеров», чтобы искать сразу во всём
проекте. В колонке «Путь» видно расположение результата. При активации Builder
сохранит открытый уровень, сам пройдёт через нужные контейнеры и покажет ноду.
Текущий путь всегда виден над холстом, даже если навигатор закрыт. Нажмите
«На уровень выше» для обычного возврата или выберите любую хлебную крошку,
чтобы сразу вернуться к нужному родителю. Изменения внутри контейнера перед
переходом сохраняются автоматически.
Если создать внешнюю точку, протянув нить к рамке контейнера, тип данных
наследуется автоматически. Наведите указатель на список типов в паспорте, чтобы
увидеть источник. Меняйте тип вручную только осознанно: проверка схемы сообщит,
если он перестал соответствовать внутреннему соединению.

6. Отладка большой схемы
Проверяйте каждый контейнер отдельно. Ставьте точки останова на его вход и
выход, запускайте F6 и смотрите реальные значения в панели «Отладка».
Перед каждым запуском нажимайте F7. В панели «Проверка схемы» сообщение
«Что сделать» объясняет исправление. Двойной щелчок по строке переносит к
нужной ноде. Особое внимание обращайте на цепочки, которые соединены между
собой, но не доходят назад до «Старт», кнопки, клавиатуры или другого
источника события.
"""


DYNAMIC_GAME_GUIDE = """КАРТА ДИНАМИЧЕСКОЙ ИГРЫ ИЗ ОБЩИХ НОД
=======================================

Это не готовая игровая нода, а план из повторно используемых блоков.

СОСТОЯНИЕ
• «Двумерное поле» хранит клетки игрового поля.
• «Память» или «Словарь» хранит координаты, скорость, счёт и режим паузы.
• «Список данных» хранит фигуру как набор относительных координат.

ВВОД И ВРЕМЯ
• «Клавиатура» выдаёт нажатую клавишу.
• «Условие» или «Шлюз событий» выбирает движение, поворот и паузу.
• «Таймер» создаёт игровой такт. Начните с 300–500 мс, затем ускоряйте.

ПРАВИЛА
• «Математика» вычисляет новые координаты.
• «Геометрия 2D» и чтение ячеек проверяют границы и столкновения.
• «Двумерное поле» записывает остановившуюся фигуру и удаляет полные строки.
• «Цикл с повторением» или «Для каждого» обходит клетки и части фигуры.

ОТОБРАЖЕНИЕ
• «Холст двумерного поля» напрямую принимает выход Grid ноды
  «Двумерное поле» — формировать JSON-сцену не требуется.
• Соедините onChange поля с «Показать поле», а Grid — с верхним входом «Поле».
• «Щелчок по клетке» возвращает столбец, строку и значение клетки.
• После изменения состояния обновляйте поле и счёт.
• Цвета храните отдельно от правил — тогда оформление можно менять без
  изменения игровой логики.

РЕКОМЕНДУЕМЫЕ КОНТЕЙНЕРЫ
1. Создать фигуру.
2. Проверить позицию.
3. Сдвинуть или повернуть.
4. Зафиксировать на поле.
5. Удалить заполненные строки.
6. Перерисовать поле и панель.

Начните с примера «15 — Холст двумерного поля»: он закрашивает клетки щелчком
и показывает полный цикл событие → изменение состояния → перерисовка. Затем
добейтесь движения одного квадрата, фигуры из нескольких клеток, столкновений
и только после этого добавляйте очки и оформление.
"""