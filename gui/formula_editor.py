"""Fully-editable R'/K' formula builder.

The Dell/Du-Stebbins model is not fixed to one "R' = alkalis / (Al2O3+
B2O3)" definition - different figures/datasets use different modifier
sets (e.g. Na2O+CaO+Bi2O3 vs. Na2O alone), and complex multicomponent
glasses (nuclear waste borosilicates, for instance) can carry transition
metals, rare earths or even actinide oxides that a fixed candidate list
would exclude. This widget exposes every oxide in core.oxides.
CANONICAL_OXIDES (bar SiO2, which is always the K'/R'' numerator) with
an explicit role - Ignore / Former / Modifier - plus an editable
coefficient, so any composition can be assigned wherever it belongs
rather than picking from two pre-baked lists. Presets are starting
points, not a closed list; the current state can be saved/loaded as
JSON so a user's own refined formula persists across sessions.
"""
from __future__ import annotations

import json

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QDoubleSpinBox, QLabel, QComboBox, QPushButton, QGroupBox,
    QFileDialog, QMessageBox, QHeaderView,
)

from core.oxides import (
    CANONICAL_OXIDES, DELL_DEFAULT_FORMERS, DELL_DEFAULT_MODIFIERS,
    LU2021_FORMER_COEFF, LU2021_MODIFIER_COEFF,
)

CANDIDATES = [ox for ox in CANONICAL_OXIDES if ox != "SiO2"]

ROLE_IGNORE, ROLE_FORMER, ROLE_MODIFIER = "Ignore", "Former", "Modifier"

PRESETS = {
    "Dell defaults (alkalis + alkaline earths)": {
        "formers": dict(DELL_DEFAULT_FORMERS), "modifiers": dict(DELL_DEFAULT_MODIFIERS),
    },
    "Simple (Na2O + CaO only)": {
        "formers": {"Al2O3": 1.0, "B2O3": 1.0}, "modifiers": {"Na2O": 1.0, "CaO": 1.0},
    },
    "Na2O + CaO + Bi2O3": {
        "formers": {"Al2O3": 1.0, "B2O3": 1.0},
        "modifiers": {"Na2O": 1.0, "CaO": 1.0, "Bi2O3": 1.0},
    },
    "Na2O only": {
        "formers": {"Al2O3": 1.0, "B2O3": 1.0}, "modifiers": {"Na2O": 1.0},
    },
    "Lu et al. 2021 weighting scheme": {
        "formers": dict(LU2021_FORMER_COEFF),
        "modifiers": {**dict(LU2021_MODIFIER_COEFF), "Na2O": 1.0},
    },
}


class RoleOxideTable(QWidget):
    """One row per candidate oxide: role (Ignore/Former/Modifier) + weight."""
    changed = Signal()

    def __init__(self, candidates: list[str], parent=None):
        super().__init__(parent)
        self._rows: dict[str, tuple[QComboBox, QDoubleSpinBox]] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(len(candidates), 3)
        self.table.setHorizontalHeaderLabels(["Oxide", "Role", "Coefficient"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setMaximumHeight(28 * 12 + 34)  # ~12 rows visible, scrolls for the rest

        for r, ox in enumerate(candidates):
            name_item = QTableWidgetItem(ox)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, name_item)

            role_combo = QComboBox()
            role_combo.addItems([ROLE_IGNORE, ROLE_FORMER, ROLE_MODIFIER])

            spin = QDoubleSpinBox()
            spin.setRange(0.0, 20.0)
            spin.setDecimals(6)  # e.g. Lu 2021's 1/3 coefficients
            spin.setSingleStep(0.1)
            spin.setValue(1.0)

            role_combo.currentTextChanged.connect(lambda _t=None: self.changed.emit())
            spin.valueChanged.connect(lambda _v=None: self.changed.emit())
            self._rows[ox] = (role_combo, spin)
            self.table.setCellWidget(r, 1, role_combo)
            self.table.setCellWidget(r, 2, spin)
        layout.addWidget(self.table)

    def formers(self) -> dict:
        return {ox: spin.value() for ox, (combo, spin) in self._rows.items()
                if combo.currentText() == ROLE_FORMER}

    def modifiers(self) -> dict:
        return {ox: spin.value() for ox, (combo, spin) in self._rows.items()
                if combo.currentText() == ROLE_MODIFIER}

    def set_state(self, formers: dict, modifiers: dict, block: bool = False):
        for ox, (combo, spin) in self._rows.items():
            if block:
                combo.blockSignals(True)
                spin.blockSignals(True)
            if ox in formers:
                combo.setCurrentText(ROLE_FORMER)
                spin.setValue(formers[ox])
            elif ox in modifiers:
                combo.setCurrentText(ROLE_MODIFIER)
                spin.setValue(modifiers[ox])
            else:
                combo.setCurrentText(ROLE_IGNORE)
            if block:
                combo.blockSignals(False)
                spin.blockSignals(False)


class FormulaEditor(QWidget):
    """R' = sum(modifierCoeff * x) / sum(formerCoeff * x);  K' = SiO2 / sum(formerCoeff * x)."""
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        intro = QLabel(
            "K' = SiO2 / (formers, weighted).\n"
            "R' = (modifiers, weighted) / (formers, weighted).\n"
            "Every oxide can be set to Ignore, Former (denominator) or\n"
            "Modifier (R' numerator), with its own weight - from the\n"
            "simplest \"Na2O only\" up to a fully custom, weighted\n"
            "formula for complex multicomponent glasses."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("(custom)")
        self.preset_combo.addItems(list(PRESETS.keys()))
        self.preset_combo.setCurrentText("Dell defaults (alkalis + alkaline earths)")
        preset_row.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_row)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("Save formula...")
        btn_load = QPushButton("Load formula...")
        btn_reset = QPushButton("Reset to Dell defaults")
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_load)
        btn_row.addWidget(btn_reset)
        layout.addLayout(btn_row)

        oxide_box = QGroupBox("Oxide roles")
        ob_layout = QVBoxLayout(oxide_box)
        self.oxide_table = RoleOxideTable(CANDIDATES)
        ob_layout.addWidget(self.oxide_table)
        layout.addWidget(oxide_box)

        self.preset_combo.currentTextChanged.connect(self._apply_preset)
        btn_save.clicked.connect(self._save_formula)
        btn_load.clicked.connect(self._load_formula)
        btn_reset.clicked.connect(lambda: self.preset_combo.setCurrentText(
            "Dell defaults (alkalis + alkaline earths)"))
        self.oxide_table.changed.connect(self._on_table_edited)

        self._apply_preset(self.preset_combo.currentText())

    # ------------------------------------------------------------------
    def _apply_preset(self, name: str):
        if name not in PRESETS:
            return
        preset = PRESETS[name]
        self.oxide_table.set_state(preset["formers"], preset["modifiers"], block=True)
        self.changed.emit()

    def _on_table_edited(self):
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentText("(custom)")
        self.preset_combo.blockSignals(False)
        self.changed.emit()

    def formers(self) -> dict:
        return self.oxide_table.formers()

    def modifiers(self) -> dict:
        return self.oxide_table.modifiers()

    def _save_formula(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save R'/K' formula", "dust_formula.json", "JSON (*.json)")
        if not path:
            return
        data = {"formers": self.formers(), "modifiers": self.modifiers()}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        QMessageBox.information(self, "Saved", f"Formula saved to {path}")

    def _load_formula(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load R'/K' formula", "", "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.oxide_table.set_state(data.get("formers", {}), data.get("modifiers", {}), block=True)
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentText("(custom)")
            self.preset_combo.blockSignals(False)
            self.changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Load failed", f"Could not load formula:\n{exc}")
