"""Small reusable Qt widgets."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton, QColorDialog


class ColorButton(QPushButton):
    """A button that shows a solid color swatch and opens a color picker."""
    colorChanged = Signal(str)

    def __init__(self, color: str = "#000000", parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedWidth(36)
        self.clicked.connect(self._pick)
        self._refresh()

    def _refresh(self):
        self.setStyleSheet(f"background-color: {self._color}; border: 1px solid #555;")

    def _pick(self):
        col = QColorDialog.getColor(QColor(self._color), self, "Choose color")
        if col.isValid():
            self._color = col.name()
            self._refresh()
            self.colorChanged.emit(self._color)

    def color(self) -> str:
        return self._color

    def setColor(self, color: str):
        self._color = color
        self._refresh()
