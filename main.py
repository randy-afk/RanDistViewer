#!/usr/bin/env python3
"""
RanDistViewer — main.py
========================
Entry point only. No logic here.

Run:
    python main.py
"""

import sys
import os

__version__ = "1.0.0"

os.environ["QT_API"] = "pyside6"

import matplotlib
matplotlib.use("QtAgg")

from PySide6.QtWidgets import QApplication

from theme import apply_dark_palette
from gui.main_window import SDDSViewer


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RanDistViewer")
    apply_dark_palette(app)
    window = SDDSViewer(__version__)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
