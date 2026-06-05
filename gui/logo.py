"""
RanDistViewer — gui/logo.py
============================
_DistLogo: QPainter widget for the RanDistViewer header.
Depicts a phase-space (x-x') particle bunch:
  - Filled scatter cloud of dots in a dim green
  - 1-sigma ellipse outline in RAN_CLR
  - Axis cross lines
~108 x 64 px, matches RanOptics _FodoLogo dimensions.
"""

import math
import random

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from PySide6.QtCore import Qt, QPointF, QRectF

from theme import RAN_CLR, ACCENT, BG


# Deterministic "random" particle cloud — fixed seed so it looks the same every time
_RNG = random.Random(42)
_N_DOTS = 120

def _make_cloud():
    """
    Generate a tilted Gaussian cloud in normalised coords [-1, 1].
    Returns list of (x, y) tuples.
    """
    pts = []
    for _ in range(_N_DOTS):
        # Correlated Gaussian: alpha ~ -0.7 (tilted ellipse)
        u = _RNG.gauss(0, 1)
        v = _RNG.gauss(0, 1)
        x =  0.55 * u
        y = -0.45 * u + 0.30 * v
        pts.append((x, y))
    return pts

_CLOUD = _make_cloud()


class _DistLogo(QWidget):
    """Phase-space bunch logo for the RanDistViewer header."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(108, 64)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        W, H = 108, 64
        cx, cy = W / 2, H / 2   # canvas centre
        # Scale: 1 normalised unit → 22 px
        sx, sy = 22, 18

        def to_px(nx, ny):
            return QPointF(cx + nx * sx, cy - ny * sy)

        # ── Background ────────────────────────────────────────────────────
        p.fillRect(0, 0, W, H, QColor(BG))

        # ── Axis lines ────────────────────────────────────────────────────
        axis_pen = QPen(QColor("#2a2a50"), 1)
        axis_pen.setStyle(Qt.SolidLine)
        p.setPen(axis_pen)
        # x-axis
        p.drawLine(QPointF(4, cy), QPointF(W - 4, cy))
        # y-axis
        p.drawLine(QPointF(cx, 4), QPointF(cx, H - 4))

        # ── Particle dots ─────────────────────────────────────────────────
        dot_color = QColor(RAN_CLR)
        dot_color.setAlphaF(0.30)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(dot_color))
        for nx, ny in _CLOUD:
            pt = to_px(nx, ny)
            p.drawEllipse(pt, 1.4, 1.4)

        # ── 1-sigma ellipse ───────────────────────────────────────────────
        # Manually derived from the cloud covariance:
        #   sig_x=0.55, sig_y=sqrt(0.45^2+0.30^2)≈0.54, rho=-0.45*0.55/...
        # Draw as a rotated ellipse using a parametric path.
        # Parameters match _make_cloud() exactly.
        a  = 0.55          # semi-axis along u direction (x)
        b  = 0.30          # semi-axis along v direction
        th = math.atan2(-0.45, 1.0)  # tilt angle

        ellipse_pen = QPen(QColor(RAN_CLR), 1.6)
        ellipse_pen.setCapStyle(Qt.RoundCap)
        p.setPen(ellipse_pen)
        p.setBrush(Qt.NoBrush)

        N = 80
        pts_e = []
        for i in range(N + 1):
            t  = 2 * math.pi * i / N
            ex =  a * math.cos(t) * math.cos(th) - b * math.sin(t) * math.sin(th)
            ey =  a * math.cos(t) * math.sin(th) + b * math.sin(t) * math.cos(th)
            pts_e.append(to_px(ex, ey))
        for i in range(len(pts_e) - 1):
            p.drawLine(pts_e[i], pts_e[i + 1])

        # ── Axis tick labels (tiny) ────────────────────────────────────────
        label_pen = QPen(QColor("#555570"), 1)
        p.setPen(label_pen)
        font = p.font()
        font.setPixelSize(7)
        p.setFont(font)
        p.drawText(QRectF(W - 14, cy + 2, 12, 8), Qt.AlignRight, "x")
        p.drawText(QRectF(cx + 2, 2, 12, 8),      Qt.AlignLeft,  "x'")

        p.end()
