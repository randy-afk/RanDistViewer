"""
RanDistViewer — gui/main_window.py
====================================
SDDSViewer main window. Styled to match RanOptics GUI.
"""

from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QSplitter, QLabel, QPushButton, QSlider,
    QComboBox, QCheckBox, QScrollArea, QFrame,
    QFileDialog, QMessageBox, QRadioButton, QLineEdit,
    QToolBar, QStatusBar, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QAction

from theme import (
    BG, MANTLE, PANEL, BORDER, SURFACE2, CRUST,
    FG, FG_DIM, FG_LBL,
    ACCENT, ACCENT2, RAN_CLR, SUCCESS, ERROR, WARN,
    FILE_COLORS, MENUBAR_SS, BTN_SS, ENTRY_SS, COMBO_SS, CHK_SS, RB_SS,
    FONT_MAIN, FONT_BOLD, FONT_SMALL, FONT_SEC, FONT_HDR, FONT_MONO,
    apply_dark_palette,
)
from models.bunch_model import BunchModel
from models.sdds_loader import read_sdds_file, COLUMNS, COL_UNITS
from gui.plot_panel import PlotPanel
from gui.sidebar import SidebarSection, make_slider
from gui.optics_window import OpticsWindow
from gui.dialogs import open_rf_dialog, open_corr_matrix, draw_stats_panel
from gui.logo import _DistLogo


def _btn(text, slot, color=ACCENT, checkable=False, width=None, height=32):
    """Create a styled toolbar / action button matching RanOptics."""
    b = QPushButton(text)
    b.setFont(FONT_MAIN)
    if width:  b.setFixedWidth(width)
    b.setFixedHeight(height)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {PANEL}; border: 1px solid {color};
            border-radius: 8px; color: {color}; padding: 4px 10px;
            font-weight: 500;
        }}
        QPushButton:hover   {{ background: {color}; color: {CRUST}; }}
        QPushButton:pressed {{ background: {BORDER}; }}
        QPushButton:checked {{ background: {color}22; border-color: {color}; color: {color}; }}
        QPushButton:disabled {{ color: {FG_DIM}; border-color: {BORDER}; background: {PANEL}; }}
    """)
    if checkable: b.setCheckable(True)
    b.clicked.connect(slot)
    return b


class SDDSViewer(QMainWindow):

    def __init__(self, version: str = "1.0.0"):
        super().__init__()
        self.setWindowTitle(f"RanDistViewer  v{version}")
        self._version = version
        self.resize(1440, 920)

        # ── Model ─────────────────────────────────────────────────────────
        self.model = BunchModel()

        # ── App state ─────────────────────────────────────────────────────
        self.current_page    = 0
        self._playing        = False
        self._play_timer     = QTimer(self)
        self._play_timer.timeout.connect(self._advance_frame)
        self._tracked_ids    = []
        self._show_loss      = False
        self._rf_params      = None
        self._rf_ramp_data   = None
        self._show_rf_bucket = False
        self._selected_file  = None
        self._optics_win     = None
        self._panels: list[PlotPanel] = []

        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self.render_all)

        self._build_ui()
        self._add_panel()

    # ── UI construction ───────────────────────────────────────────────────

    def _build_ui(self):
        # Menu bar
        mb = self.menuBar()
        mb.setStyleSheet(MENUBAR_SS)
        fm = mb.addMenu("File")
        fm.addAction(QAction("Open SDDS file…",  self, triggered=self._open_file))
        fm.addAction(QAction("Save Session…",     self, triggered=self._save_session))
        fm.addAction(QAction("Load Session…",     self, triggered=self._load_session))
        fm.addSeparator()
        fm.addAction(QAction("Export panels…",    self, triggered=self._export))
        vm = mb.addMenu("View")
        vm.addAction(QAction("+ Panel",           self, triggered=self._add_panel))
        vm.addAction(QAction("− Panel",           self, triggered=self._remove_panel))
        vm.addAction(QAction("Lattice Optics…",   self, triggered=self._open_optics))

        # Central widget: header + content
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────
        hdr = QWidget()
        hdr.setFixedHeight(64)
        hdr.setStyleSheet(f"background: {MANTLE}; border-bottom: 2px solid {BORDER};")
        hrow = QHBoxLayout(hdr)
        hrow.setContentsMargins(16, 0, 20, 0)
        hrow.setSpacing(8)

        hrow.addWidget(_DistLogo())

        txt_w = QWidget(); txt_w.setStyleSheet("background: transparent;")
        tv = QVBoxLayout(txt_w); tv.setContentsMargins(6, 8, 0, 8); tv.setSpacing(2)

        name_row = QWidget(); name_row.setStyleSheet("background: transparent;")
        nr = QHBoxLayout(name_row); nr.setContentsMargins(0, 0, 0, 0); nr.setSpacing(4)
        name_lbl = QLabel(f"RanDistViewer"); name_lbl.setFont(FONT_HDR)
        name_lbl.setStyleSheet(f"color: {RAN_CLR}; letter-spacing: 2px;")
        nr.addWidget(name_lbl)
        ver_lbl = QLabel(f"v{self._version}"); ver_lbl.setFont(FONT_SMALL)
        ver_lbl.setStyleSheet(f"color: {FG_DIM}; padding-left: 6px;")
        nr.addWidget(ver_lbl)
        nr.addStretch()
        tv.addWidget(name_row)

        sub_lbl = QLabel("Turn-by-Turn Bunch Distribution Viewer")
        sub_lbl.setFont(FONT_SMALL)
        sub_lbl.setStyleSheet(f"color: {FG_DIM};")
        tv.addWidget(sub_lbl)
        hrow.addWidget(txt_w)
        hrow.addStretch()

        info_w = QWidget(); info_w.setStyleSheet("background: transparent;")
        iv = QVBoxLayout(info_w); iv.setContentsMargins(0, 0, 0, 0); iv.setSpacing(2)
        for t in ("Author: Randika Gamage (randika@jlab.org)",
                  "Support: Good luck, I believe in you!"):
            l = QLabel(t); l.setFont(FONT_SMALL)
            l.setAlignment(Qt.AlignRight)
            l.setStyleSheet(f"color: {FG_DIM};")
            iv.addWidget(l)
        hrow.addWidget(info_w)
        root.addWidget(hdr)

        # ── Toolbar ───────────────────────────────────────────────────────
        tb_w = QWidget()
        tb_w.setStyleSheet(f"background: {CRUST}; border-bottom: 1px solid {BORDER};")
        tb_h = QHBoxLayout(tb_w)
        tb_h.setContentsMargins(12, 4, 12, 4)
        tb_h.setSpacing(6)

        self._open_btn  = _btn("📂  Open File",    self._open_file,          ACCENT,  width=120)
        self._pp_btn    = _btn("＋ Panel",          self._add_panel,          ACCENT2, width=90)
        self._pm_btn    = _btn("－ Panel",          self._remove_panel,       ERROR,   width=90)
        self._exp_btn   = _btn("💾  Export",        self._export,             SUCCESS, width=100)
        self._ss_btn    = _btn("Save Session",      self._save_session,       FG_LBL,  width=110)
        self._ls_btn    = _btn("Load Session",      self._load_session,       FG_LBL,  width=110)
        self.corr_btn   = _btn("Corr Matrix",       self._open_corr_matrix,   ACCENT2, width=100)
        self.stats_btn  = _btn("Stats",             self._toggle_stats,       ACCENT2, checkable=True, width=70)
        self.loss_btn   = _btn("Beam Loss",         self._toggle_beam_loss,   WARN,    checkable=True, width=90)
        self.rf_btn     = _btn("RF Bucket",         self._open_rf_dialog,     SUCCESS, width=100)
        self._opt_btn   = _btn("Optics",            self._open_optics,        TEAL,    width=80)

        for w in [self._open_btn, self._sep(),
                  self._pp_btn, self._pm_btn, self._sep(),
                  self._exp_btn, self._sep(),
                  self._ss_btn, self._ls_btn, self._sep(),
                  self.corr_btn, self.stats_btn, self.loss_btn, self._sep(),
                  self.rf_btn, self._sep(),
                  self._opt_btn]:
            tb_h.addWidget(w)

        # File legend
        self._legend_widget = QWidget(); self._legend_widget.setStyleSheet("background: transparent;")
        self._legend_layout = QHBoxLayout(self._legend_widget)
        self._legend_layout.setContentsMargins(8, 0, 8, 0)
        self._legend_layout.setSpacing(8)
        tb_h.addWidget(self._legend_widget)
        tb_h.addStretch()
        root.addWidget(tb_w)

        # ── Status bar ────────────────────────────────────────────────────
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"background: {CRUST}; color: {FG_LBL};")
        self.setStatusBar(self.status_bar)
        self._page_lbl  = QLabel("No file loaded"); self._page_lbl.setFont(FONT_SMALL)
        self._param_lbl = QLabel("");                self._param_lbl.setFont(FONT_SMALL)
        self.status_bar.addWidget(self._page_lbl)
        self.status_bar.addPermanentWidget(self._param_lbl)

        # ── Content: sidebar | right ──────────────────────────────────────
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        root.addWidget(content, 1)

        # Sidebar
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFixedWidth(232)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {MANTLE}; border-right: 1px solid {BORDER}; }}
            QScrollBar:vertical {{ background: {MANTLE}; width: 6px; border-radius: 3px; }}
            QScrollBar::handle:vertical {{ background: {SURFACE2}; border-radius: 3px; min-height: 24px; }}
            QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        sidebar_inner = QWidget()
        sidebar_inner.setStyleSheet(f"background: {MANTLE};")
        self._sidebar_layout = QVBoxLayout(sidebar_inner)
        self._sidebar_layout.setContentsMargins(0, 8, 0, 8)
        self._sidebar_layout.setSpacing(0)
        sidebar_scroll.setWidget(sidebar_inner)
        self._build_sidebar()
        self._sidebar_layout.addStretch()
        content_layout.addWidget(sidebar_scroll)

        # Right panel
        right = QWidget(); right.setStyleSheet(f"background: {BG};")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(4)

        # Page slider row
        slider_row = QWidget(); slider_row.setStyleSheet(f"background: {MANTLE}; border-radius: 6px;")
        sr_layout  = QHBoxLayout(slider_row); sr_layout.setContentsMargins(8, 4, 8, 4)
        pg_lbl = QLabel("Turn:"); pg_lbl.setFont(FONT_SMALL)
        pg_lbl.setStyleSheet(f"color: {FG_LBL};")
        sr_layout.addWidget(pg_lbl)
        self._page_slider = QSlider(Qt.Horizontal)
        self._page_slider.setMinimum(0); self._page_slider.setMaximum(1)
        self._page_slider.valueChanged.connect(self._on_slider)
        sr_layout.addWidget(self._page_slider, 1)
        right_layout.addWidget(slider_row)

        # Splitter: plot grid | stats
        self._vsplit = QSplitter(Qt.Vertical)
        self._vsplit.setStyleSheet(f"QSplitter::handle {{ background: {BORDER}; }}")

        self._grid_widget = QWidget(); self._grid_widget.setStyleSheet(f"background: {BG};")
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(0, 0, 0, 0); self._grid_layout.setSpacing(4)
        self._vsplit.addWidget(self._grid_widget)

        self._stats_fig    = plt.Figure(facecolor=MANTLE, dpi=96)
        self._stats_canvas = FigureCanvas(self._stats_fig)
        self._stats_canvas.setVisible(False)
        self._vsplit.addWidget(self._stats_canvas)

        right_layout.addWidget(self._vsplit, 1)
        content_layout.addWidget(right, 1)

    def _sep(self):
        f = QFrame(); f.setFrameShape(QFrame.VLine)
        f.setStyleSheet(f"color: {BORDER};"); f.setFixedHeight(28)
        return f

    def _build_sidebar(self):
        sl = self._sidebar_layout

        # DISPLAY
        sec = SidebarSection("Display")
        self._hist_cb    = QCheckBox("Marginal histograms"); self._hist_cb.setStyleSheet(CHK_SS)
        self._overlay_cb = QCheckBox("Stats overlay");       self._overlay_cb.setStyleSheet(CHK_SS)
        self._hist_cb.toggled.connect(self.render_all)
        self._overlay_cb.toggled.connect(self.render_all)
        sec.add(self._hist_cb); sec.add(self._overlay_cb)

        self._pt_slider     = make_slider(0.5, 12.0, 2.0, 1)
        self._alpha_slider  = make_slider(0.02, 1.0, 0.35, 2)
        self._bins_slider   = make_slider(10, 200, 60)
        self._smooth_slider = make_slider(1, 30, 1)
        self._sigma_slider  = make_slider(0.5, 10.0, 3.0, 1)
        for s in [self._pt_slider, self._alpha_slider,
                  self._bins_slider, self._smooth_slider, self._sigma_slider]:
            s.valueChanged.connect(self._debounce)
        sec.add_row("Point size",              self._pt_slider)
        sec.add_row("Alpha",                   self._alpha_slider)
        sec.add_row("Histogram bins",          self._bins_slider)
        sec.add_row("Axis smoothing (frames)", self._smooth_slider)
        sec.add_row("Track window (±σ)",       self._sigma_slider)
        sl.addWidget(sec)

        # PLOT MODE
        sec2 = SidebarSection("Plot Mode")
        self._mode_scatter = QRadioButton("Scatter");    self._mode_scatter.setStyleSheet(RB_SS)
        self._mode_heatmap = QRadioButton("Heatmap 2D"); self._mode_heatmap.setStyleSheet(RB_SS)
        self._mode_scatter.setChecked(True)
        self._mode_scatter.toggled.connect(self.render_all)
        sec2.add(self._mode_scatter); sec2.add(self._mode_heatmap)
        self._cmap_combo = QComboBox(); self._cmap_combo.setStyleSheet(COMBO_SS)
        self._cmap_combo.addItems(["turbo", "plasma", "inferno", "gist_rainbow",
                                   "jet", "RdYlBu", "Spectral", "gnuplot2",
                                   "CMRmap", "afmhot"])
        self._cmap_combo.currentTextChanged.connect(self.render_all)
        sec2.add_row("Colormap", self._cmap_combo)
        self._hbins_slider   = make_slider(50, 500, 300)
        self._hsmooth_slider = make_slider(0.0, 8.0, 2.0, 1)
        self._hbins_slider.valueChanged.connect(self._debounce)
        self._hsmooth_slider.valueChanged.connect(self._debounce)
        self._log_cb  = QCheckBox("Log color scale"); self._log_cb.setStyleSheet(CHK_SS); self._log_cb.setChecked(True)
        self._cbar_cb = QCheckBox("Show colorbar");   self._cbar_cb.setStyleSheet(CHK_SS)
        self._log_cb.toggled.connect(self.render_all)
        self._cbar_cb.toggled.connect(self.render_all)
        sec2.add_row("Heatmap bins",      self._hbins_slider)
        sec2.add_row("Smoothing (sigma)", self._hsmooth_slider)
        sec2.add(self._log_cb); sec2.add(self._cbar_cb)
        sl.addWidget(sec2)

        # PLAYBACK
        sec3 = SidebarSection("Playback")
        play_row = QWidget(); play_row.setStyleSheet("background: transparent;")
        pr = QHBoxLayout(play_row); pr.setContentsMargins(0, 0, 0, 0); pr.setSpacing(6)
        self._play_btn = QPushButton("▶  Play"); self._play_btn.setFont(FONT_MAIN)
        self._play_btn.setFixedWidth(100); self._play_btn.setFixedHeight(30)
        self._play_btn.setStyleSheet(f"""
            QPushButton {{ background: {PANEL}; border: 1px solid {SUCCESS};
                border-radius: 8px; color: {SUCCESS}; font-weight: 500; }}
            QPushButton:hover {{ background: {SUCCESS}; color: {CRUST}; }}
        """)
        self._play_btn.clicked.connect(self._toggle_play)
        self._speed_slider = make_slider(1, 30, 5)
        pr.addWidget(self._play_btn)
        sec3.add(play_row)
        sec3.add_row("Speed (fps)", self._speed_slider)
        sl.addWidget(sec3)

        # PARTICLE TRACKING
        sec4 = SidebarSection("Particle Tracking")
        self._track_entry = QLineEdit()
        self._track_entry.setFont(FONT_MONO)
        self._track_entry.setPlaceholderText("e.g. 42,100,203")
        self._track_entry.setStyleSheet(ENTRY_SS)
        track_btn = QPushButton("Track"); track_btn.setFont(FONT_MAIN)
        track_btn.setFixedWidth(70); track_btn.setFixedHeight(28)
        track_btn.setStyleSheet(f"""
            QPushButton {{ background: {PANEL}; border: 1px solid {ACCENT};
                border-radius: 8px; color: {ACCENT}; font-weight: 500; }}
            QPushButton:hover {{ background: {ACCENT}; color: {CRUST}; }}
        """)
        track_btn.clicked.connect(self._set_tracking)
        clear_btn = QPushButton("Clear tracking"); clear_btn.setFont(FONT_MAIN)
        clear_btn.setFixedHeight(28)
        clear_btn.setStyleSheet(f"""
            QPushButton {{ background: {PANEL}; border: 1px solid {ERROR};
                border-radius: 8px; color: {ERROR}; font-weight: 500; }}
            QPushButton:hover {{ background: {ERROR}; color: {CRUST}; }}
        """)
        clear_btn.clicked.connect(self._clear_tracking)
        track_row = QWidget(); track_row.setStyleSheet("background: transparent;")
        trl = QHBoxLayout(track_row); trl.setContentsMargins(0, 0, 0, 0)
        trl.addWidget(self._track_entry, 1); trl.addWidget(track_btn)
        self._track_lbl = QLabel("No particle tracked"); self._track_lbl.setFont(FONT_SMALL)
        self._track_lbl.setStyleSheet(f"color: {FG_DIM};")
        sec4.add(track_row); sec4.add(clear_btn); sec4.add(self._track_lbl)
        sl.addWidget(sec4)

    # ── Settings dict ─────────────────────────────────────────────────────

    def _get_settings(self) -> dict:
        return {
            "plot_mode":    "Scatter" if self._mode_scatter.isChecked() else "Heatmap 2D",
            "cmap":         self._cmap_combo.currentText(),
            "pt_size":      self._pt_slider.real_value(),
            "alpha":        self._alpha_slider.real_value(),
            "hist_bins":    self._bins_slider.real_value(),
            "smooth_n":     self._smooth_slider.real_value(),
            "sigma":        self._sigma_slider.real_value(),
            "show_hist":    self._hist_cb.isChecked(),
            "show_overlay": self._overlay_cb.isChecked(),
            "hmap_bins":    self._hbins_slider.real_value(),
            "smooth_sigma": self._hsmooth_slider.real_value(),
            "log_scale":    self._log_cb.isChecked(),
            "show_cbar":    self._cbar_cb.isChecked(),
        }

    def _debounce(self):
        self._debounce_timer.start(120)

    # ── Panel management ──────────────────────────────────────────────────

    def _add_panel(self):
        panel = PlotPanel(self, len(self._panels))
        self._panels.append(panel)
        if self.model.labels:
            panel.update_file_list(self.model.labels, self.model.labels[0])
        self._reflow_grid()
        if self.model.n_files: self.render_all()

    def _remove_panel(self):
        if len(self._panels) <= 1: return
        self._panels.pop().destroy_panel()
        self._reflow_grid()

    def _reflow_grid(self):
        n    = len(self._panels)
        cols = 1 if n == 1 else (2 if n <= 4 else 3)
        for i in reversed(range(self._grid_layout.count())):
            self._grid_layout.itemAt(i).widget().setParent(None)
        for i, panel in enumerate(self._panels):
            r, c = divmod(i, cols)
            self._grid_layout.addWidget(panel, r, c)
        for c in range(cols): self._grid_layout.setColumnStretch(c, 1)
        for r in range((n + cols - 1) // cols): self._grid_layout.setRowStretch(r, 1)

    # ── Legend ────────────────────────────────────────────────────────────

    def _update_legend(self):
        while self._legend_layout.count():
            item = self._legend_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        for finfo in self.model.files:
            btn = QPushButton(f"● {finfo.label}"); btn.setFont(FONT_SMALL)
            btn.setStyleSheet(f"""
                QPushButton {{ color: {finfo.color}; background: transparent;
                    border: none; padding: 2px 6px; }}
                QPushButton:checked {{ background: {PANEL}; border-radius: 4px;
                    border: 1px solid {finfo.color}; }}
            """)
            btn.setCheckable(True)
            btn.setChecked(finfo.label == self._selected_file)
            lbl = finfo.label
            btn.clicked.connect(lambda _c, l=lbl: self._select_file(l))
            self._legend_layout.addWidget(btn)

    def _select_file(self, label):
        self._selected_file = label
        self._update_legend()
        if self.stats_btn.isChecked(): self._redraw_stats()

    # ── File open ─────────────────────────────────────────────────────────

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open SDDS file", "", "All files (*.*)")
        if not path: return
        try:
            pages = read_sdds_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Parse error", str(e)); return
        if not pages:
            QMessageBox.warning(self, "Empty file", "No data pages found."); return
        finfo = self.model.load_file(path, pages)
        if self._selected_file is None: self._selected_file = finfo.label
        for panel in self._panels:
            panel.update_file_list(self.model.labels, self.model.labels[-1])
        n = self.model.max_pages
        self._page_slider.setMaximum(max(1, n - 1))
        self._page_slider.setValue(0)
        self.current_page = 0
        self._update_legend()
        self.render_all()

    # ── Render ────────────────────────────────────────────────────────────

    def render_all(self):
        if not self.model.n_files: return
        settings = self._get_settings()
        for panel in self._panels:
            panel.render(self.current_page, settings)
        for finfo in self.model.files:
            if finfo.n_pages > self.current_page:
                pg    = finfo.page(self.current_page)
                n     = self.model.max_pages
                step  = pg["params"].get("Step", "?")
                s_val = pg["params"].get("s")
                npart = pg["data"].shape[0]
                s_str = f"   s = {s_val:.4f} m" if isinstance(s_val, float) else ""
                self._page_lbl.setText(f"Turn {self.current_page + 1} / {n}")
                self._param_lbl.setText(f"Step {step}{s_str}   |   {npart:,} particles")
                break
        if self.stats_btn.isChecked(): self._redraw_stats()

    # ── Playback ──────────────────────────────────────────────────────────

    def _on_slider(self, val):
        if not self.model.n_files: return
        self.current_page = val
        self.render_all()

    def _toggle_play(self):
        if self._playing:
            self._playing = False; self._play_timer.stop()
            self._play_btn.setText("▶  Play")
        else:
            if not self.model.n_files: return
            self._playing = True; self._play_btn.setText("⏸  Pause")
            self._play_timer.start(int(1000 / max(1, self._speed_slider.real_value())))

    def _advance_frame(self):
        if not self._playing: return
        fps = max(1, self._speed_slider.real_value())
        self._play_timer.setInterval(int(1000 / fps))
        self.current_page = (self.current_page + 1) % self.model.max_pages
        self._page_slider.blockSignals(True)
        self._page_slider.setValue(self.current_page)
        self._page_slider.blockSignals(False)
        self.render_all()

    # ── Particle tracking ─────────────────────────────────────────────────

    def _set_tracking(self):
        txt = self._track_entry.text().strip()
        try:
            ids = [int(x.strip()) for x in txt.split(",") if x.strip()]
        except ValueError:
            QMessageBox.warning(self, "Invalid IDs", "Enter comma-separated integers."); return
        self._tracked_ids = ids
        for finfo in self.model.files: finfo.clear_trajectory_cache()
        self._track_lbl.setText(f"Tracking: {ids}" if ids else "No particle tracked")
        self._track_lbl.setStyleSheet(
            f"color: {RAN_CLR}; font-size: 10px;" if ids else f"color: {FG_DIM}; font-size: 10px;")
        for p in self._panels: p._invalidate()
        self.render_all()

    def _clear_tracking(self):
        self._tracked_ids = []
        for finfo in self.model.files: finfo.clear_trajectory_cache()
        self._track_lbl.setText("No particle tracked")
        self._track_lbl.setStyleSheet(f"color: {FG_DIM}; font-size: 10px;")
        for p in self._panels: p._invalidate()
        self.render_all()

    # ── Beam loss ─────────────────────────────────────────────────────────

    def _toggle_beam_loss(self, checked):
        if not checked:
            self._show_loss = False
            for p in self._panels: p._invalidate()
            self.render_all(); return
        total = sum(f.n_pages * 10000 for f in self.model.files)
        if total > 5_000_000:
            r = QMessageBox.question(self, "Beam Loss",
                f"Large dataset (~{total:,} particle-pages). Continue?",
                QMessageBox.Yes | QMessageBox.No)
            if r != QMessageBox.Yes:
                self.loss_btn.setChecked(False); return
        for finfo in self.model.files: finfo.precompute_loss_map()
        self._show_loss = True
        for p in self._panels: p._invalidate()
        self.render_all()

    # ── Stats panel ───────────────────────────────────────────────────────

    def _toggle_stats(self, checked):
        self._stats_canvas.setVisible(checked)
        total = self._vsplit.height()
        if checked:
            self._vsplit.setSizes([int(total * 0.60), int(total * 0.40)])
            self._redraw_stats()
        else:
            self._vsplit.setSizes([total, 0])

    def _redraw_stats(self):
        if not self.model.n_files: return
        files_to_show = self.model.files
        if self._selected_file:
            sel = self.model.file_by_label(self._selected_file)
            if sel: files_to_show = [sel]
        draw_stats_panel(self._stats_fig, files_to_show, self.current_page)
        self._stats_canvas.draw_idle()

    # ── Corr matrix ───────────────────────────────────────────────────────

    def _open_corr_matrix(self):
        if not self.model.n_files:
            QMessageBox.warning(self, "Corr Matrix", "Load a file first."); return
        finfo = self.model.file_by_label(self._selected_file) or self.model.files[0]
        open_corr_matrix(self, finfo, self.current_page)

    # ── RF bucket ─────────────────────────────────────────────────────────

    def _open_rf_dialog(self):
        def _set_ramp(data): self._rf_ramp_data = data
        result = open_rf_dialog(self, self._rf_params, _set_ramp)
        if result is None: return
        if result == {}:
            self._rf_params = None; self._rf_ramp_data = None
            self._show_rf_bucket = False
            self.rf_btn.setText("RF Bucket")
            self.rf_btn.setStyleSheet(f"""
                QPushButton {{ background: {PANEL}; border: 1px solid {SUCCESS};
                    border-radius: 8px; color: {SUCCESS}; font-weight: 500; }}
                QPushButton:hover {{ background: {SUCCESS}; color: {CRUST}; }}
            """)
        else:
            self._rf_params = result; self._show_rf_bucket = True
            self.rf_btn.setText("* RF Bucket")
            self.rf_btn.setStyleSheet(f"""
                QPushButton {{ background: {SUCCESS}22; border: 1px solid {SUCCESS};
                    border-radius: 8px; color: {SUCCESS}; font-weight: 500; }}
                QPushButton:hover {{ background: {SUCCESS}; color: {CRUST}; }}
            """)
        for p in self._panels: p._invalidate()
        self.render_all()

    # ── Optics ────────────────────────────────────────────────────────────

    def _open_optics(self):
        if self._optics_win and self._optics_win.isVisible():
            self._optics_win.raise_(); self._optics_win.activateWindow(); return
        self._optics_win = OpticsWindow(parent=None)
        self._optics_win.show()

    # ── Export ────────────────────────────────────────────────────────────

    def _export(self):
        if not self.model.n_files:
            QMessageBox.warning(self, "Export", "No data loaded."); return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export panels", "", "PNG image (*.png);;PDF (*.pdf)")
        if not path: return
        import matplotlib.pyplot as _plt
        from theme import style_ax as _sax, AX_BG, SPINE_C
        n    = len(self._panels)
        cols = 1 if n == 1 else (2 if n <= 4 else 3)
        rows = (n + cols - 1) // cols
        fig, axes_arr = _plt.subplots(rows, cols, figsize=(cols*5, rows*4), facecolor=BG)
        axes_flat = np.array(axes_arr).flatten() if n > 1 else [axes_arr]
        settings  = self._get_settings()
        for i, panel in enumerate(self._panels):
            ax = axes_flat[i]; _sax(ax)
            pages = panel.get_pages()
            if not pages: continue
            pg = pages[min(self.current_page, len(pages)-1)]
            xn = panel.x_combo.currentText(); yn = panel.y_combo.currentText()
            xd = pg["data"][:, COLUMNS.index(xn)]
            yd = pg["data"][:, COLUMNS.index(yn)]
            xu = COL_UNITS.get(xn, ""); yu = COL_UNITS.get(yn, "")
            if settings["plot_mode"] == "Scatter":
                ax.scatter(xd, yd, s=settings["pt_size"], c=panel._color,
                           alpha=settings["alpha"], linewidths=0, zorder=2)
            ax.set_xlabel((xn+"  ["+xu+"]") if xu else xn, color=FG, fontsize=10)
            ax.set_ylabel((yn+"  ["+yu+"]") if yu else yn, color=FG, fontsize=10)
            ax.set_title(panel.file_combo.currentText(), color=FG_LBL, fontsize=9, pad=3)
        for j in range(n, len(axes_flat)): axes_flat[j].set_visible(False)
        fig.savefig(path, dpi=150, facecolor=BG, bbox_inches="tight")
        if not path.endswith(".pdf"):
            fig.savefig(path.rsplit(".",1)[0]+".pdf", facecolor=BG, bbox_inches="tight")
        _plt.close(fig)
        QMessageBox.information(self, "Export", f"Saved to {path}")

    # ── Session ───────────────────────────────────────────────────────────

    def _save_session(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Session", "", "Session (*.json)")
        if not path: return
        try:
            session = {
                "files": self.model.to_session(), "current_page": self.current_page,
                "panels": [{"file_label": p.file_combo.currentText(),
                             "x": p.x_combo.currentText(), "y": p.y_combo.currentText(),
                             "ax_mode": p.mode_combo.currentText(),
                             "bkt": p.bkt_btn.isChecked()} for p in self._panels],
                "plot_mode":    "Scatter" if self._mode_scatter.isChecked() else "Heatmap 2D",
                "cmap":         self._cmap_combo.currentText(),
                "hmap_bins":    self._hbins_slider.real_value(),
                "smooth_sigma": self._hsmooth_slider.real_value(),
                "log_scale":    self._log_cb.isChecked(),
                "show_hist":    self._hist_cb.isChecked(),
                "hist_bins":    self._bins_slider.real_value(),
                "pt_size":      self._pt_slider.real_value(),
                "alpha":        self._alpha_slider.real_value(),
                "smooth_n":     self._smooth_slider.real_value(),
                "sigma":        self._sigma_slider.real_value(),
                "overlay":      self._overlay_cb.isChecked(),
                "rf_params":    self._rf_params,
                "show_rf":      self._show_rf_bucket,
            }
            with open(path, "w") as f: json.dump(session, f, indent=2)
            QMessageBox.information(self, "Session saved", f"Saved to {Path(path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Save error", str(e))

    def _load_session(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Session", "", "Session (*.json)")
        if not path: return
        try:
            with open(path) as f: session = json.load(f)
            failed = self.model.restore_session_files(session.get("files", []), read_sdds_file)
            for fp in failed:
                QMessageBox.warning(self, "File missing", f"{fp} not found — skipping.")
            if not self.model.n_files: return
            if self._selected_file is None: self._selected_file = self.model.labels[0]
            if session.get("plot_mode") == "Heatmap 2D": self._mode_heatmap.setChecked(True)
            else: self._mode_scatter.setChecked(True)
            self._cmap_combo.setCurrentText(session.get("cmap", "turbo"))
            self._log_cb.setChecked(session.get("log_scale", True))
            self._hist_cb.setChecked(session.get("show_hist", False))
            self._overlay_cb.setChecked(session.get("overlay", False))
            self._rf_params = session.get("rf_params", None)
            self._show_rf_bucket = session.get("show_rf", False)
            if self._rf_params:
                self.rf_btn.setText("* RF Bucket")
            saved_panels = session.get("panels", [])
            labels = self.model.labels
            while len(self._panels) < len(saved_panels): self._add_panel()
            while len(self._panels) > len(saved_panels) and len(self._panels) > 1:
                self._panels.pop().destroy_panel()
            for panel, pdata in zip(self._panels, saved_panels):
                panel.update_file_list(labels, pdata.get("file_label", labels[0]))
                panel.x_combo.setCurrentText(pdata.get("x", "t"))
                panel.y_combo.setCurrentText(pdata.get("y", "p"))
                panel._update_mode_options()
                panel.mode_combo.setCurrentText(pdata.get("ax_mode", "Roll"))
                panel.bkt_btn.setChecked(pdata.get("bkt", False))
                panel._invalidate()
            self._reflow_grid(); self._update_legend()
            n = self.model.max_pages
            self.current_page = min(session.get("current_page", 0), n-1)
            self._page_slider.setMaximum(max(1, n-1))
            self._page_slider.setValue(self.current_page)
            self.render_all()
        except Exception as e:
            QMessageBox.critical(self, "Load session error", str(e))

    # ── Window events ─────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._playing = False; self._play_timer.stop()
        for panel in self._panels: plt.close(panel.fig)
        plt.close(self._stats_fig)
        event.accept()

    def keyPressEvent(self, event):
        key = event.key(); mods = event.modifiers()
        if key == Qt.Key_O and mods & Qt.ControlModifier: self._open_file()
        elif key == Qt.Key_Space: self._toggle_play()
        elif key in (Qt.Key_Right, Qt.Key_Up):
            if self.model.n_files:
                self.current_page = min(self.current_page+1, self.model.max_pages-1)
                self._page_slider.blockSignals(True); self._page_slider.setValue(self.current_page); self._page_slider.blockSignals(False)
                self.render_all()
        elif key in (Qt.Key_Left, Qt.Key_Down):
            if self.model.n_files:
                self.current_page = max(self.current_page-1, 0)
                self._page_slider.blockSignals(True); self._page_slider.setValue(self.current_page); self._page_slider.blockSignals(False)
                self.render_all()
        else: super().keyPressEvent(event)


# Re-export TEAL so _btn() in this file can use it without extra import
from theme import TEAL
