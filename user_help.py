"""User-facing help, search indexes and project navigation helpers."""
from __future__ import annotations

from typing import Any

from components import COMPONENTS, ComponentSpec, effective_ports
from practical_help import component_help, render_help


KIND_NAMES = {
    "work_in": "действие, которое можно запустить",
    "event_out": "момент, после которого можно продолжить сценарий",
    "data_in": "место для значения",
    "data_out": "готовое значение для следующего шага",
}


def component_search_text(spec: ComponentSpec) -> str:
    """Search text includes visible names, purpose and usable connection terms."""
    values: list[Any] = [
        spec.caption, spec.type_name, spec.category, spec.subgroup,
        spec.description, spec.source, spec.support_status,
    ]
    entry = component_help(spec.type_name)
    values.extend((entry.purpose, entry.when_to_use, entry.example))
    for prop in spec.properties:
        values.extend((prop.name, prop.caption, prop.description, prop.default))
        values.extend(prop.options)
    for port in effective_ports(spec.type_name):
        values.extend((
            port.name, port.caption, port.description, port.data_type,
            KIND_NAMES.get(port.kind, ""),
        ))
    return " ".join(str(value) for value in values if str(value).strip()).lower()


def node_instance_search_text(model: dict[str, Any]) -> str:
    """Search index for one installed element, including changed settings."""
    spec = COMPONENTS.get(str(model.get("type", "")))
    values: list[Any] = (str(model.get("id", "")), str(model.get("type", "")))
    if spec is not None:
        values.append(component_search_text(spec))
    properties = model.get("properties", {})
    if isinstance(properties, dict):
        for name, value in properties.items():
            if not str(name).startswith("_") and name != "subgraph":
                values.extend((name, str(value)[:500]))
    return " ".join(str(value) for value in values if str(value).strip()).lower()


def node_instance_label(model: dict[str, Any]) -> str:
    """Human label that distinguishes several copies of one element."""
    spec = COMPONENTS.get(str(model.get("type", "")))
    caption = spec.caption if spec is not None else str(model.get("type", "Элемент"))
    props = model.get("properties", {})
    name = str(props.get("name", "")).strip() if isinstance(props, dict) else ""
    return f"{caption} · {name}" if name and name != caption else caption


def project_node_records(
    project: dict[str, Any],
    path_names: tuple[str, ...] = (),
    path_ids: tuple[str, ...] = (),
    *,
    max_depth: int = 32,
) -> list[dict[str, Any]]:
    """Flatten nested user containers while retaining an openable path."""
    records: list[dict[str, Any]] = []
    if not isinstance(project, dict) or max_depth < 0:
        return records
    for model in project.get("nodes", []):
        if not isinstance(model, dict):
            continue
        records.append({"model": model, "path_names": path_names, "path_ids": path_ids})
        if str(model.get("type")) != "UserContainer":
            continue
        props = model.get("properties", {})
        inner = props.get("subgraph") if isinstance(props, dict) else None
        if isinstance(inner, dict):
            records.extend(project_node_records(
                inner,
                path_names + (node_instance_label(model),),
                path_ids + (str(model.get("id", "")),),
                max_depth=max_depth - 1,
            ))
    return records


def format_component_help(type_name: str) -> str:
    """Full help shown by the editor for a selected palette element."""
    if type_name not in COMPONENTS:
        return "Элемент не найден в каталоге."
    return render_help(component_help(type_name), show_advanced=True)


BEGINNER_GUIDE = """КАК СОБРАТЬ ПЕРВУЮ ПРОГРАММУ

1. Откройте готовый проект из меню «Примеры».
2. Выберите элемент. Справа прочитайте: что он делает, когда применять, как использовать и что получится.
3. Проследите линию от действия человека, например «Нажатие», до видимого результата.
4. Поменяйте один текст, число или подпись и запустите программу.
5. Если линия не соединяется, наведите курсор на точку. Справка подскажет допустимое продолжение.

Начинайте с готовых проектов «Калькулятор заказа», «Список покупок» и «Таймер фокуса». Они содержат форму, действия, данные и видимый результат.
"""

DYNAMIC_GAME_GUIDE = """КАК ИЗУЧАТЬ ИГРУ

Сначала найдите, что запускает игру. Затем проследите отдельные линии для движения, проверки правила, счёта и показа результата. Меняйте один параметр за раз и запускайте проект после каждого изменения. Если нужно увидеть внутреннюю схему готового блока, откройте его в расширенном режиме.
"""
