# RanDistViewer

**Turn-by-turn particle bunch distribution viewer for ELEGANT SDDS files.**

Part of the **Ran\*** suite of accelerator physics tools developed at Jefferson Lab.

---

## Overview

RanDistViewer visualises particle bunch distributions from ELEGANT `watch` and
`watch` output files. Each file contains many pages — one per beam turn — and
the viewer plays through them as a high-speed animation using a blit-based
Matplotlib pipeline that bypasses full redraws between frames.

Multiple files can be loaded simultaneously, each displayed in its own
configurable panel, coloured distinctly, and animated in lock-step.

---

## Features

| Category | Capability |
|---|---|
| **Data** | Binary SDDS bunch files (ELEGANT `watch` output) |
| **Panels** | Multi-panel grid; up to 6 independent phase-space plots |
| **Plot modes** | Scatter, 2D heatmap (linear / log) with Gaussian smoothing |
| **Animation** | Blit-based frame-by-frame playback; adjustable speed |
| **Axis control** | Auto, Roll, Track, Fixed, Roll+Δ, Track+Δ |
| **Overlays** | Twiss/sigma stats, emittance ellipse, RF bucket separatrix |
| **Histograms** | Marginal 1D histograms on both axes |
| **Tracking** | Particle trajectory trails across turns |
| **Beam loss** | Lost-particle highlighting (red overlay) |
| **Stats panel** | σ and emittance evolution over all turns |
| **Optics** | Lattice Twiss viewer (`.twi` + `.mag` files) |
| **Session** | Save/load full GUI state as JSON |
| **Export** | Interactive Plotly HTML for all panels |

---

## Quick links

- [Installation](installation.md)
- [Quickstart](quickstart.md)
- [Plot Panel reference](gui/plot_panel.md)
- [RF Bucket physics](physics/rf_bucket.md)
- [File format details](file_formats.md)

---

## Part of the Ran\* suite

| Tool | Purpose |
|---|---|
| **RanOptics** | Interactive accelerator optics plotting GUI (Tao/Bmad, ELEGANT, MAD-X, xsuite) |
| **RanDistViewer** | Turn-by-turn SDDS bunch distribution viewer |
| **RanPlot** | General-purpose scientific figure editor |

---

## Author

Randika Wickramasinghe — [randika@jlab.org](mailto:randika@jlab.org)  
Jefferson Lab, Newport News VA

!!! note "License"
    Jefferson Lab internal use. Not for public distribution.
