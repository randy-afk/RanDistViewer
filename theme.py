"""
RanDistViewer — theme.py
=========================
Catppuccin Mocha palette + RanOptics brand colors.
Matches RanOptics GUI exactly. Import from here everywhere.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPalette, QFont

# ── Catppuccin Mocha ──────────────────────────────────────────────────────────
BG       = "#1e1e2e"   # Base
PANEL    = "#313244"   # Surface0
BORDER   = "#45475a"   # Surface1
SURFACE2 = "#585b70"   # Surface2 (hover)
MANTLE   = "#181825"   # Mantle (deep bg)
CRUST    = "#11111b"   # Crust (darkest)
FG       = "#cdd6f4"   # Text
FG_DIM   = "#6c7086"   # Overlay0
FG_LBL   = "#9399b2"   # Overlay2

# ── RanOptics brand (must never change) ───────────────────────────────────────
RAN_CLR  = "#00e676"   # bright green  — primary accent
ACCENT   = "#89b4fa"   # blue          — matches RanOptics ACCENT
ACCENT2  = "#cba6f7"   # mauve         — section headers
SUCCESS  = "#a6e3a1"   # green
WARN     = "#f9e2af"   # yellow
ERROR    = "#f38ba8"   # red
TEAL     = "#94e2d5"   # info

# ── Matplotlib colors ─────────────────────────────────────────────────────────
AX_BG   = "#12121e"
GRID_C  = "#2a2a3e"
SPINE_C = "#45475a"
TEXT_C  = FG
TEXT_DIM = FG_LBL

# ── Per-file dataset colors ───────────────────────────────────────────────────
FILE_COLORS = [
    "#89b4fa",   # blue   (ACCENT)
    "#fab387",   # peach
    "#a6e3a1",   # green
    "#f38ba8",   # red
    "#cba6f7",   # mauve
    "#f9e2af",   # yellow
]

# ── Particle tracking trail colors ────────────────────────────────────────────
TRACK_COLORS = [
    "#ffffff", "#f9e2af", "#fab387", "#a6e3a1",
    "#cba6f7", "#94e2d5", "#f38ba8", "#89b4fa",
]

# ── Magnet element colors ─────────────────────────────────────────────────────
ELE_COLORS = {
    "QUAD":    ("#f38ba8", 1),
    "KQUAD":   ("#f38ba8", 1),
    "SBEN":    ("#89b4fa", 1),
    "RBEN":    ("#89b4fa", 1),
    "CSBEND":  ("#89b4fa", 1),
    "SEXT":    ("#a6e3a1", 1),
    "KSEXT":   ("#a6e3a1", 1),
    "OCT":     ("#f9e2af", 1),
    "KOCT":    ("#f9e2af", 1),
    "KICKER":  ("#cba6f7", 1),
    "HKICK":   ("#cba6f7", 1),
    "VKICK":   ("#cba6f7", 1),
    "RFCA":    ("#94e2d5", 1),
    "RFCW":    ("#94e2d5", 1),
    "SOLE":    ("#fab387", 1),
    "WIGGLER": ("#fab387", 1),
    "DRIF":    (None,      0),
    "MARK":    ("#45475a", 0),
    "MONI":    ("#585b70", 0),
    "WATCH":   ("#585b70", 0),
}

OPT_X = ACCENT
OPT_Y = "#fab387"   # peach

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_MAIN  = QFont(); FONT_MAIN.setPointSize(11)
FONT_BOLD  = QFont(); FONT_BOLD.setPointSize(11);  FONT_BOLD.setBold(True)
FONT_SMALL = QFont(); FONT_SMALL.setPointSize(10)
FONT_MONO  = QFont("Monospace"); FONT_MONO.setPointSize(10)
FONT_HDR   = QFont(); FONT_HDR.setPointSize(16);   FONT_HDR.setBold(True)
FONT_SEC   = QFont(); FONT_SEC.setPointSize(11);   FONT_SEC.setBold(True)

# ── Stylesheets (match RanOptics exactly) ─────────────────────────────────────
BTN_SS = f"""
    QPushButton {{
        background: {PANEL}; border: 1px solid {BORDER};
        border-radius: 8px; color: {ACCENT}; padding: 4px 10px;
        font-weight: 500;
    }}
    QPushButton:hover   {{ background: {SURFACE2}; border-color: {ACCENT}; }}
    QPushButton:pressed {{ background: {BORDER}; }}
    QPushButton:checked {{ background: {PANEL}; border-color: {RAN_CLR}; color: {RAN_CLR}; }}
    QPushButton:disabled {{ color: {FG_DIM}; border-color: {BORDER}; background: {PANEL}; }}
"""

ENTRY_SS = f"""
    QLineEdit {{
        background: {MANTLE}; border: 1px solid {BORDER};
        border-radius: 8px; color: {FG}; padding: 4px 10px;
        selection-background-color: {ACCENT}; selection-color: {CRUST};
    }}
    QLineEdit:focus {{
        border-color: {ACCENT};
        border-left: 3px solid {ACCENT};
        background: {BG};
    }}
"""

COMBO_SS = f"""
    QComboBox {{
        background: {MANTLE}; border: 1px solid {BORDER};
        border-radius: 8px; color: {FG}; padding: 4px 10px;
    }}
    QComboBox:focus {{ border-color: {ACCENT}; }}
    QComboBox::drop-down {{ border: none; width: 20px; }}
    QComboBox::down-arrow {{ width: 0; height: 0; }}
    QComboBox QAbstractItemView {{
        background: {PANEL}; color: {FG}; border: 1px solid {BORDER};
        border-radius: 6px; padding: 2px;
        selection-background-color: {ACCENT}; selection-color: {CRUST};
        outline: none;
    }}
"""

CHK_SS = f"""
    QCheckBox {{ color: {FG}; spacing: 7px; }}
    QCheckBox::indicator {{
        width: 15px; height: 15px; border-radius: 4px;
        border: 1px solid {SURFACE2}; background: {MANTLE};
    }}
    QCheckBox::indicator:unchecked:hover {{ border-color: {ACCENT}; }}
    QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
"""

RB_SS = f"""
    QRadioButton {{ color: {FG}; spacing: 7px; }}
    QRadioButton::indicator {{
        width: 14px; height: 14px; border-radius: 7px;
        border: 1px solid {SURFACE2}; background: {MANTLE};
    }}
    QRadioButton::indicator:checked {{
        background: {ACCENT}; border-color: {ACCENT}; border-width: 3px;
    }}
"""

SCROLL_SS = f"""
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{
        background: {MANTLE}; width: 6px; margin: 0; border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {SURFACE2}; border-radius: 3px; min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""

MENUBAR_SS = f"""
    QMenuBar {{
        background: {CRUST}; color: {FG_LBL};
        border-bottom: 1px solid {BORDER};
    }}
    QMenuBar::item {{ padding: 4px 10px; border-radius: 4px; }}
    QMenuBar::item:selected {{ background: {SURFACE2}; color: {FG}; }}
    QMenu {{
        background: {MANTLE}; color: {FG};
        border: 1px solid {BORDER}; border-radius: 8px; padding: 4px;
    }}
    QMenu::item {{ padding: 5px 20px; border-radius: 4px; }}
    QMenu::item:selected {{ background: {PANEL}; color: {ACCENT}; }}
    QMenu::separator {{ background: {BORDER}; height: 1px; margin: 4px 8px; }}
"""

# ── Matplotlib axis styling ───────────────────────────────────────────────────
def style_ax(ax):
    ax.set_facecolor(AX_BG)
    ax.tick_params(colors=FG, labelsize=9)
    for sp in ax.spines.values():
        sp.set_edgecolor(SPINE_C)
    ax.grid(True, color=GRID_C, linewidth=0.4, zorder=0)


# ── Qt palette ────────────────────────────────────────────────────────────────
def apply_dark_palette(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor(BG))
    palette.setColor(QPalette.WindowText,      QColor(FG))
    palette.setColor(QPalette.Base,            QColor(MANTLE))
    palette.setColor(QPalette.AlternateBase,   QColor(PANEL))
    palette.setColor(QPalette.ToolTipBase,     QColor(MANTLE))
    palette.setColor(QPalette.ToolTipText,     QColor(FG))
    palette.setColor(QPalette.Text,            QColor(FG))
    palette.setColor(QPalette.Button,          QColor(PANEL))
    palette.setColor(QPalette.ButtonText,      QColor(FG))
    palette.setColor(QPalette.BrightText,      QColor("#ffffff"))
    palette.setColor(QPalette.Highlight,       QColor(ACCENT))
    palette.setColor(QPalette.HighlightedText, QColor(CRUST))
    palette.setColor(QPalette.Disabled, QPalette.Text,       QColor(FG_DIM))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(FG_DIM))
    app.setPalette(palette)

    app.setStyleSheet(f"""
        QWidget {{ font-size: 11px; background: {BG}; color: {FG}; }}
        QMainWindow {{ background: {BG}; }}
        QPushButton {{
            background: {PANEL}; border: 1px solid {BORDER};
            border-radius: 8px; color: {ACCENT}; padding: 4px 10px; font-weight: 500;
        }}
        QPushButton:hover   {{ background: {SURFACE2}; border-color: {ACCENT}; }}
        QPushButton:pressed {{ background: {BORDER}; }}
        QPushButton:checked {{ border-color: {RAN_CLR}; color: {RAN_CLR}; }}
        QPushButton:disabled {{ color: {FG_DIM}; border-color: {BORDER}; }}
        QComboBox {{
            background: {MANTLE}; border: 1px solid {BORDER};
            border-radius: 8px; color: {FG}; padding: 4px 10px;
        }}
        QComboBox:focus {{ border-color: {ACCENT}; }}
        QComboBox::drop-down {{ border: none; }}
        QComboBox QAbstractItemView {{
            background: {PANEL}; color: {FG}; border: 1px solid {BORDER};
            selection-background-color: {ACCENT}; selection-color: {CRUST};
        }}
        QSlider::groove:horizontal {{
            height: 4px; background: {BORDER}; border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            width: 12px; height: 12px; margin: -4px 0;
            background: {ACCENT}; border-radius: 6px;
        }}
        QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
        QLineEdit {{
            background: {MANTLE}; border: 1px solid {BORDER};
            border-radius: 8px; color: {FG}; padding: 4px 10px;
        }}
        QLineEdit:focus {{ border-color: {ACCENT}; border-left: 3px solid {ACCENT}; }}
        QCheckBox {{ color: {FG}; spacing: 7px; }}
        QCheckBox::indicator {{
            width: 15px; height: 15px; border-radius: 4px;
            border: 1px solid {SURFACE2}; background: {MANTLE};
        }}
        QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
        QRadioButton {{ color: {FG}; spacing: 7px; }}
        QRadioButton::indicator {{
            width: 14px; height: 14px; border-radius: 7px;
            border: 1px solid {SURFACE2}; background: {MANTLE};
        }}
        QRadioButton::indicator:checked {{
            background: {ACCENT}; border-color: {ACCENT}; border-width: 3px;
        }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{
            background: {MANTLE}; width: 6px; border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: {SURFACE2}; border-radius: 3px; min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QSplitter::handle {{ background: {BORDER}; }}
        QToolBar {{ background: {MANTLE}; border: none; spacing: 4px; padding: 2px 4px; }}
        QStatusBar {{ background: {CRUST}; color: {FG_LBL}; }}
        QGroupBox {{
            border: 1px solid {BORDER}; border-radius: 8px;
            margin-top: 8px; padding-top: 6px; color: {ACCENT2}; font-weight: bold;
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 10px; }}
        QDoubleSpinBox, QSpinBox {{
            background: {MANTLE}; border: 1px solid {BORDER};
            border-radius: 6px; padding: 2px 6px; color: {FG};
        }}
        QLabel {{ color: {FG}; background: transparent; }}
        QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: {BORDER}; }}
    """)
