"""Main application window: data table + results + customization + plots."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QSplitter,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QFormLayout,
    QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QGroupBox, QLineEdit,
    QScrollArea, QFileDialog, QMessageBox, QGridLayout,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from core.oxides import DELL_DEFAULT_FORMERS, DELL_DEFAULT_MODIFIERS
from core.dell_model import compute_dell
from core.lu_model import compute_lu_all
from gui.table import DataTable
from gui.plots import FigAConfig, FigBConfig, SeriesStyle, draw_fig_a, draw_fig_b
from gui.widgets import ColorButton
from gui.formula_editor import FormulaEditor

RESULT_DISPLAY_COLUMNS = [
    ("Sample", "Sample"),
    ("Dell_R", "R' (Dell)"),
    ("Dell_K", "K' (Dell)"),
    ("Dell_regime", "NBO regime"),
    ("Dell_N4", "N4 (Dell)"),
    ("Dell_pct_NBO_SiQ3", "%NBO-Si Q3"),
    ("Dell_pct_NBO_SiQ2", "%NBO-Si Q2"),
    ("Dell_pct_NBO_B", "%NBO-B"),
    ("Lu_ds_whole_N4", "N4 (Lu DS whole)"),
    ("Lu_ds_borosilicate_N4", "N4 (Lu DS boro)"),
    ("Lu_bernstein_whole_N4", "N4 (Lu Bernstein whole)"),
    ("Lu_bernstein_borosilicate_N4", "N4 (Lu Bernstein boro)"),
]

SERIES_DEFAULTS = [
    ("Dell_N4", "Dell / Du-Stebbins", "#d62728", "o"),
    ("Lu_ds_whole_N4", "Lu 2021 - DS (whole)", "#1f77b4", "s"),
    ("Lu_ds_borosilicate_N4", "Lu 2021 - DS (borosilicate)", "#2ca02c", "^"),
    ("Lu_bernstein_whole_N4", "Lu 2021 - Bernstein (whole)", "#9467bd", "D"),
    ("Lu_bernstein_borosilicate_N4", "Lu 2021 - Bernstein (borosilicate)", "#8c564b", "v"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DUST  -  N4/NBO speciation (Dell 1983 & Lu et al. 2021 models)")
        self.resize(1500, 950)

        self.formers = dict(DELL_DEFAULT_FORMERS)
        self.modifiers = dict(DELL_DEFAULT_MODIFIERS)
        self.computed_df = pd.DataFrame()

        self.fig_a_cfg = FigAConfig()
        self.fig_b_cfg = FigBConfig(series=[
            SeriesStyle(column=col, label=label, color=color, marker=marker, visible=(col == "Dell_N4"))
            for col, label, color, marker in SERIES_DEFAULTS
        ])

        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        # ---- left: tabs ----
        self.left_tabs = QTabWidget()
        splitter.addWidget(self.left_tabs)

        self.table = DataTable()
        self.table.dataChanged.connect(self.recompute)
        self.left_tabs.addTab(self.table, "Data")

        self.results_table = QTableWidget(0, len(RESULT_DISPLAY_COLUMNS))
        self.results_table.setHorizontalHeaderLabels([lbl for _, lbl in RESULT_DISPLAY_COLUMNS])
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        results_container = QWidget()
        rc_layout = QVBoxLayout(results_container)
        btn_export_results = QPushButton("Export results CSV...")
        btn_export_results.clicked.connect(self.export_results_csv)
        rc_layout.addWidget(btn_export_results)
        rc_layout.addWidget(self.results_table)
        self.left_tabs.addTab(results_container, "Results")

        self.formula_editor = FormulaEditor()
        self.formula_editor.changed.connect(self._formulas_changed)
        self.left_tabs.addTab(self._wrap_formulas_tab(), "Formulas / Oxides")
        self.left_tabs.addTab(self._build_appearance_tab(), "Appearance")

        # ---- right: figures ----
        right_tabs = QTabWidget()
        splitter.addWidget(right_tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self.fig_a = Figure(figsize=(6, 5))
        self.canvas_a = FigureCanvas(self.fig_a)
        right_tabs.addTab(self._wrap_canvas(self.canvas_a, self.fig_a), "K' vs R'")

        self.fig_b = Figure(figsize=(6, 5))
        self.canvas_b = FigureCanvas(self.fig_b)
        right_tabs.addTab(self._wrap_canvas(self.canvas_b, self.fig_b), "N4 vs R'")

        self._load_sample_data()
        self.recompute()

    # ------------------------------------------------------------------
    def _wrap_canvas(self, canvas, fig):
        w = QWidget()
        layout = QVBoxLayout(w)
        toolbar = NavigationToolbar(canvas, w)
        layout.addWidget(toolbar)
        layout.addWidget(canvas)
        btn_row = QHBoxLayout()
        dpi_spin = QSpinBox()
        dpi_spin.setRange(72, 1200)
        dpi_spin.setValue(300)
        btn_row.addWidget(QLabel("Export DPI:"))
        btn_row.addWidget(dpi_spin)
        btn_export = QPushButton("Export figure...")
        btn_export.clicked.connect(lambda: self._export_figure(fig, dpi_spin.value()))
        btn_row.addWidget(btn_export)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)
        return w

    def _export_figure(self, fig, dpi):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export figure", "figure.png",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)",
        )
        if not path:
            return
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        QMessageBox.information(self, "Export complete", f"Saved to {path}")

    # ------------------------------------------------------------------
    def _wrap_formulas_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.formula_editor)

        lu_box = QGroupBox("Lu et al. (2021) model")
        lu_layout = QVBoxLayout(lu_box)
        lu_note1 = QLabel(
            "K'' / R'' use a fixed multicomponent weighting scheme "
            "(Al2O3 x4, ZrO2 x3, alkalis x1, alkaline earths x0.5, "
            "La2O3/Y2O3/Bi2O3 x1/3), applied to all 4 fit variants - "
            "choose which to plot in the Appearance tab. This weighting "
            "is fixed to the published fit; the formula editor above "
            "only affects the Dell/Du-Stebbins model's R'/K'. Any oxide "
            "outside this scheme is simply excluded from R''/K'', not "
            "an error."
        )
        lu_note1.setWordWrap(True)
        lu_layout.addWidget(lu_note1)
        lu_note2 = QLabel(
            "Note: this model reports N4 only - no NBO speciation "
            "breakdown is published for it, so %NBO-species columns use "
            "the Dell model only."
        )
        lu_note2.setWordWrap(True)
        lu_layout.addWidget(lu_note2)
        layout.addWidget(lu_box)
        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    def _formulas_changed(self, *_):
        self.formers = self.formula_editor.formers()
        self.modifiers = self.formula_editor.modifiers()
        self.recompute()

    # ------------------------------------------------------------------
    def _build_appearance_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)

        # -- Fig A ----------------------------------------------------
        box_a = QGroupBox("K' vs R'")
        form_a = QFormLayout(box_a)
        self.a_title = QLineEdit(self.fig_a_cfg.title)
        self.a_cmap = QComboBox()
        self.a_cmap.addItems(["viridis", "plasma", "magma", "cividis", "YlGnBu", "coolwarm"])
        self.a_cmap.setCurrentText(self.fig_a_cfg.colormap)
        self.a_rmin, self.a_rmax = QDoubleSpinBox(), QDoubleSpinBox()
        self.a_kmin, self.a_kmax = QDoubleSpinBox(), QDoubleSpinBox()
        for sb in (self.a_rmin, self.a_rmax, self.a_kmin, self.a_kmax):
            sb.setRange(0, 50)
            sb.setDecimals(2)
        self.a_rmin.setValue(self.fig_a_cfg.r_min)
        self.a_rmax.setValue(self.fig_a_cfg.r_max)
        self.a_kmin.setValue(self.fig_a_cfg.k_min)
        self.a_kmax.setValue(self.fig_a_cfg.k_max)
        self.a_colorby = QComboBox()
        self.a_colorby.addItem("(single color)")
        self.a_point_color = ColorButton(self.fig_a_cfg.point_color)
        self.a_point_size = QDoubleSpinBox()
        self.a_point_size.setRange(1, 1000)
        self.a_point_size.setValue(self.fig_a_cfg.point_size)
        self.a_marker = QComboBox()
        self.a_marker.addItems(["+", "o", "s", "^", "x", "D", "v"])
        self.a_marker.setCurrentText(self.fig_a_cfg.point_marker)
        self.a_label_col = QComboBox()
        self.a_label_col.addItem("(none)")
        self.a_label_col.addItem("Sample")
        self.a_colorbar_chk = QCheckBox("Show colorbar")
        self.a_colorbar_chk.setChecked(self.fig_a_cfg.show_colorbar)
        self.a_grid_chk = QCheckBox("Show grid")
        self.a_grid_chk.setChecked(self.fig_a_cfg.show_grid)

        form_a.addRow("Title", self.a_title)
        form_a.addRow("Colormap", self.a_cmap)
        form_a.addRow("R' range", self._hbox(self.a_rmin, self.a_rmax))
        form_a.addRow("K' range", self._hbox(self.a_kmin, self.a_kmax))
        form_a.addRow("Color points by", self.a_colorby)
        form_a.addRow("Point color", self.a_point_color)
        form_a.addRow("Point size", self.a_point_size)
        form_a.addRow("Point marker", self.a_marker)
        form_a.addRow("Point labels", self.a_label_col)
        form_a.addRow(self.a_colorbar_chk)
        form_a.addRow(self.a_grid_chk)
        layout.addWidget(box_a)

        self.a_title.editingFinished.connect(self._appearance_changed)
        for w in (self.a_cmap, self.a_colorby, self.a_marker, self.a_label_col):
            w.currentTextChanged.connect(self._appearance_changed)
        for w in (self.a_rmin, self.a_rmax, self.a_kmin, self.a_kmax, self.a_point_size):
            w.valueChanged.connect(self._appearance_changed)
        for w in (self.a_colorbar_chk, self.a_grid_chk):
            w.stateChanged.connect(self._appearance_changed)
        self.a_point_color.colorChanged.connect(self._appearance_changed)

        # -- Fig B ----------------------------------------------------
        box_b = QGroupBox("N4 vs R' - regions and data series")
        form_b = QFormLayout(box_b)
        self.b_title = QLineEdit(self.fig_b_cfg.title)
        self.b_rmin, self.b_rmax = QDoubleSpinBox(), QDoubleSpinBox()
        self.b_n4min, self.b_n4max = QDoubleSpinBox(), QDoubleSpinBox()
        self.b_rmin.setRange(0, 50)
        self.b_rmax.setRange(0, 50)
        self.b_n4min.setRange(0, 2)
        self.b_n4max.setRange(0, 2)
        self.b_rmin.setValue(self.fig_b_cfg.r_min)
        self.b_rmax.setValue(self.fig_b_cfg.r_max)
        self.b_n4min.setValue(self.fig_b_cfg.n4_min)
        self.b_n4max.setValue(self.fig_b_cfg.n4_max)
        self.b_isok = QLineEdit(", ".join(str(k) for k in self.fig_b_cfg.iso_k_values))
        self.b_show_isok = QCheckBox("Show iso-K' lines")
        self.b_show_isok.setChecked(self.fig_b_cfg.show_iso_k)
        self.b_show_region_legend = QCheckBox("Show regime legend")
        self.b_show_region_legend.setChecked(self.fig_b_cfg.show_region_legend)
        self.b_grid_chk = QCheckBox("Show grid")
        self.b_grid_chk.setChecked(self.fig_b_cfg.show_grid)

        form_b.addRow("Title", self.b_title)
        form_b.addRow("R' range", self._hbox(self.b_rmin, self.b_rmax))
        form_b.addRow("N4 range", self._hbox(self.b_n4min, self.b_n4max))
        form_b.addRow("Iso-K' values", self.b_isok)
        form_b.addRow(self.b_show_isok)
        form_b.addRow(self.b_show_region_legend)
        form_b.addRow(self.b_grid_chk)

        region_names = {1: "No NBO", 2: "NBO-Si only (Q3)", 3: "NBO-Si (Q2&Q3) + NBO-B"}
        self._region_color_buttons = {}
        for i in (1, 2, 3):
            btn = ColorButton(self.fig_b_cfg.region_colors.get(i, "white"))
            btn.colorChanged.connect(self._appearance_changed)
            self._region_color_buttons[i] = btn
            form_b.addRow(f"Region color: {region_names[i]}", btn)

        self.b_title.editingFinished.connect(self._appearance_changed)
        self.b_isok.editingFinished.connect(self._appearance_changed)
        for w in (self.b_rmin, self.b_rmax, self.b_n4min, self.b_n4max):
            w.valueChanged.connect(self._appearance_changed)
        for w in (self.b_show_isok, self.b_show_region_legend, self.b_grid_chk):
            w.stateChanged.connect(self._appearance_changed)

        self._series_widgets = {}
        series_grid = QGridLayout()
        series_grid.addWidget(QLabel("Show"), 0, 0)
        series_grid.addWidget(QLabel("Model"), 0, 1)
        series_grid.addWidget(QLabel("Color"), 0, 2)
        series_grid.addWidget(QLabel("Marker"), 0, 3)
        for i, s in enumerate(self.fig_b_cfg.series):
            chk = QCheckBox()
            chk.setChecked(s.visible)
            lbl = QLabel(s.label)
            color_btn = ColorButton(s.color)
            marker_combo = QComboBox()
            marker_combo.addItems(["o", "s", "^", "D", "v", "x", "+"])
            marker_combo.setCurrentText(s.marker)
            chk.stateChanged.connect(self._appearance_changed)
            color_btn.colorChanged.connect(self._appearance_changed)
            marker_combo.currentTextChanged.connect(self._appearance_changed)
            self._series_widgets[s.column] = (chk, color_btn, marker_combo)
            series_grid.addWidget(chk, i + 1, 0)
            series_grid.addWidget(lbl, i + 1, 1)
            series_grid.addWidget(color_btn, i + 1, 2)
            series_grid.addWidget(marker_combo, i + 1, 3)
        form_b.addRow(series_grid)
        layout.addWidget(box_b)
        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    @staticmethod
    def _hbox(*widgets):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        for widget in widgets:
            lay.addWidget(widget)
        return w

    def _appearance_changed(self, *_):
        self.fig_a_cfg.title = self.a_title.text()
        self.fig_a_cfg.colormap = self.a_cmap.currentText()
        self.fig_a_cfg.r_min = self.a_rmin.value()
        self.fig_a_cfg.r_max = self.a_rmax.value()
        self.fig_a_cfg.k_min = self.a_kmin.value()
        self.fig_a_cfg.k_max = self.a_kmax.value()
        colorby = self.a_colorby.currentText()
        self.fig_a_cfg.point_color_by = None if colorby == "(single color)" else colorby
        self.fig_a_cfg.point_color = self.a_point_color.color()
        self.fig_a_cfg.point_size = self.a_point_size.value()
        self.fig_a_cfg.point_marker = self.a_marker.currentText()
        label_col = self.a_label_col.currentText()
        self.fig_a_cfg.label_column = None if label_col == "(none)" else label_col
        self.fig_a_cfg.show_colorbar = self.a_colorbar_chk.isChecked()
        self.fig_a_cfg.show_grid = self.a_grid_chk.isChecked()

        self.fig_b_cfg.title = self.b_title.text()
        self.fig_b_cfg.r_min = self.b_rmin.value()
        self.fig_b_cfg.r_max = self.b_rmax.value()
        self.fig_b_cfg.n4_min = self.b_n4min.value()
        self.fig_b_cfg.n4_max = self.b_n4max.value()
        try:
            self.fig_b_cfg.iso_k_values = tuple(
                float(x) for x in self.b_isok.text().split(",") if x.strip()
            )
        except ValueError:
            pass
        self.fig_b_cfg.show_iso_k = self.b_show_isok.isChecked()
        self.fig_b_cfg.show_region_legend = self.b_show_region_legend.isChecked()
        for i, btn in self._region_color_buttons.items():
            self.fig_b_cfg.region_colors[i] = btn.color()
        self.fig_b_cfg.show_grid = self.b_grid_chk.isChecked()

        for s in self.fig_b_cfg.series:
            chk, color_btn, marker_combo = self._series_widgets[s.column]
            s.visible = chk.isChecked()
            s.color = color_btn.color()
            s.marker = marker_combo.currentText()

        self._redraw()

    def _refresh_colorby_options(self, df: pd.DataFrame):
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        current = self.a_colorby.currentText()
        self.a_colorby.blockSignals(True)
        self.a_colorby.clear()
        self.a_colorby.addItem("(single color)")
        self.a_colorby.addItems(numeric_cols)
        if current in numeric_cols:
            self.a_colorby.setCurrentText(current)
        self.a_colorby.blockSignals(False)

    # ------------------------------------------------------------------
    def recompute(self):
        df = self.table.get_dataframe()
        if len(df) == 0:
            self.computed_df = df
            self._update_results_table(df)
            self._redraw()
            return
        try:
            df = compute_dell(df, formers=self.formers, modifiers=self.modifiers)
            df = compute_lu_all(df)
        except Exception as exc:
            QMessageBox.warning(self, "Calculation error", str(exc))
            return
        self.computed_df = df
        self._refresh_colorby_options(df)
        self._update_results_table(df)
        self._redraw()

    def _update_results_table(self, df: pd.DataFrame):
        self.results_table.setRowCount(len(df))
        for r in range(len(df)):
            for c, (col, _label) in enumerate(RESULT_DISPLAY_COLUMNS):
                if col in df.columns:
                    val = df[col].iloc[r]
                    if isinstance(val, float):
                        text = "" if pd.isna(val) else f"{val:.4g}"
                    else:
                        text = str(val)
                else:
                    text = ""
                self.results_table.setItem(r, c, QTableWidgetItem(text))
        self.results_table.resizeColumnsToContents()

    def _redraw(self):
        draw_fig_a(self.fig_a, self.computed_df, self.fig_a_cfg)
        self.canvas_a.draw_idle()
        draw_fig_b(self.fig_b, self.computed_df, self.fig_b_cfg)
        self.canvas_b.draw_idle()

    def export_results_csv(self):
        if self.computed_df is None or len(self.computed_df) == 0:
            QMessageBox.information(self, "Nothing to export", "The table is empty.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export results CSV", "n4_nbo_results.csv", "CSV files (*.csv)")
        if not path:
            return
        self.computed_df.to_csv(path, index=False)
        QMessageBox.information(self, "Export complete", f"Saved to {path}")

    # ------------------------------------------------------------------
    def _load_sample_data(self):
        sample_path = Path(__file__).resolve().parent.parent / "sample_data" / "example_glasses.csv"
        if sample_path.exists():
            try:
                df = pd.read_csv(sample_path)
                self.table.set_dataframe(df)
            except Exception:
                pass
