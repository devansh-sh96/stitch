"""
main.py - Main Entry Point for Stitch Workspace Hub & Desktop Pet
Launches the full PySide6 desktop application with high-DPI scaling enabled.
"""

import sys
import os
from PySide6 import QtCore, QtGui, QtWidgets

# Enable High DPI Scaling
if hasattr(QtCore.Qt, "AA_EnableHighDpiScaling"):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
if hasattr(QtCore.Qt, "AA_UseHighDpiPixmaps"):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

from ui import StitchWorkspaceWindow


def run():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Stitch Workspace Hub")
    app.setOrganizationName("thelifeofpablo")

    # Set Application default font
    font = QtGui.QFont("Segoe UI", 10)
    app.setFont(font)

    # Initialize Main Hub Window
    window = StitchWorkspaceWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run()
