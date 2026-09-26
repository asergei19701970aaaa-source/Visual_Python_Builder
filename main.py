"""Visual Python Builder entry point."""
from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from builder_ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Visual Python Builder")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
