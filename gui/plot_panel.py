"""
RanBeam — gui/plot_panel.py
============================
PlotPanel: one phase-space plot panel.

Performance design
------------------
The key to fast turn-by-turn animation is the blit pipeline:

  1. On first render (or after a layout change such as toggling histograms),
     draw the full figure once with canvas.draw() — this caches the background.

  2. On every subsequent frame:
       a. Restore the cached background with canvas.restore_region().
       b. Update only the data inside existing artists (set_offsets /
          set_data) — NO new artist creation.
       c. Re-draw only the changed artists with ax.draw_artist().
       d. Flush with canvas.blit(ax.bbox).

  This skips re-drawing the axes, ticks, grid, and all static chrome —
  which is the expensive part — and only repaints the actual data pixels.

Blit is bypassed (full redraw) only when:
  - Layout changes: histogram toggle, colorbar toggle
  - Axis limits change: mode switch, file change, column change
  - Settings change: plot mode, point size, alpha, etc.

These are rare events and don't happen during playback.
"""

from __future__ import annotations
from collections import deque

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.gridspec import GridSpec
from matplotlib.colors import LogNorm, Normalize
from scipy.ndimage import gaussian_filter

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt

from theme import (
    BG, AX_BG, PANEL, BORDER, FILE_COLORS, TRACK_COLORS, FG,
    RAN_CLR, style_ax,
)
from models.sdds_loader import COLUMNS, COL_UNITS, DEFAULT_PAIRS
from physics.beam_stats import draw_stats_overlay
from physics.rf_bucket import compute_rf_separatrix

# Heatmap cache size limit (number of entries per panel)
_HMAP_CACHE_MAX = 50


class PlotPanel(QWidget):

    def __init__(self, app, panel_index: int, parent=None):
        super().__init__(parent)
        self.app   = app
        self.index = panel_index

        # ── State ─────────────────────────────────────────────────────────
        self._color       = FILE_COLORS[0]
        self._ax_history  = deque()
        self._ax_cols     = None
        self._hmap_cache  = {}
        self._hmap_key    = None
        self._cbar        = None
        self._fixed_xlim  = None
        self._fixed_ylim  = None

        # Blit state
        self._bg_cache      = None   # saved background image
        self._blit_artists  = []     # artists redrawn each frame
        self._needs_full    = True   # force full draw on next render
        self._last_settings = None   # detect settings changes

        # Overlay artists (created once, updated in-place)
        self._scatter_artist  = None
        self._imshow_artist   = None
        self._overlay_artists = {}   # from draw_stats_overlay
        self._rf_line         = None
        self._hist_artists    = {}   # {ax_hx: artist, ax_hy: artist}
        self._loss_scatter    = None
        self._track_artists   = {}   # {pid: (trail_line, dot_scatter)}

        # Layout tracking
        self._show_hist_last  = False
        self._show_cbar_last  = False
        self._mode_last       = ""

        pair = DEFAULT_PAIRS[panel_index % len(DEFAULT_PAIRS)]

        # ── Widget styling ────────────────────────────────────────────────
        self.setObjectName("plotpanel")
        self._set_border(FILE_COLORS[0])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        # ── Header row ────────────────────────────────────────────────────
        hdr = QWidget()
        hdr.setStyleSheet(f"background: #0a0a1a; border-radius: 4px;")
        hdr.setFixedHeight(30)
        hl  = QHBoxLayout(hdr)
        hl.setContentsMargins(4, 2, 4, 2)
        hl.setSpacing(4)

        self.file_combo = QComboBox(); self.file_combo.setFixedWidth(110)
        self.file_combo.currentTextChanged.connect(self._on_file_change)

        self.x_combo = QComboBox(); self.x_combo.addItems(COLUMNS)
        self.x_combo.setCurrentText(pair[0]); self.x_combo.setFixedWidth(70)
        self.x_combo.currentTextChanged.connect(self._on_axis_change)

        self.y_combo = QComboBox(); self.y_combo.addItems(COLUMNS)
        self.y_combo.setCurrentText(pair[1]); self.y_combo.setFixedWidth(70)
        self.y_combo.currentTextChanged.connect(self._on_axis_change)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Auto", "Roll", "Track", "Fixed"])
        self.mode_combo.setCurrentText("Roll"); self.mode_combo.setFixedWidth(90)
        self.mode_combo.currentTextChanged.connect(self._on_mode_change)

        self._lock_btn = QPushButton("[ ]")
        self._lock_btn.setFixedWidth(28); self._lock_btn.setFixedHeight(22)
        self._lock_btn.setToolTip("Lock current axis limits (Fixed mode)")
        self._lock_btn.setStyleSheet("QPushButton { font-size: 10px; padding: 0; }")
        self._lock_btn.clicked.connect(self._lock_axes)

        self.rf_lbl = QLabel("RF")
        self.rf_lbl.setStyleSheet(
            "color: #1a3a2a; background: #1a3a2a; "
            "border-radius: 3px; padding: 1px 4px; "
            "font-size: 10px; font-weight: bold;")
        self.rf_lbl.setFixedHeight(18)

        self.bkt_btn = QPushButton("Bkt")
        self.bkt_btn.setCheckable(True)
        self.bkt_btn.setFixedWidth(36); self.bkt_btn.setFixedHeight(20)
        self.bkt_btn.setStyleSheet("QPushButton { font-size: 10px; padding: 0; }")
        self.bkt_btn.toggled.connect(lambda _: self._invalidate())

        for w in [self.file_combo,
                  self._sep(), QLabel("X"), self.x_combo,
                  self._sep(), QLabel("Y"), self.y_combo,
                  self._sep(), self.mode_combo, self._lock_btn,
                  self.rf_lbl, self.bkt_btn]:
            hl.addWidget(w)
        hl.addStretch()
        layout.addWidget(hdr)

        # ── Matplotlib canvas ─────────────────────────────────────────────
        self.fig = plt.Figure(facecolor=BG, dpi=96)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.canvas)

        # Invalidate blit cache when canvas is resized
        self.canvas.mpl_connect("resize_event", self._on_resize)

        self._draw_empty()
        self._update_mode_options()

    # ── Qt helpers ────────────────────────────────────────────────────────

    def _sep(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.VLine)
        f.setStyleSheet(f"color: {BORDER};")
        f.setFixedWidth(1)
        return f

    def _set_border(self, color: str) -> None:
        self.setStyleSheet(
            f"QWidget#plotpanel {{ border: 2px solid {color}; "
            f"border-radius: 6px; background: {PANEL}; }}")

    # ── Invalidation helpers ──────────────────────────────────────────────

    def _invalidate(self) -> None:
        """Force a full redraw on the next render() call."""
        self._needs_full   = True
        self._bg_cache     = None
        self._blit_artists = []

    def _on_resize(self, _event=None) -> None:
        self._invalidate()

    def _on_file_change(self, label: str) -> None:
        finfo = self.app.model.file_by_label(label)
        color = finfo.color if finfo else FILE_COLORS[0]
        self._color = color
        self._set_border(color)
        self._ax_history.clear()
        self._hmap_cache.clear()
        self._invalidate()
        self.app.render_all()

    def _on_axis_change(self) -> None:
        self._ax_history.clear()
        self._hmap_cache.clear()
        self._update_mode_options()
        self._invalidate()
        self.app.render_all()

    def _on_mode_change(self) -> None:
        self._ax_history.clear()
        self._invalidate()
        self.app.render_all()

    def _lock_axes(self) -> None:
        if not self.fig.axes:
            return
        ax = self.fig.axes[0]
        self._fixed_xlim = ax.get_xlim()
        self._fixed_ylim = ax.get_ylim()
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentText("Fixed")
        self.mode_combo.blockSignals(False)
        self.app.render_all()

    def _update_mode_options(self) -> None:
        xn = self.x_combo.currentText()
        yn = self.y_combo.currentText()
        has_ref = xn in ("p", "t") or yn in ("p", "t")
        cur = self.mode_combo.currentText()
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        opts = (["Auto", "Roll", "Track", "Fixed", "Roll+Δ", "Track+Δ"]
                if has_ref else ["Auto", "Roll", "Track", "Fixed"])
        self.mode_combo.addItems(opts)
        if "Δ" in cur and not has_ref:
            cur = "Roll"
        self.mode_combo.setCurrentText(
            cur if cur in opts else "Roll")
        self.mode_combo.blockSignals(False)

    # ── File list update ──────────────────────────────────────────────────

    def update_file_list(self, labels: list[str], default: str | None = None):
        self.file_combo.blockSignals(True)
        self.file_combo.clear()
        self.file_combo.addItems(labels)
        if default and default in labels:
            self.file_combo.setCurrentText(default)
        self.file_combo.blockSignals(False)
        finfo = self.app.model.file_by_label(self.file_combo.currentText())
        if finfo:
            self._color = finfo.color

    def get_pages(self):
        finfo = self.app.model.file_by_label(self.file_combo.currentText())
        return finfo.pages if finfo else None

    # ── Empty state ───────────────────────────────────────────────────────

    def _draw_empty(self) -> None:
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        style_ax(ax)
        ax.text(0.5, 0.5, "Open an SDDS file to begin",
                transform=ax.transAxes, ha="center", va="center",
                color="#888888", fontsize=12)
        ax.set_xticks([]); ax.set_yticks([])
        self.canvas.draw_idle()
        self._needs_full = True

    # ── Axis limit computation ────────────────────────────────────────────

    def _compute_limits(self, xd, yd, settings: dict):
        ax_mode  = self.mode_combo.currentText()
        base     = ax_mode.replace("+Δ", "")
        smooth_n = settings["smooth_n"]

        if base == "Fixed":
            return self._fixed_xlim, self._fixed_ylim

        if base == "Roll":
            xc    = float(xd.mean()); yc = float(yd.mean())
            xhalf = (float(xd.max() - xd.min()) / 2.0) or 1e-10
            yhalf = (float(yd.max() - yd.min()) / 2.0) or 1e-10
            self._ax_history.append((xhalf * 1.05, yhalf * 1.05))
            while len(self._ax_history) > max(1, smooth_n):
                self._ax_history.popleft()
            arr  = list(self._ax_history)
            sxh  = sum(a[0] for a in arr) / len(arr)
            syh  = sum(a[1] for a in arr) / len(arr)
            return (xc - sxh, xc + sxh), (yc - syh, yc + syh)

        if base == "Track":
            nsig = settings["sigma"]
            xc, xs = float(xd.mean()), float(xd.std()) or 1e-10
            yc, ys = float(yd.mean()), float(yd.std()) or 1e-10
            self._ax_history.append((xs, ys))
            while len(self._ax_history) > max(1, smooth_n):
                self._ax_history.popleft()
            arr  = list(self._ax_history)
            sxs  = sum(a[0] for a in arr) / len(arr)
            sys_ = sum(a[1] for a in arr) / len(arr)
            return (xc - nsig * sxs, xc + nsig * sxs), \
                   (yc - nsig * sys_, yc + nsig * sys_)

        return None, None   # Auto

    # ── Settings change detection ─────────────────────────────────────────

    def _settings_changed(self, settings: dict, xn: str, yn: str) -> bool:
        key = (settings["plot_mode"], settings["show_hist"],
               settings["show_cbar"] and settings["plot_mode"] == "Heatmap 2D",
               settings["pt_size"], settings["alpha"],
               settings["hmap_bins"], settings["smooth_sigma"],
               settings["log_scale"], xn, yn)
        if key != self._last_settings:
            self._last_settings = key
            return True
        return False

    # ── Main render ───────────────────────────────────────────────────────

    def render(self, page_idx: int, settings: dict) -> None:
        pages = self.get_pages()
        if not pages:
            self._draw_empty()
            return

        pg     = pages[min(page_idx, len(pages) - 1)]
        data   = pg["data"]
        params = pg["params"]

        xn = self.x_combo.currentText()
        yn = self.y_combo.currentText()
        xi = COLUMNS.index(xn)
        yi = COLUMNS.index(yn)
        xd = data[:, xi].copy()
        yd = data[:, yi].copy()

        # Δ centering
        center_ref = "Δ" in self.mode_combo.currentText()
        p_central  = params.get("pCentral", None)
        t_central  = params.get("PassCentralTime", None)
        if center_ref:
            if xn == "p" and p_central is not None: xd -= float(p_central)
            if yn == "p" and p_central is not None: yd -= float(p_central)
            if xn == "t" and t_central is not None: xd -= float(t_central)
            if yn == "t" and t_central is not None: yd -= float(t_central)

        xu  = COL_UNITS.get(xn, "")
        yu  = COL_UNITS.get(yn, "")
        pfx = "Δ" if center_ref else ""
        xlbl = (pfx + xn + "  [" + xu + "]") if xu else pfx + xn
        ylbl = (pfx + yn + "  [" + yu + "]") if yu else pfx + yn

        # Detect if we need a full redraw (layout / settings changed)
        col_key   = (xn, yn)
        if col_key != self._ax_cols:
            self._ax_history.clear()
            self._ax_cols = col_key

        show_hist = settings["show_hist"]
        show_cbar = settings["show_cbar"] and settings["plot_mode"] == "Heatmap 2D"

        layout_changed = (show_hist   != self._show_hist_last or
                          show_cbar   != self._show_cbar_last)
        settings_changed = self._settings_changed(settings, xn, yn)

        if self._needs_full or layout_changed or settings_changed:
            self._full_redraw(xd, yd, xn, yn, xlbl, ylbl,
                              show_hist, show_cbar, settings,
                              params, p_central, center_ref,
                              page_idx, pages, xi, yi)
            self._show_hist_last = show_hist
            self._show_cbar_last = show_cbar
            self._needs_full     = False
            return

        # ── Fast blit path ────────────────────────────────────────────────
        self._blit_update(xd, yd, xn, yn, xlbl, ylbl,
                          show_hist, show_cbar, settings,
                          params, p_central, center_ref,
                          page_idx, pages, xi, yi)

    # ── Full redraw (rare) ────────────────────────────────────────────────

    def _build_axes(self, show_hist: bool, show_cbar: bool):
        """Tear down and rebuild the figure layout."""
        self.fig.clear()
        self._cbar           = None
        self._scatter_artist = None
        self._imshow_artist  = None
        self._overlay_artists = {}
        self._rf_line        = None
        self._hist_artists   = {}
        self._loss_scatter   = None
        self._track_artists  = {}
        self.fig.patch.set_facecolor(BG)

        right = 0.82 if show_cbar else 0.97
        if show_hist:
            gs = GridSpec(2, 2, figure=self.fig,
                          width_ratios=[4, 1], height_ratios=[1, 4],
                          hspace=0.03, wspace=0.03,
                          left=0.12, right=right, top=0.97, bottom=0.12)
            ax_s  = self.fig.add_subplot(gs[1, 0])
            ax_hx = self.fig.add_subplot(gs[0, 0], sharex=ax_s)
            ax_hy = self.fig.add_subplot(gs[1, 1], sharey=ax_s)
            for ax in (ax_s, ax_hx, ax_hy):
                style_ax(ax)
            return ax_s, ax_hx, ax_hy
        else:
            ax = self.fig.add_subplot(111)
            style_ax(ax)
            self.fig.subplots_adjust(
                left=0.12, right=right, top=0.97, bottom=0.12)
            return ax, None, None

    def _full_redraw(self, xd, yd, xn, yn, xlbl, ylbl,
                     show_hist, show_cbar, settings,
                     params, p_central, center_ref,
                     page_idx, pages, xi, yi):
        ax_main, ax_hx, ax_hy = self._build_axes(show_hist, show_cbar)
        mode  = settings["plot_mode"]
        xlim, ylim = self._compute_limits(xd, yd, settings)

        # ── Primary data ──────────────────────────────────────────────────
        if mode == "Scatter":
            self._scatter_artist = ax_main.scatter(
                xd, yd,
                s=settings["pt_size"], c=self._color,
                alpha=settings["alpha"], linewidths=0, zorder=2)

        elif mode == "Heatmap 2D":
            h, xe, ye = self._get_heatmap(
                xd, yd, page_idx, settings["hmap_bins"],
                settings["smooth_sigma"])
            norm    = self._make_norm(h, settings["log_scale"])
            cmap_fn = plt.get_cmap(settings["cmap"]).copy()
            cmap_fn.set_bad(color=AX_BG)
            self._imshow_artist = ax_main.imshow(
                h, origin="lower", aspect="auto",
                extent=[xe[0], xe[-1], ye[0], ye[-1]],
                cmap=cmap_fn, norm=norm,
                interpolation="gaussian", zorder=2)
            ax_main.set_xlim(xe[0], xe[-1])
            ax_main.set_ylim(ye[0], ye[-1])
            if show_cbar:
                self._cbar = self.fig.colorbar(
                    self._imshow_artist, ax=ax_main,
                    fraction=0.046, pad=0.02)
                self._cbar.ax.tick_params(colors=FG, labelsize=8)
                from theme import SPINE_C
                self._cbar.outline.set_edgecolor(SPINE_C)
                plt.setp(self._cbar.ax.yaxis.get_ticklabels(), color=FG)
                self._cbar.ax._colorbar_axes = True

        # ── Histograms ────────────────────────────────────────────────────
        if show_hist and ax_hx is not None:
            hb = settings["hist_bins"]
            self._hist_artists["hx_patches"] = ax_hx.hist(
                xd, bins=hb, color=self._color, alpha=0.75, linewidth=0)[2]
            ax_hx.tick_params(labelbottom=False, colors=FG, labelsize=8)
            self._hist_artists["hy_patches"] = ax_hy.hist(
                yd, bins=hb, color=self._color, alpha=0.75,
                orientation="horizontal", linewidth=0)[2]
            ax_hy.tick_params(labelleft=False, colors=FG, labelsize=8)

        # ── Axis limits ───────────────────────────────────────────────────
        if xlim: ax_main.set_xlim(xlim)
        if ylim: ax_main.set_ylim(ylim)

        # ── Labels ────────────────────────────────────────────────────────
        ax_main.set_xlabel(xlbl, color=FG, fontsize=10)
        ax_main.set_ylabel(ylbl, color=FG, fontsize=10)

        # ── Stats overlay ─────────────────────────────────────────────────
        if settings["show_overlay"]:
            self._overlay_artists = draw_stats_overlay(
                ax_main, xd, yd, self._color, xn, yn,
                p_central, artists=None)
        else:
            self._overlay_artists = {}

        # ── Tracking / loss / RF (initial) ───────────────────────────────
        self._draw_tracking(ax_main, pages, page_idx, xi, yi)
        self._draw_loss(ax_main, pages, page_idx, xi, yi)
        self._draw_rf(ax_main, params, xn, yn, xd, yd, center_ref)
        self._update_rf_label(center_ref, xn, yn)
        if self.bkt_btn.isChecked():
            self._apply_bucket_view(ax_main, params, xn, yn, xd, yd)

        # ── Collect blit artists (data only — not static chrome) ────────────
        self._blit_artists = []
        if self._scatter_artist:
            self._blit_artists.append((ax_main, self._scatter_artist))
        if self._imshow_artist:
            self._blit_artists.append((ax_main, self._imshow_artist))
        for a in self._overlay_artists.values():
            self._blit_artists.append((ax_main, a))
        if self._rf_line:
            self._blit_artists.append((ax_main, self._rf_line))
        if self._loss_scatter:
            self._blit_artists.append((ax_main, self._loss_scatter))
        for line, dot in self._track_artists.values():
            if line: self._blit_artists.append((ax_main, line))
            if dot:  self._blit_artists.append((ax_main, dot))

        # ── Draw & cache background (data artists hidden so cache is clean) ──
        for _ax, _artist in self._blit_artists:
            _artist.set_visible(False)
        self.canvas.draw()
        self._bg_cache = self.canvas.copy_from_bbox(self.fig.bbox)
        for _ax, _artist in self._blit_artists:
            _artist.set_visible(True)

    # ── Blit update (fast path) ───────────────────────────────────────────

    def _blit_update(self, xd, yd, xn, yn, xlbl, ylbl,
                     show_hist, show_cbar, settings,
                     params, p_central, center_ref,
                     page_idx, pages, xi, yi):
        """
        Update only data artists in-place, then blit.
        No new artist creation, no axes teardown.
        """
        ax_list = [a for a in self.fig.axes
                   if not getattr(a, "_colorbar_axes", False)]
        if not ax_list:
            self._needs_full = True
            return

        ax_main = ax_list[0]
        ax_hx   = ax_list[1] if show_hist and len(ax_list) > 1 else None
        ax_hy   = ax_list[2] if show_hist and len(ax_list) > 2 else None

        mode = settings["plot_mode"]

        # ── Scatter ───────────────────────────────────────────────────────
        if mode == "Scatter" and self._scatter_artist is not None:
            self._scatter_artist.set_offsets(np.c_[xd, yd])

        # ── Heatmap ───────────────────────────────────────────────────────
        elif mode == "Heatmap 2D" and self._imshow_artist is not None:
            h, xe, ye = self._get_heatmap(
                xd, yd, page_idx, settings["hmap_bins"],
                settings["smooth_sigma"])
            norm = self._make_norm(h, settings["log_scale"])
            self._imshow_artist.set_data(h)
            self._imshow_artist.set_norm(norm)
            self._imshow_artist.set_extent([xe[0], xe[-1], ye[0], ye[-1]])

        # ── Axis limits ───────────────────────────────────────────────────
        xlim, ylim = self._compute_limits(xd, yd, settings)
        if xlim: ax_main.set_xlim(xlim)
        if ylim: ax_main.set_ylim(ylim)

        # ── Stats overlay ─────────────────────────────────────────────────
        if settings["show_overlay"] and self._overlay_artists:
            self._overlay_artists = draw_stats_overlay(
                ax_main, xd, yd, self._color, xn, yn,
                p_central, artists=self._overlay_artists)
        elif settings["show_overlay"] and not self._overlay_artists:
            # Overlay was off before; need full redraw to create artists
            self._needs_full = True
            return

        # ── Histograms (update bin data) ──────────────────────────────────
        if show_hist and ax_hx is not None:
            # Histograms require artist rebuild — just redraw those axes
            ax_hx.cla(); style_ax(ax_hx)
            ax_hy.cla(); style_ax(ax_hy)
            hb = settings["hist_bins"]
            ax_hx.hist(xd, bins=hb, color=self._color, alpha=0.75, linewidth=0)
            ax_hx.tick_params(labelbottom=False, colors=FG, labelsize=8)
            ax_hy.hist(yd, bins=hb, color=self._color, alpha=0.75,
                       orientation="horizontal", linewidth=0)
            ax_hy.tick_params(labelleft=False, colors=FG, labelsize=8)

        # ── RF / tracking / loss ──────────────────────────────────────────
        self._update_rf_line(ax_main, params, xn, yn, xd, yd, center_ref)
        self._update_rf_label(center_ref, xn, yn)
        self._draw_tracking(ax_main, pages, page_idx, xi, yi)
        self._draw_loss(ax_main, pages, page_idx, xi, yi)

        # ── Blit ─────────────────────────────────────────────────────────
        if self._bg_cache is None:
            self.canvas.draw()
            self._bg_cache = self.canvas.copy_from_bbox(self.fig.bbox)

        self.canvas.restore_region(self._bg_cache)
        for ax_ref, artist in self._blit_artists:
            try:
                ax_ref.draw_artist(artist)
            except Exception:
                pass
        self.canvas.blit(self.fig.bbox)

    # ── Heatmap helpers ───────────────────────────────────────────────────

    def _get_heatmap(self, xd, yd, page_idx: int, bins: int, sigma: float):
        """Return (h, xe, ye) from cache or recompute."""
        hmap_key = (self.x_combo.currentText(), self.y_combo.currentText(),
                    self.file_combo.currentText(),
                    "Δ" in self.mode_combo.currentText())
        if hmap_key != self._hmap_key:
            self._hmap_cache.clear()
            self._hmap_key = hmap_key

        cache_key = (page_idx, bins, round(sigma, 2))
        if cache_key in self._hmap_cache:
            return self._hmap_cache[cache_key]

        h, xe, ye = np.histogram2d(xd, yd, bins=bins)
        h = h.T.astype(float)
        if sigma > 0:
            h = gaussian_filter(h, sigma=sigma)
        if len(self._hmap_cache) >= _HMAP_CACHE_MAX:
            self._hmap_cache.pop(next(iter(self._hmap_cache)))
        self._hmap_cache[cache_key] = (h, xe, ye)
        return h, xe, ye

    @staticmethod
    def _make_norm(h, log_scale: bool):
        pos = h[h > 0]
        if log_scale and len(pos):
            return LogNorm(vmin=max(1e-3, pos.min()), vmax=h.max())
        return Normalize(vmin=float(h.min()), vmax=float(h.max()))

    # ── RF helpers ────────────────────────────────────────────────────────

    def _get_separatrix(self, params: dict) -> tuple:
        """Return (dt_sep, dp_sep) or (None, None)."""
        rf = self.app._rf_params
        if rf is None:
            return None, None
        p_central = params.get("pCentral", None)
        t_central = params.get("PassCentralTime", 0.0)
        if p_central is None:
            return None, None

        cavities_raw = rf.get("cavities", [])
        if self.app._rf_ramp_data is not None:
            ramp = self.app._rf_ramp_data
            idx  = int(np.argmin(np.abs(ramp["Time"] - float(t_central))))
            cavities_raw = ramp["cavities"][idx]
        if not cavities_raw:
            return None, None

        cavities = [(V, int(h), float(phi_s) * np.pi / 180.0)
                    for V, h, phi_s in cavities_raw]
        dt_s, dl_s = compute_rf_separatrix(
            cavities, rf.get("alphac", 0.0), p_central,
            rf.get("mass_mev", 0.51099895), rf.get("f_rev_hz", 1e6))
        if dt_s is None:
            return None, None
        return dt_s, dl_s * float(p_central)

    def _draw_rf(self, ax, params, xn, yn, xd, yd, center_ref) -> None:
        rf_active = (self.app._show_rf_bucket and center_ref
                     and {xn, yn} == {"t", "p"})
        if not rf_active:
            self._rf_line = None
            return
        t_mean = float(xd.mean()) if xn == "t" else float(yd.mean())
        p_mean = float(yd.mean()) if yn == "p" else float(xd.mean())
        dt_s, dp_s = self._get_separatrix(params)
        if dt_s is None:
            self._rf_line = None
            return
        if xn == "t":
            lx, ly = dt_s + t_mean, dp_s + p_mean
        else:
            lx, ly = dp_s + p_mean, dt_s + t_mean
        (self._rf_line,) = ax.plot(
            lx, ly, color="#ffdd44", linewidth=1.4,
            linestyle="--", alpha=0.85, zorder=8)

    def _update_rf_line(self, ax, params, xn, yn, xd, yd, center_ref) -> None:
        rf_active = (self.app._show_rf_bucket and center_ref
                     and {xn, yn} == {"t", "p"})
        if not rf_active:
            if self._rf_line:
                self._rf_line.set_visible(False)
            return
        t_mean = float(xd.mean()) if xn == "t" else float(yd.mean())
        p_mean = float(yd.mean()) if yn == "p" else float(xd.mean())
        dt_s, dp_s = self._get_separatrix(params)
        if dt_s is None:
            if self._rf_line:
                self._rf_line.set_visible(False)
            return
        if self._rf_line is None:
            # First time RF is active but artist was not created — full redraw
            self._needs_full = True
            return
        if xn == "t":
            self._rf_line.set_data(dt_s + t_mean, dp_s + p_mean)
        else:
            self._rf_line.set_data(dp_s + p_mean, dt_s + t_mean)
        self._rf_line.set_visible(True)

    def _apply_bucket_view(self, ax, params, xn, yn, xd, yd) -> None:
        dt_s, dp_s = self._get_separatrix(params)
        if dt_s is None:
            return
        t_mean = float(xd.mean()) if xn == "t" else float(yd.mean())
        p_mean = float(yd.mean()) if yn == "p" else float(xd.mean())
        pad_t  = abs(dt_s).max() * 0.15
        pad_p  = abs(dp_s).max() * 0.15
        if xn == "t":
            ax.set_xlim(t_mean + dt_s.min() - pad_t, t_mean + dt_s.max() + pad_t)
            ax.set_ylim(p_mean + dp_s.min() - pad_p, p_mean + dp_s.max() + pad_p)
        else:
            ax.set_xlim(p_mean + dp_s.min() - pad_p, p_mean + dp_s.max() + pad_p)
            ax.set_ylim(t_mean + dt_s.min() - pad_t, t_mean + dt_s.max() + pad_t)

    def _update_rf_label(self, center_ref: bool, xn: str, yn: str) -> None:
        active = (self.app._show_rf_bucket and center_ref
                  and {xn, yn} == {"t", "p"})
        if active:
            self.rf_lbl.setStyleSheet(
                f"color: {RAN_CLR}; background: #0a2a14; "
                "border-radius: 3px; padding: 1px 4px; "
                "font-size: 10px; font-weight: bold;")
        else:
            self.rf_lbl.setStyleSheet(
                "color: #1a3a2a; background: #1a3a2a; "
                "border-radius: 3px; padding: 1px 4px; "
                "font-size: 10px; font-weight: bold;")

    # ── Tracking / loss ───────────────────────────────────────────────────

    def _draw_tracking(self, ax, pages, page_idx: int, xi: int, yi: int):
        tracked = self.app._tracked_ids
        if not tracked:
            return
        finfo = self.app.model.file_by_label(self.file_combo.currentText())
        if finfo is None:
            return
        finfo.precompute_trajectories(tracked)
        for t_idx, pid in enumerate(tracked):
            tcol = TRACK_COLORS[t_idx % len(TRACK_COLORS)]
            traj = finfo.traj_cache.get(pid, [])
            tx   = [float(r[xi]) for r in traj[:page_idx + 1] if r is not None]
            ty   = [float(r[yi]) for r in traj[:page_idx + 1] if r is not None]
            cur  = traj[page_idx] if page_idx < len(traj) else None

            if pid in self._track_artists:
                line, dot = self._track_artists[pid]
                if len(tx) > 1 and line:
                    line.set_data(tx, ty)
                if cur is not None and dot:
                    dot.set_offsets([[float(cur[xi]), float(cur[yi])]])
            else:
                line = None
                if len(tx) > 1:
                    (line,) = ax.plot(tx, ty, color=tcol, linewidth=0.8,
                                      alpha=0.5, zorder=7)
                dot = None
                if cur is not None:
                    dot = ax.scatter([float(cur[xi])], [float(cur[yi])],
                                     s=60, color=tcol, zorder=8,
                                     linewidths=1.5,
                                     edgecolors=self._color)
                self._track_artists[pid] = (line, dot)

    def _draw_loss(self, ax, pages, page_idx: int, xi: int, yi: int):
        if not self.app._show_loss:
            if self._loss_scatter:
                self._loss_scatter.set_visible(False)
            return
        finfo = self.app.model.file_by_label(self.file_combo.currentText())
        if finfo is None:
            return
        lmap = finfo.loss_map
        if not lmap:
            return
        pg_data = pages[page_idx]["data"]
        pid_col = pg_data[:, COLUMNS.index("particleID")].astype(int)
        lost_rows = []
        for pid, last_pg in lmap.items():
            if last_pg == page_idx:
                hits = np.where(pid_col == pid)[0]
                if len(hits):
                    lost_rows.append(pg_data[hits[0]])
        if not lost_rows:
            if self._loss_scatter:
                self._loss_scatter.set_visible(False)
            return
        lx = np.array([r[xi] for r in lost_rows])
        ly = np.array([r[yi] for r in lost_rows])
        if self._loss_scatter is None:
            self._loss_scatter = ax.scatter(
                lx, ly, s=12, color="#ff3333",
                alpha=0.8, linewidths=0, zorder=9, marker="x")
        else:
            self._loss_scatter.set_offsets(np.c_[lx, ly])
            self._loss_scatter.set_visible(True)

    # ── Cleanup ───────────────────────────────────────────────────────────

    def destroy_panel(self) -> None:
        plt.close(self.fig)
        self.deleteLater()
