# RanDistViewer

**Turn-by-turn particle bunch distribution viewer for ELEGANT SDDS files.**

Part of the Ran* suite of accelerator physics tools developed at Jefferson Lab.

---

## Features

- Multi-file, multi-panel phase-space plot grid
- Scatter and 2D heatmap modes with Gaussian smoothing
- Fast blit-based frame-by-frame animation (turn-by-turn playback)
- Marginal histograms and Twiss/sigma stats overlay
- RF bucket separatrix overlay (static or ramped)
- Particle tracking across turns with trajectory trails
- Beam loss highlighting
- Stats-over-time panel (σ, emittance evolution)
- Correlation matrix dialog
- Lattice optics viewer (.twi + .mag files)
- Session save/load (JSON)
- Plotly HTML export

---

## Requirements

```
PySide6
matplotlib
numpy
scipy
plotly
```

Install with:

```bash
pip install PySide6 matplotlib numpy scipy plotly
```

---

## Usage

```bash
python main.py
```

---

## Project Structure

```
RanDistViewer/
├── main.py              # Entry point
├── theme.py             # Color palette, fonts, stylesheets
├── physics/
│   ├── rf_bucket.py     # RF separatrix computation (pure numpy)
│   └── beam_stats.py    # Twiss parameters, ellipse overlays
├── models/
│   ├── sdds_loader.py   # Binary SDDS bunch file parser
│   ├── twi_loader.py    # ELEGANT .twi and .mag file parsers
│   └── bunch_model.py   # BunchFile dataclass + BunchModel engine
└── gui/
    ├── main_window.py   # SDDSViewer — main window, signal/slot wiring
    ├── plot_panel.py    # PlotPanel — blit-based phase-space panel
    ├── optics_window.py # Lattice optics viewer
    ├── sidebar.py       # SidebarSection, make_slider
    ├── dialogs.py       # RF config, correlation matrix, stats panel
    └── logo.py          # _DistLogo QPainter widget
```

---

## File Format

Accepts binary SDDS files produced by ELEGANT (`watch`, `buncher`, etc.)
with the standard 8-column particle layout:

| Column | Unit |
|--------|------|
| x | m |
| xp | rad |
| y | m |
| yp | rad |
| t | s |
| p | mβγ |
| dt | s |
| particleID | — |

---

## Author

Randika Wickramasinghe — randika@jlab.org  
Jefferson Lab, Newport News VA

---

## License

Jefferson Lab internal use. Not for public distribution.
