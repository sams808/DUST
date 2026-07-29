"""Per-point style overrides, edited by double-clicking a point in
either figure. A "point" is identified by (row uid, plot key) - plot
key is "A" for the K'-vs-R' figure, or an N4 series column name (e.g.
"Dell_N4") for the N4-vs-R' figure, since one row can have several
points there (one per visible model series).

Untouched points keep using each figure's normal batch-rendered,
auto-arranged styling (fast, and adjustText-managed label layout).
Only points with an explicit PointStyle are pulled out and drawn
individually with their own color/marker/label/offset - see
gui/plots.py.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QFormLayout, QLineEdit,
    QComboBox, QDoubleSpinBox, QCheckBox, QDialogButtonBox, QLabel,
)

from gui.widgets import ColorButton

MARKERS = ["o", "s", "^", "D", "v", "x", "+", "*", "p", "h"]


@dataclass
class PointStyle:
    color: str
    marker: str
    label: str | None = None   # None = use the figure's default label text; "" = hidden; else custom text
    label_dx: float = 8.0       # label offset from the point, in points
    label_dy: float = 8.0
    show_leader: bool = True    # draw a connecting line from the point to its (offset) label


class PointStyleDialog(QDialog):
    """Edit one point's style. ``default_label`` is shown as a placeholder
    so the user can see what "use default" resolves to without retyping it."""

    def __init__(self, title: str, default_label: str, style: PointStyle, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customize point")
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setWordWrap(True)
        layout.addWidget(heading)

        form = QFormLayout()
        self.color_btn = ColorButton(style.color)
        form.addRow("Color", self.color_btn)

        self.marker_combo = QComboBox()
        self.marker_combo.addItems(MARKERS)
        self.marker_combo.setCurrentText(style.marker if style.marker in MARKERS else MARKERS[0])
        form.addRow("Marker", self.marker_combo)

        self.label_edit = QLineEdit("" if style.label in (None, "") else style.label)
        self.label_edit.setPlaceholderText(
            f"(default: {default_label})" if default_label else "(no default label)"
        )
        form.addRow("Label text", self.label_edit)

        self.hide_label_chk = QCheckBox("Hide label")
        self.hide_label_chk.setChecked(style.label == "")
        self.hide_label_chk.toggled.connect(self.label_edit.setDisabled)
        self.label_edit.setDisabled(self.hide_label_chk.isChecked())
        form.addRow(self.hide_label_chk)

        offset_row = QWidget()
        offset_layout = QHBoxLayout(offset_row)
        offset_layout.setContentsMargins(0, 0, 0, 0)
        self.dx_spin = QDoubleSpinBox()
        self.dx_spin.setRange(-200, 200)
        self.dx_spin.setValue(style.label_dx)
        self.dy_spin = QDoubleSpinBox()
        self.dy_spin.setRange(-200, 200)
        self.dy_spin.setValue(style.label_dy)
        offset_layout.addWidget(QLabel("dx"))
        offset_layout.addWidget(self.dx_spin)
        offset_layout.addWidget(QLabel("dy"))
        offset_layout.addWidget(self.dy_spin)
        form.addRow("Label offset (pt)", offset_row)

        self.leader_chk = QCheckBox("Link label to point (leader line)")
        self.leader_chk.setChecked(style.show_leader)
        form.addRow(self.leader_chk)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.reset_btn = buttons.addButton("Reset to default", QDialogButtonBox.ResetRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.reset_btn.clicked.connect(self._on_reset)
        layout.addWidget(buttons)
        self._was_reset = False

    def _on_reset(self):
        self._was_reset = True
        self.accept()

    def was_reset(self) -> bool:
        return self._was_reset

    def result_style(self) -> PointStyle:
        if self.hide_label_chk.isChecked():
            label = ""
        else:
            text = self.label_edit.text()
            label = text if text else None
        return PointStyle(
            color=self.color_btn.color(),
            marker=self.marker_combo.currentText(),
            label=label,
            label_dx=self.dx_spin.value(),
            label_dy=self.dy_spin.value(),
            show_leader=self.leader_chk.isChecked(),
        )
