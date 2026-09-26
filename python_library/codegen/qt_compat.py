"""Совместимый импорт Qt: сначала PyQt6, затем PySide6."""
QT_API = None
try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    try: from PyQt6 import QtWebEngineWidgets
    except Exception: QtWebEngineWidgets = None
    try: from PyQt6 import QtOpenGLWidgets
    except Exception: QtOpenGLWidgets = None
    try: from PyQt6 import QtQuickWidgets
    except Exception: QtQuickWidgets = None
    try: from PyQt6 import QtSvgWidgets
    except Exception: QtSvgWidgets = None
    try: from PyQt6 import QtPrintSupport
    except Exception: QtPrintSupport = None
    try: from PyQt6 import uic
    except Exception: uic = None
    QtUiTools = None
    QT_API = 'PyQt6'
except Exception:
    from PySide6 import QtCore, QtGui, QtWidgets
    try: from PySide6 import QtWebEngineWidgets
    except Exception: QtWebEngineWidgets = None
    try: from PySide6 import QtOpenGLWidgets
    except Exception: QtOpenGLWidgets = None
    try: from PySide6 import QtQuickWidgets
    except Exception: QtQuickWidgets = None
    try: from PySide6 import QtSvgWidgets
    except Exception: QtSvgWidgets = None
    try: from PySide6 import QtPrintSupport
    except Exception: QtPrintSupport = None
    try: from PySide6 import QtUiTools
    except Exception: QtUiTools = None
    uic = None
    QT_API = 'PySide6'
