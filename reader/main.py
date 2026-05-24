"""
COMIO — Desktop Comic Reader
Entry point for the application.
"""

import sys
import os

# Add the reader directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from app import ComioMainWindow


def main():
    # High DPI support
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("COMIO")
    app.setOrganizationName("COMIO")
    app.setApplicationVersion("1.0.0")

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create and show main window
    window = ComioMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
