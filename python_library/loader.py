"""Автоматическая загрузка библиотек нод."""
from __future__ import annotations

import importlib
import importlib.util
import os
import pkgutil
import traceback
from typing import Dict, List, Optional, Sequence, Tuple

from python_library.core import NodeSpec
from python_library.registry import REGISTRY

HERE = os.path.dirname(os.path.abspath(__file__))
NODES_DIR = os.path.join(HERE, "nodes")
USER_NODES_DIR = os.path.join(os.path.expanduser("~"), ".visual_python_builder", "nodes")


def discover(nodes_dir: Optional[str] = None,
             extra_dirs: Optional[Sequence[str]] = None
             ) -> Tuple[Dict[str, NodeSpec], List[str]]:
    """Импортирует все модули с нодами.

    Возвращает ({ключ: NodeSpec}, [тексты ошибок]).
    Ошибка в одном файле не мешает загрузить остальные.
    """
    errors: List[str] = []
    base = nodes_dir or NODES_DIR

    # 1. штатные библиотеки отдельной Python-библиотеки Builder
    if os.path.isdir(base):
        for info in pkgutil.iter_modules([base]):
            if info.name.startswith("_"):
                continue
            try:
                importlib.import_module(f"python_library.nodes.{info.name}")
            except Exception:  # noqa: BLE001
                errors.append(f"{info.name}: {traceback.format_exc(limit=3)}")

    # 2. пользовательские ноды (~/.visual_python_builder/nodes/*.py) и доп. папки
    for folder in [USER_NODES_DIR, *(extra_dirs or [])]:
        if not folder or not os.path.isdir(folder):
            continue
        for filename in sorted(os.listdir(folder)):
            if not filename.endswith(".py") or filename.startswith("_"):
                continue
            path = os.path.join(folder, filename)
            module_name = f"visual_builder_user_{os.path.splitext(filename)[0]}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, path)
                if spec is None or spec.loader is None:
                    raise ImportError("не удалось прочитать файл")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception:  # noqa: BLE001
                errors.append(f"{path}: {traceback.format_exc(limit=3)}")

    return dict(REGISTRY), errors


def user_nodes_dir(create: bool = False) -> str:
    """Папка для своих нод пользователя."""
    if create:
        os.makedirs(USER_NODES_DIR, exist_ok=True)
    return USER_NODES_DIR