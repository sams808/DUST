"""Editable composition table: manual entry + CSV import/export.

Backed by a pandas DataFrame; the QTableWidget is just a thin editable
view over it. Oxide columns are mol%; two free-text columns ("Sample",
"Label") are carried through for point annotation / grouping in the
plots. Every row also carries a hidden "_uid" column (not a visible
table column - tracked in lockstep with the table's rows) so per-point
plot styling (gui/point_style.py) can stay attached to the same row
even if other rows are added, deleted, or reordered around it.
"""
from __future__ import annotations

import uuid

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QFileDialog, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QCheckBox, QLabel, QMenu,
)

from core.oxides import CANONICAL_OXIDES, MOLAR_MASS
from core import io as core_io

DEFAULT_OXIDE_COLUMNS = [
    "SiO2", "Al2O3", "B2O3", "Na2O", "Li2O", "K2O", "CaO", "MgO", "BaO", "Bi2O3",
]
EXTRA_COLUMNS = ["Sample", "Label"]


class ColumnMappingDialog(QDialog):
    """Lets the user confirm/adjust how CSV columns map onto oxides."""

    def __init__(self, columns, guessed_mapping, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Map CSV columns")
        self.columns = list(columns)
        self._combos = {}

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Confirm what each CSV column represents. Unrecognized columns "
            "default to \"Ignore\"; pick \"Sample\" or \"Label\" to keep them "
            "as text, or pick an oxide to import it as composition data."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QFormLayout()
        options = ["Ignore", "Sample", "Label"] + CANONICAL_OXIDES
        for col in self.columns:
            combo = QComboBox()
            combo.addItems(options)
            guess = guessed_mapping.get(col)
            if guess in CANONICAL_OXIDES:
                combo.setCurrentText(guess)
            elif col.strip().lower() in ("sample", "name", "id", "glass"):
                combo.setCurrentText("Sample")
            else:
                combo.setCurrentText("Ignore")
            self._combos[col] = combo
            form.addRow(col, combo)
        layout.addLayout(form)

        self.wt_to_mol_checkbox = QCheckBox("Values are wt% - convert to mol% on import")
        layout.addWidget(self.wt_to_mol_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def result_mapping(self) -> dict:
        mapping = {}
        for col, combo in self._combos.items():
            choice = combo.currentText()
            mapping[col] = None if choice == "Ignore" else choice
        return mapping

    def convert_wt_to_mol(self) -> bool:
        return self.wt_to_mol_checkbox.isChecked()


class DataTable(QWidget):
    dataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.oxide_columns = list(DEFAULT_OXIDE_COLUMNS)
        self._row_uids: list[str] = []

        layout = QVBoxLayout(self)
        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Add row")
        self.btn_del = QPushButton("Delete selected rows")
        self.btn_import = QPushButton("Import CSV...")
        self.btn_export = QPushButton("Export CSV...")
        self.btn_add_col = QPushButton("Add oxide column...")
        for b in (self.btn_add, self.btn_del, self.btn_import, self.btn_export, self.btn_add_col):
            btn_row.addWidget(b)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.table = QTableWidget(0, 0)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        layout.addWidget(self.table)

        self.btn_add.clicked.connect(self.add_row)
        self.btn_del.clicked.connect(self.delete_selected_rows)
        self.btn_import.clicked.connect(self.import_csv)
        self.btn_export.clicked.connect(self.export_csv)
        self.btn_add_col.clicked.connect(self._add_oxide_column)

        self._rebuild_headers()
        self.table.itemChanged.connect(lambda _item: self.dataChanged.emit())

    # -- headers / rows -------------------------------------------------
    def _rebuild_headers(self):
        headers = EXTRA_COLUMNS + self.oxide_columns
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

    def _context_menu(self, pos):
        menu = QMenu(self)
        act_remove_col = menu.addAction("Remove this oxide column")
        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen == act_remove_col:
            col = self.table.currentColumn()
            headers = EXTRA_COLUMNS + self.oxide_columns
            if 0 <= col < len(headers) and headers[col] in self.oxide_columns:
                self.oxide_columns.remove(headers[col])
                self.set_dataframe(self.get_dataframe())

    def _add_oxide_column(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Add oxide column")
        layout = QVBoxLayout(dlg)
        combo = QComboBox()
        remaining = [o for o in CANONICAL_OXIDES if o not in self.oxide_columns]
        combo.addItems(remaining)
        layout.addWidget(combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        if dlg.exec() == QDialog.Accepted and combo.currentText():
            df = self.get_dataframe()
            self.oxide_columns.append(combo.currentText())
            self.set_dataframe(df)

    # -- row operations ---------------------------------------------------
    def add_row(self, values: dict | None = None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self._row_uids.insert(row, uuid.uuid4().hex[:8])
        headers = EXTRA_COLUMNS + self.oxide_columns
        values = values or {}
        self.table.blockSignals(True)
        for c, h in enumerate(headers):
            text = "" if h in EXTRA_COLUMNS else "0"
            if h in values and pd.notna(values[h]):
                text = str(values[h])
            self.table.setItem(row, c, QTableWidgetItem(text))
        self.table.blockSignals(False)
        self.dataChanged.emit()

    def delete_selected_rows(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)
            if 0 <= r < len(self._row_uids):
                del self._row_uids[r]
        self.dataChanged.emit()

    # -- dataframe conversion ---------------------------------------------
    def get_dataframe(self) -> pd.DataFrame:
        headers = EXTRA_COLUMNS + self.oxide_columns
        self._sync_uids()
        rows = []
        for r in range(self.table.rowCount()):
            row = {}
            for c, h in enumerate(headers):
                item = self.table.item(r, c)
                text = item.text().strip() if item else ""
                if h in self.oxide_columns:
                    try:
                        row[h] = float(text) if text != "" else 0.0
                    except ValueError:
                        row[h] = 0.0
                else:
                    row[h] = text
            row["_uid"] = self._row_uids[r]
            rows.append(row)
        return pd.DataFrame(rows, columns=headers + ["_uid"])

    def _sync_uids(self):
        """Keep _row_uids the same length as the table, generating fresh
        ids for any row that doesn't have one yet (defensive - every path
        that adds/removes rows should already keep this in sync)."""
        n = self.table.rowCount()
        while len(self._row_uids) < n:
            self._row_uids.append(uuid.uuid4().hex[:8])
        del self._row_uids[n:]

    def set_dataframe(self, df: pd.DataFrame):
        # grow oxide_columns to include anything present in df
        for col in df.columns:
            if col in CANONICAL_OXIDES and col not in self.oxide_columns:
                self.oxide_columns.append(col)
        self._rebuild_headers()
        headers = EXTRA_COLUMNS + self.oxide_columns

        if "_uid" in df.columns:
            self._row_uids = [
                uid if isinstance(uid, str) and uid else uuid.uuid4().hex[:8]
                for uid in df["_uid"]
            ]
        else:
            self._row_uids = [uuid.uuid4().hex[:8] for _ in range(len(df))]

        self.table.blockSignals(True)
        self.table.setRowCount(len(df))
        for r in range(len(df)):
            for c, h in enumerate(headers):
                val = df[h].iloc[r] if h in df.columns else ("" if h in EXTRA_COLUMNS else 0)
                if h in self.oxide_columns:
                    text = "" if pd.isna(val) else f"{float(val):g}"
                else:
                    text = "" if pd.isna(val) else str(val)
                self.table.setItem(r, c, QTableWidgetItem(text))
        self.table.blockSignals(False)
        self.dataChanged.emit()

    # -- CSV --------------------------------------------------------------
    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV files (*.csv);;All files (*)")
        if not path:
            return
        try:
            raw = core_io.read_csv_auto(path)
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", f"Could not read CSV:\n{exc}")
            return

        guessed = core_io.suggest_column_mapping(raw.columns)
        dlg = ColumnMappingDialog(raw.columns, guessed, self)
        if dlg.exec() != QDialog.Accepted:
            return
        mapping = dlg.result_mapping()
        df = core_io.apply_mapping(raw, mapping)

        if dlg.convert_wt_to_mol():
            df = core_io.wt_to_mol_percent(df, MOLAR_MASS)

        existing = self.get_dataframe()
        headers = EXTRA_COLUMNS + self.oxide_columns
        for col in df.columns:
            if col not in headers:
                if col in CANONICAL_OXIDES:
                    self.oxide_columns.append(col)
                headers = EXTRA_COLUMNS + self.oxide_columns
        combined = pd.concat([existing, df], ignore_index=True, sort=False)
        # keep "_uid" through the reindex (it's not a visible header column)
        # so pre-existing rows retain their identity - only the freshly
        # imported rows (which never had one) get a "" that set_dataframe
        # below will turn into a fresh id.
        combined = combined.reindex(columns=headers + ["_uid"], fill_value="")
        self.set_dataframe(combined)
        QMessageBox.information(self, "Import complete", f"Imported {len(df)} row(s).")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "n4_nbo_data.csv", "CSV files (*.csv)")
        if not path:
            return
        # "_uid" is an internal identity column for per-point plot styling,
        # not something a user importing this file elsewhere should see.
        self.get_dataframe().drop(columns=["_uid"]).to_csv(path, index=False)
        QMessageBox.information(self, "Export complete", f"Saved to {path}")
