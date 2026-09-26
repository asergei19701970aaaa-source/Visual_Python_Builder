from __future__ import annotations

import copy
import collections
import heapq
import itertools
import json
import keyword
import math
import os
import re
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QMimeData,
    QLineF,
    QPoint,
    QPointF,
    QProcess,
    QProcessEnvironment,
    QRectF,
    QSize,
    Qt,
    QTimer,
    QSettings,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QDrag,
    QFont,
    QFontMetrics,
    QIcon,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
    QPixmap,
    QPolygonF,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QDoubleSpinBox,
    QColorDialog,
    QFileDialog,
    QFontDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsPathItem,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QStyle,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QToolButton,
    QToolTip,
    QToolBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from components import (
    COMPONENTS,
    ComponentSpec,
    default_properties,
    effective_ports,
)
from hiasm_support import (
    grow_dynamic_group,
    is_visual_container,
    parse_hiasm_font,
    serialize_hiasm_font,
    style_mask,
)
from generator import expand_user_containers, generate_python
from container_support import build_interface, pack_project
from ui_importer import import_ui_to_project, report_counts
from wire import (
    build_curve_path,
    build_orthogonal_points,
    normalize_orthogonal_points,
    rounded_orthogonal_path,
)


EVENT_COLOR = QColor("#D5803B")
DATA_COLOR = QColor("#2783DE")

DELPHI_COLORS = {
    "clblack": "#000000", "clmaroon": "#800000", "clgreen": "#008000",
    "clolive": "#808000", "clnavy": "#000080", "clpurple": "#800080",
    "clteal": "#008080", "clgray": "#808080", "clsilver": "#C0C0C0",
    "clred": "#FF0000", "cllime": "#00FF00", "clyellow": "#FFFF00",
    "clblue": "#0000FF", "clfuchsia": "#FF00FF", "claqua": "#00FFFF",
    "clwhite": "#FFFFFF", "clwindow": "#FFFFFF", "clwindowtext": "#000000",
    "clbtnface": "#F0F0F0", "clbtntext": "#000000",
    "clhighlight": "#0078D7", "clgraytext": "#6D6D6D",
    "clmedgray": "#A0A0A0", "clskyblue": "#87CEEB",
    "cldefault": "#000000", "clbtnshadow": "#A0A0A0",
    "clbtnhighlight": "#FFFFFF",
}


def to_qcolor(value: Any, fallback: str = "#000000") -> QColor:
    text = str(value or "").strip()
    color = QColor(DELPHI_COLORS.get(text.lower(), text))
    if not color.isValid():
        try:
            number = int(text, 0)
            # Delphi TColor stores RGB as 0x00BBGGRR.
            color = QColor(number & 255, (number >> 8) & 255, (number >> 16) & 255)
        except (TypeError, ValueError):
            color = QColor(fallback)
    return color


def to_qfont(value: Any) -> QFont:
    data = parse_hiasm_font(value)
    font = QFont(data.name, data.size)
    font.setBold(data.bold)
    font.setItalic(data.italic)
    font.setUnderline(data.underline)
    font.setStrikeOut(data.strikeout)
    return font


def qfont_to_value(font: QFont, previous: Any = None) -> str:
    old = parse_hiasm_font(previous)
    return serialize_hiasm_font(type(old)(
        font.family(),
        max(1, font.pointSize()),
        style_mask(
            bold=font.bold(), italic=font.italic(),
            underline=font.underline(), strikeout=font.strikeOut(),
        ),
        old.color,
        old.charset,
    ))


def default_enabled_ports(
    spec: ComponentSpec, ports: tuple | list | None = None
) -> list[str]:
    """Keep a new node compact while exposing one useful port per direction."""
    all_ports = tuple(ports if ports is not None else spec.ports)
    enabled = [port.name for port in all_ports if port.required]
    priorities = {
        "work_in": (
            "doClick", "doSetText", "doValue", "doSetTitle",
            "doWork", "doData", "doSet", "doShow", "doOn", "doRun",
        ),
        "event_out": (
            "onClick", "onChange", "onCreate", "onStart", "onResult",
            "onSuccess", "onEvent",
        ),
        "data_in": ("Data", "Value", "Text", "Caption", "String"),
        "data_out": ("Result", "Value", "Text", "Data", "String"),
    }
    for kind, preferred in priorities.items():
        candidates = [port for port in all_ports if port.kind == kind]
        if not candidates:
            continue
        chosen = next(
            (port for name in preferred for port in candidates if port.name == name),
            candidates[0],
        )
        if chosen.name not in enabled:
            enabled.append(chosen.name)
    return enabled
NODE_SYMBOLS = {
    "Start": "▶",
    "Form": "▣",
    "Button": "OK",
    "Label": "Ab",
    "LineEdit": "I▭",
    "TextEdit": "≡",
    "CheckBox": "✓",
    "ComboBox": "▾",
    "Timer": "T",
    "Hub": "↦",
    "EventHub": "⇉",
    "DataHub": "⤓",
    "IfElse": "?",
    "Memory": "M",
    "Math": "±",
    "FormatStr": "F",
    "FileRead": "R",
    "FileWrite": "W",
    "DebugPrint": "D",
    "ListWidget": "L",
    "ProgressBar": "%",
    "Slider": "—",
    "SpinBox": "#",
    "OpenFileDialog": "O",
    "SaveFileDialog": "S",
    "Delay": "⌛",
    "Counter": "C",
    "Random": "R",
    "HTTPGet": "H",
    "RunProcess": "▶",
    "TableWidget": "▦",
    "TreeWidget": "↳",
    "DateEdit": "Д",
    "Calendar": "▦",
    "LCDNumber": "88",
    "JSONParse": "{}",
    "JSONStringify": "J",
    "SQLiteQuery": "SQL",
    "Clipboard": "▣",
    "MessageBox": "!",
}


def is_visual_type(type_name: str) -> bool:
    spec = COMPONENTS.get(type_name)
    if spec is None:
        return False
    if spec.visual:
        return True
    if "FormScene" in globals() and type_name in FormScene.VISUAL_TYPES:
        return True
    # Some container INI files are categorized as "service" even though they
    # are normal WinControls. Geometry is the reliable catalog-level signal.
    if type_name.startswith("Delphi::"):
        names = {prop.name.lower() for prop in spec.properties}
        original = type_name.split("::", 1)[1].lower()
        return (
            {"left", "top", "width", "height"}.issubset(names)
            and original not in {
                "mainform", "simpleform", "childform", "childformex"
            }
        )
    return False


def property_value(
    properties: dict[str, Any], *names: str, default: Any = None
) -> Any:
    for name in names:
        if name in properties:
            return properties[name]
    lowered = {str(key).lower(): value for key, value in properties.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return default


def set_property_value(
    properties: dict[str, Any], value: Any, *names: str
):
    for name in names:
        if name in properties:
            properties[name] = value
            return
    properties[names[0]] = value


HIASM_ICON_ALIASES = {
    "Start": "MainForm",
    "Form": "MainForm",
    "LineEdit": "Edit",
    "TextEdit": "Memo",
    "ListWidget": "ListBox",
    "TableWidget": "StringTable",
    "TreeWidget": "TreeView",
    "Slider": "TrackBar",
    "SpinBox": "UpDown",
    "DateEdit": "DatePicker",
    "Calendar": "MonthCalendar",
    "LCDNumber": "LedNumber",
    "MessageBox": "Message",
    "DebugPrint": "Debug",
    "FormatStr": "FormatStr",
    "SQLiteQuery": "SQLite_Query",
    "EventHub": "Hub", "DataHub": "CableData",
    "RadioButton": "RadioButton", "GroupBox": "GroupBox",
    "Dial": "TrackBarRush", "ToolButton": "ButtonRush",
    "PlainTextEdit": "RichEdit", "DoubleSpinBox": "UpDown",
    "ScrollBar": "ScrollBar", "TimeEdit": "Time",
    "DateTimeEdit": "DateConvertor", "TextBrowser": "WebBrowser",
    "FontComboBox": "FontBox", "KeySequenceEdit": "Shortcut",
    "CommandLinkButton": "BitBtn", "Frame": "WinBorders",
    "HorizontalLine": "CrossLine",
    "Gauge": "AnalogGauge", "Speedometer": "CPUUsage",
    "Tachometer": "TimeCounter", "Thermometer": "Volume",
    "LevelMeter": "VolumeComparator", "LEDIndicator": "LED",
    "Compass": "Position", "BatteryIndicator": "CeBatteryStatus",
    "SignalIndicator": "NetInterfaceInfo", "Sparkline": "PlotLines",
    "AnalogClock": "MMTimer", "Knob": "TrackBar",
    "LineChart": "Plotter", "BarChart": "PlotHistogram",
    "PieChart": "Img_Diagram", "RadarChart": "VectorFields",
    "Oscilloscope": "BASS_ChannelVisibleOcilloScope",
    "VUMeter": "VolumeDetector", "SevenSegmentDisplay": "LedNumber",
    "LEDMatrix": "LedLadder",
    "XYPlot": "PlotPoints", "HeatMap": "ColorShade",
    "Timeline": "Events", "WaterfallChart": "PlotDiffSeries",
    "GeoMap": "NetworkLocator", "Waveform": "WaveArray",
    "SpectrumAnalyzer": "BASS_ChannelVisibleSpectrum",
    "MultiSegmentDisplay": "LedNumberEx", "CustomInstrument": "VisualShape", "DashboardCanvas": "PlotPoints",
}
_ICON_INDEX: dict[str, str] | None = None
_ICON_ASSIGNMENTS: dict[str, str] | None = None
APP_ROOT = Path(__file__).resolve().parents[1]
ICONS_DIR = APP_ROOT / "icons"
CUSTOM_ICONS_DIR = ICONS_DIR / "custom"
ICON_SETTINGS_DIR = ICONS_DIR / "settings"
ICON_ASSIGNMENTS_FILE = ICON_SETTINGS_DIR / "icon_assignments.json"
SUPPORTED_ICON_SUFFIXES = {".ico", ".png", ".svg", ".jpg", ".jpeg", ".bmp", ".webp"}


def load_icon_assignments() -> dict[str, str]:
    global _ICON_ASSIGNMENTS
    if _ICON_ASSIGNMENTS is None:
        try:
            raw = json.loads(ICON_ASSIGNMENTS_FILE.read_text(encoding="utf-8"))
            _ICON_ASSIGNMENTS = {str(k): str(v) for k, v in raw.items()}
        except (OSError, ValueError, TypeError):
            _ICON_ASSIGNMENTS = {}
    return _ICON_ASSIGNMENTS


def save_icon_assignment(type_name: str, source: Path | None) -> Path | None:
    """Copy an icon into the portable project folder and remember it by type."""
    assignments = load_icon_assignments()
    if source is None:
        assignments.pop(type_name, None)
    else:
        source = Path(source)
        if source.suffix.lower() not in SUPPORTED_ICON_SUFFIXES:
            raise ValueError("Неподдерживаемый формат значка")
        CUSTOM_ICONS_DIR.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", type_name).strip("._") or "component"
        destination = CUSTOM_ICONS_DIR / f"{safe}{source.suffix.lower()}"
        if source.resolve() != destination.resolve():
            shutil.copy2(source, destination)
        assignments[type_name] = destination.relative_to(ICONS_DIR).as_posix()
    ICON_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    ICON_ASSIGNMENTS_FILE.write_text(
        json.dumps(assignments, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return component_icon_path(type_name)


def component_icon_path(type_name: str) -> Path | None:
    global _ICON_INDEX
    custom = load_icon_assignments().get(type_name)
    if custom:
        candidate = (ICONS_DIR / custom).resolve()
        try:
            candidate.relative_to(ICONS_DIR.resolve())
        except ValueError:
            candidate = Path()
        if candidate.is_file():
            return candidate
    if _ICON_INDEX is None:
        index_path = ICONS_DIR / "index.json"
        try:
            _ICON_INDEX = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _ICON_INDEX = {}
    original = (
        type_name.rsplit(".", 1)[-1]
        if type_name.startswith("Python::")
        else type_name.split("::", 1)[1]
        if type_name.startswith("Delphi::")
        else HIASM_ICON_ALIASES.get(type_name, type_name)
    )
    filename = _ICON_INDEX.get(original.lower())
    if not filename:
        lowered = type_name.lower()
        alias = (
            "math" if any(x in lowered for x in ("math","add","multiply","divide","power")) else
            "formatstr" if any(x in lowered for x in ("text","string","format","replace","split")) else
            "array" if any(x in lowered for x in ("list","array","tuple")) else
            "if_else" if any(x in lowered for x in ("logic","condition","compare","boolean")) else
            "filetools" if any(x in lowered for x in ("file","folder","path")) else
            "time" if any(x in lowered for x in ("date","time","calendar")) else
            "http_get" if any(x in lowered for x in ("http","url","internet")) else
            "image" if any(x in lowered for x in ("image","graphic","pixel")) else
            "memory")
        filename = _ICON_INDEX.get(alias)
    if not filename:
        return None
    path = ICONS_DIR / "delphi" / filename
    return path if path.exists() else None


