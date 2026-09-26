"""Диагностика генерации и запуска Visual Python Builder."""
from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from typing import Iterable


DEBUG_STREAM_PREFIX = "__VPB_DEBUG__ "


@dataclass(frozen=True)
class RuntimeDiagnostic:
    severity: str
    message: str
    detail: str = ""
    source_path: str = ""
    line: int | None = None
    node_id: str = ""
    node_type: str = ""


_TRACEBACK_LINE = re.compile(r'File "([^"]+)", line (\d+)')
_NODE_MARKER = re.compile(r"^\s*# VPB_NODE id=(\S+) type=(\S+)")


def build_source_map(source: str) -> dict[int, tuple[str, str]]:
    """Map generated Python line numbers to Builder node IDs and types."""
    result: dict[int, tuple[str, str]] = {}
    current: tuple[str, str] | None = None
    for number, line in enumerate(source.splitlines(), 1):
        match = _NODE_MARKER.match(line)
        if match:
            current = (match.group(1), match.group(2))
        if current is not None:
            result[number] = current
    return result


def extract_traceback(text: str) -> tuple[str, int | None, str]:
    """Return the last traceback file, line and final exception line."""
    matches = list(_TRACEBACK_LINE.finditer(text or ""))
    path = matches[-1].group(1) if matches else ""
    line = int(matches[-1].group(2)) if matches else None
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    final = lines[-1] if lines else "Неизвестная ошибка выполнения."
    return path, line, final


def runtime_diagnostics(
    text: str,
    source: str = "",
    source_path: str = "",
) -> list[RuntimeDiagnostic]:
    """Convert process stderr/traceback text into actionable diagnostics."""
    if not text.strip():
        return []
    path, line, final = extract_traceback(text)
    source_map = build_source_map(source)
    node_id = node_type = ""
    if line is not None:
        node_id, node_type = source_map.get(line, ("", ""))
    detail = text.strip()
    if line is not None and path:
        display_path = source_path or path
        message = f"{final} (строка {line})"
        return [RuntimeDiagnostic(
            "error", message, detail, display_path, line, node_id, node_type
        )]
    return [RuntimeDiagnostic("error", final, detail, source_path or path)]


def write_debug_log(path: str | Path, text: str) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    return destination


def format_diagnostic(item: RuntimeDiagnostic) -> str:
    location = ""
    if item.line is not None:
        location = f" · строка {item.line}"
    node = f" · нода {item.node_id}" if item.node_id else ""
    return f"{item.message}{location}{node}"


def summarize_diagnostics(items: Iterable[RuntimeDiagnostic]) -> str:
    values = list(items)
    if not values:
        return "Ошибок выполнения не найдено."
    return "\n".join(format_diagnostic(item) for item in values)