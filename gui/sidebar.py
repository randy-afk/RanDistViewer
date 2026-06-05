"""
RanDistViewer — gui/sidebar.py
================================
SidebarSection and make_slider — styled to match RanOptics.
Section headers use pill label + horizontal rule (_sec pattern).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QFrame,
)
from PySide6.QtCore import Qt

from theme import (
    BG, MANTLE, PANEL, BORDER, SURFACE2,
    ACCENT, ACCENT2, CRUST, FG, FG_DIM, FG_LBL,
    FONT_MAIN, FONT_SEC, FONT_SMALL,
)


class SidebarSection(QWidget):
    """
    Collapsible sidebar section — pill header + rule, matching RanOptics _sec().
    """

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(2)

        # ── Section header: pill label + rule ────────────────────────────
        hdr_w = QWidget()
        hdr_w.setStyleSheet("background: transparent;")
        hdr_h = QHBoxLayout(hdr_w)
        hdr_h.setContentsMargins(8, 6, 8, 2)
        hdr_h.setSpacing(8)

        self._toggle = QPushButton(f"  {title.upper()}  ")
        self._toggle.setFont(FONT_SEC)
        self._toggle.setCheckable(True)
        self._toggle.setChecked(True)
        self._toggle.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT2}; border: none; border-radius: 4px;
                color: {CRUST}; padding: 1px 6px; font-weight: bold;
                text-align: left;
            }}
            QPushButton:hover {{ background: {ACCENT}; color: {CRUST}; }}
        """)
        self._toggle.toggled.connect(self._on_toggle)

        rule = QFrame()
        rule.setFrameShape(QFrame.HLine)
        rule.setStyleSheet(f"color: {BORDER}; background: {BORDER};")

        hdr_h.addWidget(self._toggle)
        hdr_h.addWidget(rule, 1)
        layout.addWidget(hdr_w)

        # ── Body ─────────────────────────────────────────────────────────
        self._body = QWidget()
        self._body.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(8, 2, 8, 8)
        body_layout.setSpacing(4)
        layout.addWidget(self._body)
        self.body_layout = body_layout

    def _on_toggle(self, checked: bool):
        self._body.setVisible(checked)

    def add(self, widget: QWidget) -> None:
        self.body_layout.addWidget(widget)

    def add_row(self, label_text: str, widget: QWidget) -> None:
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl  = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label_text)
        lbl.setFont(FONT_SMALL)
        lbl.setStyleSheet(f"color: {FG_LBL};")
        rl.addWidget(lbl)
        rl.addWidget(widget, 1)
        self.body_layout.addWidget(row)


def make_slider(mn, mx, val, decimals: int = 0) -> QSlider:
    s = QSlider(Qt.Horizontal)
    s.setMinimum(0)
    s.setMaximum(1000)
    s._mn = mn; s._mx = mx; s._decimals = decimals
    s.setValue(int((val - mn) / (mx - mn) * 1000))

    def real_value():
        v = s.value() / 1000.0 * (s._mx - s._mn) + s._mn
        return round(v, decimals) if decimals > 0 else int(round(v))

    s.real_value = real_value
    return s
