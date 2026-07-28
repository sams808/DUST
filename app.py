"""Entry point: DUST.

Plots the two thesis-style figures (K' vs R' background N4 map, and
N4 vs R' NBO-regime map) for aluminoborosilicate / multicomponent
glasses, using the Dell (1983)/Du & Stebbins (2005a) model and the
Lu et al. (2021) model, with an editable composition table (manual
entry or CSV import) and full plot customization.

Run with:  py -3.11 app.py   (or double-click DUST.bat)
"""
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from gui.main_window import MainWindow

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("DUST")

    icon_path = os.path.join(ASSETS, "dust_logo.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    splash = None
    splash_path = os.path.join(ASSETS, "dust_splash.png")
    if os.path.exists(splash_path):
        splash = QSplashScreen(QPixmap(splash_path))
        splash.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        splash.show()
        app.processEvents()

    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    if splash is not None:
        splash.finish(window)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
