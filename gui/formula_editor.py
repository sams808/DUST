"""Fully-editable R'/K' formula builder.

The Dell/Du-Stebbins model is not fixed to one "R' = alkalis / (Al2O3+
B2O3)" definition - the thesis itself uses different modifier sets for
Fig 4.17 (Na2O+CaO+Bi2O3) vs Fig 5.7 (Na2O only), and Lu et al. (2021)
goes further, weighting each oxide by a per-group coefficient rather
than including it at full strength. This widget exposes exactly that:
every candidate oxide gets an include checkbox AND an editable
coefficient, for both the "formers" (K'/R' shared denominator) and
"modifiers" (R' numerator) groups - so any of the above, or a fully
custom formula, is a few clicks away. Presets are starting points, not
a closed list; the current state can be saved/loaded as JSON so a
user's own refined formula persists across sessions.
"""
from __future__ import annotations

import json

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QCheckBox, QDoubleSpinBox, QLabel, QComboBox, QPushButton, QGroupBox,
    QFileDialog, QMessageBox, QHeaderView,
)

from core.oxides import (
    CANONICAL_OXIDES, DELL_DEFAULT_FORMERS, DELL_DEFAULT_MODIFIERS,
    DELL_OPTIONAL_MODIFIERS, LU2021_FORMER_COEFF, LU2021_MODIFIER_COEFF,
)

FORMER_CANDIDATES = [o for o in CANONICAL_OXIDES if o != "SiO2" and o not in (
    "Na2O", "Li2O", "K2O", "Cs2O", "Rb2O", "CaO", "MgO", "SrO", "BaO",
    "ZnO", "PbO", "La2O3", "Y2O3", "Bi2O3",
)]
MODIFIER_CANDIDATES = [
    "Na2O", "Li2O", "K2O", "Cs2O", "Rb2O", "CaO", "MgO", "SrO", "BaO",
    "ZnO", "PbO", "Bi2O3", "La2O3", "Y2O3",
]

PRESETS = {
    "Dell defaults (alkalis + alkaline earths + Bi2O3)": {
        "formers": dict(DELL_DEFAULT_FORMERS), "modifiers": dict(DELL_DEFAULT_MODIFIERS),
    },
    "Simple (Na2O + CaO only)": {
        "formers": {"Al2O3": 1.0, "B2O3": 1.0}, "modifiers": {"Na2O": 1.0, "CaO": 1.0},
    },
    "Thesis Fig 4.17 (Na2O + CaO + Bi2O3)": {
        "formers": {"Al2O3": 1.0, "B2O3": 1.0},
        "modifiers": {"Na2O": 1.0, "CaO": 1.0, "Bi2O3": 1.0},
    },
    "Thesis Fig 5.7 (Na2O only)": {
        "formers": {"Al2O3": 1.0, "B2O3": 1.0}, "modifiers": {"Na2O": 1.0},
    },
    "Lu et al. 2021 weighting scheme": {
        "formers": dict(LU2021_FORMER_COEFF),
        "modifiers": {**dict(LU2021_MODIFIER_COEFF), "Na2O": 1.0},
    },
}

_ALL_DEFAULT_COEFF = {
    **{o: 1.0 for o in FORMER_CANDIDATES}, **{o: 1.0 for o in MODIFIER_CANDIDATES},
    **DELL_DEFAULT_FORMERS, **DELL_DEFAULT_MODIFIERS, **DELL_OPTIONAL_MODIFIERS,
    **LU2021_FORMER_COEFF, **{k: v for k, v in LU2021_MODIFIER_COEFF.items()},
}


class _OxideCoeffTable(QWidget):
    changed = Signal()

    def __init__(self, candidates: list[str], default_on: dict, parent=None):
        super().__init__(parent)
        self._rows: dict[str, tuple[QCheckBox, QDoubleSpinBox]] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.table = QTableWidget(len(candidates), 3)
        self.table.setHorizontalHeaderLabels(["Include", "Oxide", "Coefficient"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setMaximumHeight(28 * min(len(candidates), 8) + 34)
        for r, ox in enumerate(candidates):
            chk = QCheckBox()
            chk.setChecked(ox in default_on)
            spin = QDoubleSpinBox()
            spin.setRange(0.0, 20.0)
            spin.setDecimals(6)  # Lu 2021's 1/3 coefficients need more than 4 places
            spin.setSingleStep(0.1)
            spin.setValue(default_on.get(ox, _ALL_DEFAULT_COEFF.get(ox, 1.0)))
            # wrapped in a lambda: stateChanged/valueChanged pass an argument
            # (int state / float value) but Signal().emit() takes none
            chk.stateChanged.connect(lambda _state=None: self.changed.emit())
            spin.valueChanged.connect(lambda _value=None: self.changed.emit())
            self._rows[ox] = (chk, spin)
            self.table.setCellWidget(r, 0, chk)
            name_item = QTableWidgetItem(ox)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 1, name_item)
            self.table.setCellWidget(r, 2, spin)
        layout.addWidget(self.table)

    def get_dict(self) -> dict:
        return {ox: spin.value() for ox, (chk, spin) in self._rows.items() if chk.isChecked()}

    def set_dict(self, d: dict, block=False):
        for ox, (chk, spin) in self._rows.items():
            if block:
                chk.blockSignals(True)
                spin.blockSignals(True)
            chk.setChecked(ox in d)
            if ox in d:
                spin.setValue(d[ox])
            if block:
                chk.blockSignals(False)
                spin.blockSignals(False)


class FormulaEditor(QWidget):
    """R' = sum(modifierCoeff * x) / sum(formerCoeff * x);  K' = SiO2 / sum(formerCoeff * x)."""
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "K' = SiO2 / (checked formers, weighted).   "
            "R' = (checked modifiers, weighted) / (checked formers, weighted).\n"
            "Any oxide can be included/excluded and given its own weight - "
            "from the simplest \"Na2O only\" up to Lu-2021-style weighted "
            "groups, or your own refined thesis formula."
        ))

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("(custom)")
        self.preset_combo.addItems(list(PRESETS.keys()))
        self.preset_combo.setCurrentText("Dell defaults (alkalis + alkaline earths + Bi2O3)")
        preset_row.addWidget(self.preset_combo, 1)
        btn_save = QPushButton("Save formula...")
        btn_load = QPushButton("Load formula...")
        btn_reset = QPushButton("Reset to Dell defaults")
        preset_row.addWidget(btn_save)
        preset_row.addWidget(btn_load)
        preset_row.addWidget(btn_reset)
        layout.addLayout(preset_row)

        formers_box = QGroupBox("Formers (K' numerator and shared denominator)")
        fb_layout = QVBoxLayout(formers_box)
        self.formers_table = _OxideCoeffTable(FORMER_CANDIDATES, DELL_DEFAULT_FORMERS)
        fb_layout.addWidget(self.formers_table)
        layout.addWidget(formers_box)

        modifiers_box = QGroupBox("Modifiers (R' numerator)")
        mb_layout = QVBoxLayout(modifiers_box)
        self.modifiers_table = _OxideCoeffTable(MODIFIER_CANDIDATES, DELL_DEFAULT_MODIFIERS)
        mb_layout.addWidget(self.modifiers_table)
        layout.addWidget(modifiers_box)

        self.preset_combo.currentTextChanged.connect(self._apply_preset)
        btn_save.clicked.connect(self._save_formula)
        btn_load.clicked.connect(self._load_formula)
        btn_reset.clicked.connect(lambda: self.preset_combo.setCurrentText(
            "Dell defaults (alkalis + alkaline earths + Bi2O3)"))
        self.formers_table.changed.connect(self._on_tables_edited)
        self.modifiers_table.changed.connect(self._on_tables_edited)

    # ------------------------------------------------------------------
    def _apply_preset(self, name: str):
        if name not in PRESETS:
            return
        preset = PRESETS[name]
        self.formers_table.set_dict(preset["formers"], block=True)
        self.modifiers_table.set_dict(preset["modifiers"], block=True)
        self.changed.emit()

    def _on_tables_edited(self):
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentText("(custom)")
        self.preset_combo.blockSignals(False)
        self.changed.emit()

    def formers(self) -> dict:
        return self.formers_table.get_dict()

    def modifiers(self) -> dict:
        return self.modifiers_table.get_dict()

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
            self.formers_table.set_dict(data.get("formers", {}), block=True)
            self.modifiers_table.set_dict(data.get("modifiers", {}), block=True)
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentText("(custom)")
            self.preset_combo.blockSignals(False)
            self.changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, "Load failed", f"Could not load formula:\n{exc}")
