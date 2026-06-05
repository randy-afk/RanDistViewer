"""
RanBeam — gui/optics_window.py
================================
OpticsWindow: standalone Twiss functions + magnet strip viewer.
Loads .twi (binary SDDS) and optional .mag (ASCII) files.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Rectangle

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QFrame, QFileDialog,
    QMessageBox, QSizePolicy,
)
from PySide6.QtCore import Qt

from theme import (
    BG, AX_BG, FG, FG_LBL, SPINE_C, OPT_X, OPT_Y,
    ELE_COLORS, RAN_CLR, style_ax,
)
from models.twi_loader import read_twi_file, read_mag_file


class OpticsWindow(QWidget):
    """
    Floating window showing ELEGANT Twiss functions and magnet layout.
    Can be opened from the main toolbar.
    """

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("Lattice Optics — RanBeam")
        self.resize(1300, 850)

        self._twi_data      = None
        self._mag_data      = None
        self._cursor_lines  = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # ── Toolbar ───────────────────────────────────────────────────────
        ctrl = QWidget()
        ctrl.setStyleSheet(f"background: #0f0f1e; border-radius: 4px;")
        cl = QHBoxLayout(ctrl)
        cl.setContentsMargins(8, 4, 8, 4)
        cl.setSpacing(8)

        load_twi_btn = QPushButton("Load .twi...")
        load_twi_btn.setFixedHeight(26)
        load_twi_btn.clicked.connect(self._load_twi)

        load_mag_btn = QPushButton("Load .mag...")
        load_mag_btn.setFixedHeight(26)
        load_mag_btn.clicked.connect(self._load_mag)

        cl.addWidget(load_twi_btn)
        cl.addWidget(load_mag_btn)

        self._file_lbl = QLabel("No files loaded")
        self._file_lbl.setStyleSheet(f"color: {FG_LBL}; font-size: 10px;")
        cl.addWidget(self._file_lbl)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: #2a2a3a;"); sep.setFixedWidth(1)
        cl.addWidget(sep)

        cl.addWidget(QLabel("Show:"))
        self._cb_beta  = QCheckBox("beta");  self._cb_beta.setChecked(True)
        self._cb_alpha = QCheckBox("alpha"); self._cb_alpha.setChecked(False)
        self._cb_eta   = QCheckBox("eta");   self._cb_eta.setChecked(True)
        self._cb_phi   = QCheckBox("phi");   self._cb_phi.setChecked(False)
        for cb in [self._cb_beta, self._cb_alpha, self._cb_eta, self._cb_phi]:
            cb.setStyleSheet(f"color: {FG};")
            cb.toggled.connect(self._rebuild)
            cl.addWidget(cb)

        cl.addStretch()
        self._params_lbl = QLabel("")
        self._params_lbl.setStyleSheet(
            f"color: {RAN_CLR}; font-size: 10px; font-family: monospace;")
        cl.addWidget(self._params_lbl)
        layout.addWidget(ctrl)

        # ── Canvas ────────────────────────────────────────────────────────
        self.fig    = plt.Figure(facecolor=BG, dpi=96)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.canvas)

        # Hover tooltip
        self._tooltip = QLabel("", self.canvas)
        self._tooltip.setStyleSheet(
            f"QLabel {{ background: #1a1a3a; color: {FG}; "
            f"border: 1px solid {RAN_CLR}; border-radius: 4px; "
            f"padding: 3px 8px; font-size: 10px; font-family: monospace; }}")
        self._tooltip.hide()
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect(
            "figure_leave_event", lambda _: self._tooltip.hide())

    # ── File loading ───────────────────────────────────────────────────────

    def _load_twi(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Twiss file", "",
            "Twiss files (*.twi);;SDDS files (*.sdds);;All files (*.*)")
        if not path:
            return
        try:
            self._twi_data = read_twi_file(path)
            self._update_file_label()
            self._update_params_label()
            self._rebuild()
        except Exception as e:
            QMessageBox.critical(self, "Twi load error", str(e))

    def _load_mag(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open magnet layout file", "",
            "Magnet files (*.mag);;All files (*.*)")
        if not path:
            return
        try:
            self._mag_data = read_mag_file(path)
            self._update_file_label()
            self._rebuild()
        except Exception as e:
            QMessageBox.critical(self, "Mag load error", str(e))

    def _update_file_label(self):
        parts = []
        if self._twi_data:
            n = len(self._twi_data["data"].get("s", []))
            parts.append(f"twi: {n} elements")
        if self._mag_data:
            n = len(self._mag_data.get("s", []))
            parts.append(f"mag: {n} elements")
        self._file_lbl.setText("  |  ".join(parts) if parts else "No files loaded")
        self._file_lbl.setStyleSheet(
            f"color: {RAN_CLR}; font-size: 10px;" if parts
            else f"color: {FG_LBL}; font-size: 10px;")

    def _update_params_label(self):
        if not self._twi_data:
            return
        p     = self._twi_data.get("params", {})
        parts = []
        if "nux"    in p: parts.append(f"nu_x = {p['nux']:.4f}")
        if "nuy"    in p: parts.append(f"nu_y = {p['nuy']:.4f}")
        if "alphac" in p: parts.append(f"alphac = {p['alphac']:.4g}")
        if "ex0"    in p: parts.append(f"eps_x = {p['ex0']*1e9:.3g} nm")
        self._params_lbl.setText("   ".join(parts))

    # ── Plot building ──────────────────────────────────────────────────────

    def _active_panels(self) -> list[str]:
        out = []
        if self._cb_beta.isChecked():  out.append("beta")
        if self._cb_alpha.isChecked(): out.append("alpha")
        if self._cb_eta.isChecked():   out.append("eta")
        if self._cb_phi.isChecked():   out.append("phi")
        return out

    def _rebuild(self):
        if self._twi_data is None:
            return
        d      = self._twi_data["data"]
        s      = d.get("s", np.array([]))
        panels = self._active_panels()

        if len(s) == 0 or not panels:
            self.fig.clear()
            self.canvas.draw_idle()
            return

        has_mag  = (self._mag_data is not None
                    and len(self._mag_data["s"]) > 0)
        n_panels = len(panels)
        strip_h  = 2
        plot_h   = 7
        ratios   = ([strip_h] + [plot_h] * n_panels if has_mag
                    else [plot_h] * n_panels)

        self.fig.clear()
        self._cursor_lines = []

        gs = self.fig.add_gridspec(
            len(ratios), 1, height_ratios=ratios,
            hspace=0.06,
            left=0.09, right=0.97, top=0.97, bottom=0.07)

        ref_ax     = None
        row_offset = 0

        if has_mag:
            ax_strip = self.fig.add_subplot(gs[0])
            self._draw_mag_strip(ax_strip, s)
            line = ax_strip.axvline(
                x=float(s[0]), color="#ffffff",
                linewidth=0.8, alpha=0.4, zorder=10)
            self._cursor_lines.append(line)
            ref_ax     = ax_strip
            row_offset = 1

        _colors = {"x": OPT_X, "y": OPT_Y}

        for i, panel in enumerate(panels):
            ax = self.fig.add_subplot(
                gs[i + row_offset],
                sharex=ref_ax if ref_ax else None)
            if ref_ax is None:
                ref_ax = ax
            style_ax(ax)

            if panel == "beta":
                ax.plot(s, d["betax"], color=_colors["x"],
                        linewidth=1.2, label="betax [m]")
                ax.plot(s, d["betay"], color=_colors["y"],
                        linewidth=1.2, label="betay [m]")
                ax.set_ylabel("beta [m]", color=FG, fontsize=9)
                ax.legend(fontsize=8, facecolor=BG, labelcolor=FG,
                          framealpha=0.8, loc="upper right")

            elif panel == "alpha":
                ax.plot(s, d["alphax"], color=_colors["x"],
                        linewidth=1.2, label="alphax")
                ax.plot(s, d["alphay"], color=_colors["y"],
                        linewidth=1.2, label="alphay")
                ax.set_ylabel("alpha", color=FG, fontsize=9)
                ax.axhline(0, color=SPINE_C, linewidth=0.5)
                ax.legend(fontsize=8, facecolor=BG, labelcolor=FG,
                          framealpha=0.8, loc="upper right")

            elif panel == "eta":
                ax.plot(s, d["etax"] * 100, color=_colors["x"],
                        linewidth=1.2, label="etax [cm]")
                ax.plot(s, d["etay"] * 100, color=_colors["y"],
                        linewidth=1.2, label="etay [cm]")
                ax.set_ylabel("eta [cm]", color=FG, fontsize=9)
                ax.axhline(0, color=SPINE_C, linewidth=0.5)
                ax.legend(fontsize=8, facecolor=BG, labelcolor=FG,
                          framealpha=0.8, loc="upper right")

            elif panel == "phi":
                ax.plot(s, d["psix"] / (2 * np.pi), color=_colors["x"],
                        linewidth=1.2, label="phix / 2π")
                ax.plot(s, d["psiy"] / (2 * np.pi), color=_colors["y"],
                        linewidth=1.2, label="phiy / 2π")
                ax.set_ylabel("phi / 2π", color=FG, fontsize=9)
                ax.legend(fontsize=8, facecolor=BG, labelcolor=FG,
                          framealpha=0.8, loc="upper right")

            if i == n_panels - 1:
                ax.set_xlabel("s  [m]", color=FG, fontsize=10)
            else:
                ax.tick_params(labelbottom=False)

            line = ax.axvline(
                x=float(s[0]), color="#ffffff",
                linewidth=0.8, alpha=0.4, zorder=10)
            self._cursor_lines.append(line)

        self.canvas.draw_idle()

    def _draw_mag_strip(self, ax, s_twi):
        ax.set_facecolor("#0a0a18")
        ax.set_yticks([])
        ax.tick_params(labelbottom=False, bottom=False,
                       left=False, labelleft=False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_ylim(-1.2, 1.2)
        ax.axhline(0, color=SPINE_C, linewidth=0.6)
        ax.set_xlim(float(s_twi[0]), float(s_twi[-1]))

        mag      = self._mag_data
        s_arr    = mag["s"]
        profiles = mag["profile"]
        etypes   = mag["etype"]

        s_start     = np.zeros_like(s_arr)
        s_start[1:] = s_arr[:-1]

        for i in range(len(s_arr)):
            prof  = profiles[i]
            etype = etypes[i].upper()
            cinfo = ELE_COLORS.get(etype, ("#505050", 1))
            color = cinfo[0]
            if color is None or abs(prof) < 1e-6:
                continue
            length = s_arr[i] - s_start[i]
            if length < 1e-6:
                continue
            height = min(abs(prof), 1.0)
            y_bot  = 0.0 if prof > 0 else -height
            ax.add_patch(Rectangle(
                (s_start[i], y_bot), length, height,
                facecolor=color, edgecolor="none",
                alpha=0.85, zorder=2))

    # ── Hover tooltip ──────────────────────────────────────────────────────

    def _on_hover(self, event):
        if event.inaxes is None or self._twi_data is None:
            self._tooltip.hide()
            return
        d     = self._twi_data["data"]
        s_arr = d.get("s", np.array([]))
        if len(s_arr) == 0 or event.xdata is None:
            self._tooltip.hide()
            return

        idx   = int(np.argmin(np.abs(s_arr - event.xdata)))
        s_val = float(s_arr[idx])
        name  = (d["ElementName"][idx]
                 if idx < len(d.get("ElementName", [])) else "?")
        etype = (d["ElementType"][idx]
                 if idx < len(d.get("ElementType", [])) else "?")
        betax = float(d["betax"][idx]) if "betax" in d else 0.0
        betay = float(d["betay"][idx]) if "betay" in d else 0.0
        etax  = float(d["etax"][idx])  if "etax"  in d else 0.0

        txt = (f"{name}  [{etype}]\n"
               f"s = {s_val:.4f} m\n"
               f"betax = {betax:.3f} m   betay = {betay:.3f} m\n"
               f"etax = {etax*100:.3f} cm")
        self._tooltip.setText(txt)
        self._tooltip.adjustSize()

        for line in self._cursor_lines:
            line.set_xdata([s_val, s_val])
        self.canvas.draw_idle()

        px = self.canvas.mapFromGlobal(self.canvas.cursor().pos()).x() + 14
        py = self.canvas.mapFromGlobal(self.canvas.cursor().pos()).y() - 10
        px = min(px, self.canvas.width()  - self._tooltip.width()  - 4)
        py = max(4,  min(py, self.canvas.height() - self._tooltip.height() - 4))
        self._tooltip.move(px, py)
        self._tooltip.show()

    def closeEvent(self, event):
        plt.close(self.fig)
        event.accept()
