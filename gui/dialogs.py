"""
RanBeam — gui/dialogs.py
=========================
Modal dialogs and the stats-over-time panel drawing helper.
All dialogs are opened from main_window.py.
"""

from __future__ import annotations
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.gridspec import GridSpec
from scipy.ndimage import gaussian_filter

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QCheckBox,
    QGroupBox, QDoubleSpinBox, QSpinBox, QRadioButton,
    QFileDialog, QMessageBox, QWidget, QSizePolicy,
)
from PySide6.QtCore import Qt

from theme import BG, FG, FG_LBL, SPINE_C, RAN_CLR, OPT_X, OPT_Y, style_ax
from models.sdds_loader import COLUMNS

# Particle masses (MeV)
PARTICLE_MASSES = {
    "Electron": 0.51099895,
    "Proton":   938.27208816,
}

_STAT_COLS = ["x", "xp", "y", "yp", "t", "p", "dt"]
_CONJ      = [("x", "xp"), ("y", "yp")]


# ── RF Bucket dialog ──────────────────────────────────────────────────────────

def open_rf_dialog(parent, current_rf_params: dict | None,
                   rf_ramp_setter) -> dict | None:
    """
    Show the RF Bucket configuration dialog.

    Returns the new rf_params dict if Apply was clicked,
    an empty dict {} if Clear was clicked,
    or None if Cancel / closed without action.
    """
    ex        = current_rf_params or {}
    ex_cavs   = ex.get("cavities", [(1e6, 1, 0.0)])
    ex_mass   = ex.get("mass_mev", 0.51099895)
    ex_ac     = ex.get("alphac", 0.0)
    ex_frev   = ex.get("f_rev_hz", 1e6) / 1e6
    ex_mode   = ex.get("mode", "Static")
    ex_species = next((sp for sp, m in PARTICLE_MASSES.items()
                       if abs(m - ex_mass) < 0.001), "Custom")

    dlg = QDialog(parent)
    dlg.setWindowTitle("RF Bucket Configuration" + (" — Edit" if ex else ""))
    dlg.resize(500, 580)
    layout = QVBoxLayout(dlg)

    # Particle & lattice
    grp1 = QGroupBox("Particle & Lattice")
    gl1  = QGridLayout(grp1)
    gl1.addWidget(QLabel("Species:"), 0, 0)
    species_combo = QComboBox()
    species_combo.addItems(["Electron", "Proton", "Custom"])
    species_combo.setCurrentText(ex_species)
    gl1.addWidget(species_combo, 0, 1)
    gl1.addWidget(QLabel("Mass (MeV):"), 0, 2)
    mass_spin = QDoubleSpinBox()
    mass_spin.setDecimals(6); mass_spin.setRange(0.001, 10000)
    mass_spin.setValue(ex_mass)
    gl1.addWidget(mass_spin, 0, 3)
    def on_species(text):
        if text in PARTICLE_MASSES:
            mass_spin.setValue(PARTICLE_MASSES[text])
    species_combo.currentTextChanged.connect(on_species)
    gl1.addWidget(QLabel("alphac:"), 1, 0)
    ac_spin = QDoubleSpinBox()
    ac_spin.setDecimals(8); ac_spin.setRange(-1, 1); ac_spin.setValue(ex_ac)
    gl1.addWidget(ac_spin, 1, 1)
    gl1.addWidget(QLabel("f_rev (MHz):"), 1, 2)
    frev_spin = QDoubleSpinBox()
    frev_spin.setDecimals(6); frev_spin.setRange(0.001, 1000)
    frev_spin.setValue(ex_frev)
    gl1.addWidget(frev_spin, 1, 3)
    layout.addWidget(grp1)

    # RF Mode
    grp2    = QGroupBox("RF Mode")
    gl2     = QHBoxLayout(grp2)
    static_rb = QRadioButton("Static")
    ramp_rb   = QRadioButton("Ramp (CSV)")
    static_rb.setChecked(ex_mode == "Static")
    ramp_rb.setChecked(ex_mode == "Ramp")
    gl2.addWidget(static_rb); gl2.addWidget(ramp_rb)
    layout.addWidget(grp2)

    # Cavities
    grp3 = QGroupBox("Cavities  (V in Volts, phi_s in degrees)")
    gl3  = QVBoxLayout(grp3)
    hdr_row = QWidget()
    hrl = QHBoxLayout(hdr_row); hrl.setContentsMargins(0, 0, 0, 0)
    for txt, w in [("#", 30), ("Voltage (V)", 120),
                   ("Harmonic h", 100), ("phi_s (deg)", 110)]:
        lbl = QLabel(txt); lbl.setFixedWidth(w)
        lbl.setStyleSheet(f"color: {FG_LBL}; font-size: 10px;")
        hrl.addWidget(lbl)
    gl3.addWidget(hdr_row)
    cavity_rows = []
    cav_container = QWidget()
    cav_layout = QVBoxLayout(cav_container)
    cav_layout.setContentsMargins(0, 0, 0, 0); cav_layout.setSpacing(2)
    gl3.addWidget(cav_container)

    def add_cavity(V=1e6, h=1, phi=0.0):
        row = QWidget()
        rl  = QHBoxLayout(row); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(4)
        num = QLabel(str(len(cavity_rows) + 1)); num.setFixedWidth(20)
        v_spin = QDoubleSpinBox(); v_spin.setDecimals(0)
        v_spin.setRange(0, 1e9); v_spin.setValue(V); v_spin.setFixedWidth(110)
        h_spin = QSpinBox(); h_spin.setRange(1, 100000)
        h_spin.setValue(int(h)); h_spin.setFixedWidth(90)
        p_spin = QDoubleSpinBox(); p_spin.setDecimals(4)
        p_spin.setRange(-360, 360); p_spin.setValue(phi); p_spin.setFixedWidth(100)
        for w in [num, v_spin, h_spin, p_spin]: rl.addWidget(w)
        cav_layout.addWidget(row)
        cavity_rows.append((v_spin, h_spin, p_spin))

    for V, h, phi in ex_cavs:
        add_cavity(V, h, phi)
    add_cav_btn = QPushButton("+ Cavity"); add_cav_btn.setFixedWidth(90)
    add_cav_btn.clicked.connect(lambda: add_cavity())
    gl3.addWidget(add_cav_btn)
    layout.addWidget(grp3)

    # Ramp CSV
    grp4 = QGroupBox("Ramp CSV")
    gl4  = QHBoxLayout(grp4)
    ramp_lbl = QLabel("No ramp file loaded")
    ramp_lbl.setStyleSheet(f"color: {FG_LBL}; font-size: 10px;")
    load_csv_btn = QPushButton("Load CSV"); load_csv_btn.setFixedWidth(90)
    gl4.addWidget(ramp_lbl, 1); gl4.addWidget(load_csv_btn)
    layout.addWidget(grp4)

    def load_ramp():
        path, _ = QFileDialog.getOpenFileName(
            dlg, "Load RF ramp CSV", "",
            "CSV files (*.csv *.txt *.dat);;All files (*.*)")
        if not path:
            return
        try:
            with open(path) as f:
                first = f.readline().strip()
            delim = "," if "," in first else ("\t" if "\t" in first else None)
            data_rows = []
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    vals = ([v.strip() for v in line.split(delim)]
                            if delim else line.split())
                    data_rows.append([float(v) for v in vals])
            if not data_rows: raise ValueError("No data rows")
            arr     = np.array(data_rows)
            times   = arr[:, 0]
            n_cav   = (arr.shape[1] - 1) // 3
            cav_data = []
            for row in arr:
                cavs = []
                for i in range(n_cav):
                    b = 1 + i * 3
                    cavs.append((float(row[b]), int(row[b+1]), float(row[b+2])))
                cav_data.append(cavs)
            rf_ramp_setter({"Time": times, "cavities": cav_data})
            ramp_lbl.setText(
                Path(path).name +
                f" ({len(data_rows)} steps, {n_cav} cavit" +
                ("y)" if n_cav == 1 else "ies)"))
            ramp_lbl.setStyleSheet(f"color: {RAN_CLR}; font-size: 10px;")
        except Exception as e:
            QMessageBox.critical(dlg, "Ramp load error", str(e))

    load_csv_btn.clicked.connect(load_ramp)

    # Buttons
    result = [None]
    btn_row = QWidget()
    brl = QHBoxLayout(btn_row)
    apply_btn  = QPushButton("Apply");        apply_btn.setStyleSheet("background: #1a4a2a;")
    clear_btn  = QPushButton("Clear & Close"); clear_btn.setStyleSheet("background: #3a1a1a;")
    cancel_btn = QPushButton("Cancel")
    brl.addWidget(apply_btn); brl.addWidget(clear_btn); brl.addWidget(cancel_btn)
    layout.addWidget(btn_row)

    def apply():
        try:
            cavs = [(v_sp.value(), h_sp.value(), p_sp.value())
                    for v_sp, h_sp, p_sp in cavity_rows]
            result[0] = {
                "mass_mev": mass_spin.value(),
                "alphac":   ac_spin.value(),
                "f_rev_hz": frev_spin.value() * 1e6,
                "cavities": cavs,
                "mode":     "Static" if static_rb.isChecked() else "Ramp",
            }
            dlg.accept()
        except Exception as e:
            QMessageBox.critical(dlg, "RF config error", str(e))

    def clear():
        result[0] = {}   # sentinel: clear
        dlg.accept()

    apply_btn.clicked.connect(apply)
    clear_btn.clicked.connect(clear)
    cancel_btn.clicked.connect(dlg.reject)
    dlg.exec()
    return result[0]   # None = cancelled, {} = cleared, dict = applied


# ── Correlation matrix dialog ─────────────────────────────────────────────────

def open_corr_matrix(parent, finfo, page_idx: int):
    """Open the correlation matrix dialog for the given BunchFile page."""
    pg   = finfo.pages[min(page_idx, finfo.n_pages - 1)]
    data = pg["data"]
    cols = ["x", "xp", "y", "yp", "t", "p"]
    nc   = len(cols)

    dlg    = QDialog(parent)
    dlg.setWindowTitle(f"Correlation Matrix — {finfo.label}")
    dlg.resize(700, 650)
    layout = QVBoxLayout(dlg)

    fig  = plt.Figure(facecolor=BG, dpi=96)
    canv = FigureCanvas(fig)
    layout.addWidget(canv)

    gs = GridSpec(nc, nc, figure=fig,
                  hspace=0.15, wspace=0.15,
                  left=0.08, right=0.97, top=0.97, bottom=0.08)

    color = finfo.color
    for i in range(nc):
        for j in range(nc):
            ax = fig.add_subplot(gs[i, j])
            style_ax(ax)
            ax.tick_params(labelsize=7)
            xd = data[:, COLUMNS.index(cols[j])]
            yd = data[:, COLUMNS.index(cols[i])]
            if i == j:
                ax.hist(xd, bins=60, color=color, alpha=0.8, linewidth=0)
            else:
                ax.scatter(xd, yd, s=0.3, c=color, alpha=0.3, linewidths=0)
                r = float(np.corrcoef(xd, yd)[0, 1])
                ax.text(0.05, 0.95, f"r={r:.2f}",
                        transform=ax.transAxes, fontsize=8,
                        color=FG, va="top")
            if i == nc - 1:
                ax.set_xlabel(cols[j], color=FG, fontsize=8)
            if j == 0:
                ax.set_ylabel(cols[i], color=FG, fontsize=8)

    canv.draw()
    dlg.exec()
    plt.close(fig)


# ── Stats panel helper ────────────────────────────────────────────────────────

def draw_stats_panel(stats_fig, files_to_show: list, current_page: int):
    """
    Draw the stats-over-time panel.
    stats_fig   : the persistent plt.Figure owned by the main window
    files_to_show : list of BunchFile objects
    current_page  : int, 0-indexed current page for the cursor line
    """
    stats_fig.clear()
    stats_fig.patch.set_facecolor(BG)
    gs = GridSpec(3, 3, figure=stats_fig,
                  hspace=0.6, wspace=0.4,
                  left=0.07, right=0.97, top=0.95, bottom=0.12)
    axes   = [stats_fig.add_subplot(gs[i // 3, i % 3]) for i in range(9)]
    titles = ["x", "xp", "y", "yp", "t", "p", "dt", "ε_x", "ε_y"]
    for ax, title in zip(axes, titles):
        style_ax(ax)
        ax.set_title(title, color=FG, fontsize=9, pad=2)

    for finfo in files_to_show:
        # Ensure stats are computed
        finfo.precompute_stats()
        sc_data = finfo.stats_cache
        color   = finfo.color
        px      = np.arange(1, sc_data["n_pages"] + 1)

        for i, col in enumerate(_STAT_COLS):
            ax  = axes[i]
            s   = sc_data["stats"][col]
            mu  = s["mean"]; sig = s["sigma"]
            ax.plot(px, mu, color=color, linewidth=1.0)
            ax.fill_between(px, mu - sig, mu + sig, alpha=0.25, color=color)
            ax.plot(px, s["min"], color=color, linewidth=0.5, linestyle=":")
            ax.plot(px, s["max"], color=color, linewidth=0.5, linestyle=":")

        for i, pair in enumerate(_CONJ):
            ax = axes[7 + i]
            ax.plot(px, sc_data["emit"][pair], color=color, linewidth=1.0)

    cp = current_page + 1
    for ax in axes:
        xlim = ax.get_xlim()
        if xlim[1] - xlim[0] > 0:
            ax.axvline(cp, color="white", linewidth=0.8, alpha=0.6)
