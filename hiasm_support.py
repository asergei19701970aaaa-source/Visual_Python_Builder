"""HiAsm compatibility primitives shared by editor, generator and tests.

The rules in this module are derived from the original Delphi package:
conf/*.ini (especially [Type] Sub) and TFontRec usage in hiFont.pas.
It deliberately contains no Qt imports.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

PORT_KINDS = ("work_in", "event_out", "data_out", "data_in")


@dataclass(frozen=True)
class DynamicPortGroup:
    kind: str
    property_name: str
    prefix: str


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def parse_sub(sub: str) -> tuple[DynamicPortGroup, ...]:
    """Parse HiAsm's four-lane [Type] Sub declaration.

    Lanes are: methods, events, variables (data outputs), data inputs.
    A lane normally has ``CountProperty|PointPrefix``. Declarations without
    commas (Panel, MainForm, Form...) name the internal base element of a
    MultiElement and are therefore not dynamic point declarations.
    """
    text = str(sub or "").strip()
    if not text or "," not in text:
        return ()
    lanes = text.split(",")
    lanes += [""] * (4 - len(lanes))
    result: list[DynamicPortGroup] = []
    for kind, lane in zip(PORT_KINDS, lanes[:4]):
        lane = lane.strip()
        if not lane or "|" not in lane:
            continue
        property_name, prefix = (part.strip() for part in lane.split("|", 1))
        if property_name and prefix:
            result.append(DynamicPortGroup(kind, property_name, prefix))
    return tuple(result)


def dynamic_port_names(sub: str, properties: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Return (name, caption, kind) for all count-driven points."""
    result: list[tuple[str, str, str]] = []
    lowered = {str(key).lower(): value for key, value in properties.items()}
    labels = {
        "work_in": "Вход",
        "event_out": "Событие",
        "data_out": "Выходные данные",
        "data_in": "Входные данные",
    }
    for group in parse_sub(sub):
        raw = properties.get(
            group.property_name,
            lowered.get(group.property_name.lower(), 0),
        )
        count = max(0, min(256, _to_int(raw)))
        for index in range(1, count + 1):
            result.append((
                f"{group.prefix}{index}",
                f"{labels[group.kind]} {index}",
                group.kind,
            ))
    return result


def grow_dynamic_group(
    sub: str,
    properties: dict[str, Any],
    kind: str,
) -> tuple[str, int, str] | None:
    """Grow the first dynamic group of ``kind`` and return its new point."""
    lowered = {str(key).lower(): key for key in properties}
    for group in parse_sub(sub):
        if group.kind != kind:
            continue
        actual_key = lowered.get(group.property_name.lower(), group.property_name)
        current = max(0, _to_int(properties.get(actual_key, 0)))
        if current >= 256:
            return None
        current += 1
        properties[actual_key] = current
        return actual_key, current, f"{group.prefix}{current}"
    return None


def is_visual_container(spec: Any) -> bool:
    interfaces = {
        item.strip().lower()
        for item in str(getattr(spec, "hiasm_interfaces", "")).split(",")
        if item.strip()
    }
    if "controlmanager" not in interfaces:
        return False
    original = str(getattr(spec, "type_name", "")).split("::")[-1].lower()
    return any(token in original for token in (
        "panel", "groupbox", "scrollbox", "pagecontrol", "tabcontrol",
    ))


def is_multi_element(spec: Any) -> bool:
    return str(getattr(spec, "hiasm_class", "")).lower() in {
        "multielement", "multielementex", "polimultielement",
    }


@dataclass(frozen=True)
class HiasmFont:
    name: str = "Arial"
    size: int = 8
    style: int = 0
    color: int | str = 0
    charset: int = 1

    @property
    def bold(self) -> bool:
        return bool(self.style & 1)

    @property
    def italic(self) -> bool:
        return bool(self.style & 2)

    @property
    def underline(self) -> bool:
        return bool(self.style & 4)

    @property
    def strikeout(self) -> bool:
        return bool(self.style & 8)


STYLE_NAMES = {
    "b": 1, "bold": 1, "fsbold": 1,
    "i": 2, "italic": 2, "fsitalic": 2,
    "u": 4, "underline": 4, "fsunderline": 4,
    "s": 8, "strikeout": 8, "fsstrikeout": 8,
}


def _parse_style(value: Any) -> int:
    text = str(value or "0").strip().strip("[]")
    try:
        return max(0, min(15, int(float(text))))
    except ValueError:
        result = 0
        normalized = text.replace(";", ",").replace("|", ",")
        tokens = [item.strip().lower() for item in normalized.split(",")]
        if len(tokens) == 1 and set(tokens[0]) <= set("bius"):
            tokens = list(tokens[0])
        for token in tokens:
            result |= STYLE_NAMES.get(token, 0)
        return result


def parse_hiasm_font(value: Any) -> HiasmFont:
    """Parse the exact HiAsm TFontRec serialization.

    Canonical order: Name, Size, Style(bit mask), Color(TColor), CharSet.
    Square brackets used by .sha files are accepted. Malformed values safely
    fall back to defaults instead of crashing the editor.
    """
    if isinstance(value, HiasmFont):
        return value
    if isinstance(value, dict):
        return HiasmFont(
            str(value.get("name", "Arial") or "Arial"),
            max(1, _to_int(value.get("size", 8), 8)),
            _parse_style(value.get("style", 0)),
            value.get("color", 0),
            max(0, min(255, _to_int(value.get("charset", 1), 1))),
        )
    text = str(value or "").strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    parts = [part.strip() for part in text.split(",")] if text else []
    name = parts[0] if parts and parts[0] else "Arial"
    size = max(1, _to_int(parts[1], 8)) if len(parts) > 1 else 8
    # Visual Python Builder 2.x/early 3.0 mistakenly serialized four style
    # booleans as Name,Size,Bold,Italic,Underline,StrikeOut.  Accept it when
    # loading old projects, but always save the real five-field TFontRec.
    if len(parts) >= 6 and all(
        item.lower() in {"0", "1", "true", "false"}
        for item in parts[2:6]
    ):
        flags = [item.lower() in {"1", "true"} for item in parts[2:6]]
        style = (
            (1 if flags[0] else 0) | (2 if flags[1] else 0)
            | (4 if flags[2] else 0) | (8 if flags[3] else 0)
        )
        return HiasmFont(name, size, style, 0, 1)
    style = _parse_style(parts[2]) if len(parts) > 2 else 0
    color: int | str = 0
    if len(parts) > 3 and parts[3]:
        raw_color = parts[3]
        try:
            color = int(raw_color, 0)
        except ValueError:
            color = raw_color
    charset = max(0, min(255, _to_int(parts[4], 1))) if len(parts) > 4 else 1
    return HiasmFont(name, size, style, color, charset)


def serialize_hiasm_font(value: HiasmFont, brackets: bool = False) -> str:
    font = parse_hiasm_font(value)
    text = f"{font.name},{font.size},{font.style},{font.color},{font.charset}"
    return f"[{text}]" if brackets else text


def style_mask(*, bold: bool, italic: bool, underline: bool, strikeout: bool) -> int:
    return (
        (1 if bold else 0)
        | (2 if italic else 0)
        | (4 if underline else 0)
        | (8 if strikeout else 0)
    )
