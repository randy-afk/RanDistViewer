# RanDistViewer — MkDocs Handoff

This document is a handoff for setting up the MkDocs Material documentation
site for RanDistViewer, to be continued in a separate chat.

---

## Context

RanDistViewer is a standalone PySide6 + Matplotlib turn-by-turn SDDS bunch
distribution viewer. It is part of the Ran* suite at Jefferson Lab, alongside
**RanOptics** which already has a deployed MkDocs Material site on GitHub Pages.

The new docs site should follow the **exact same structure, theme, and style**
as the RanOptics docs site (github.com/randy-afk/RanOptics).

---

## Repo

- GitHub: to be created (currently local only)
- Pages branch: `gh-pages` (same as RanOptics)
- Deploy command: `mkdocs gh-deploy`

---

## Project file structure (for the docs writer)

```
RanDistViewer/
├── main.py
├── theme.py
├── requirements.txt
├── README.md
├── physics/
│   ├── rf_bucket.py
│   └── beam_stats.py
├── models/
│   ├── sdds_loader.py
│   ├── twi_loader.py
│   └── bunch_model.py
└── gui/
    ├── main_window.py
    ├── plot_panel.py
    ├── optics_window.py
    ├── sidebar.py
    ├── dialogs.py
    └── logo.py
```

---

## Suggested docs structure (mkdocs.yml nav)

```
docs/
├── index.md               # Overview, feature list, screenshot placeholder
├── installation.md        # pip install, requirements, launch
├── quickstart.md          # Open a file, play through turns, export
├── gui/
│   ├── overview.md        # Main window layout diagram
│   ├── plot_panel.md      # Scatter / heatmap modes, axis modes, blit
│   ├── sidebar.md         # All sidebar controls documented
│   ├── optics_window.md   # Twiss viewer, .twi and .mag loading
│   └── dialogs.md         # RF bucket config, corr matrix, stats panel
├── physics/
│   ├── rf_bucket.md       # RF separatrix math, cavity params
│   └── beam_stats.md      # Twiss computation, emittance, ellipse overlay
├── file_formats.md        # SDDS binary format, column layout, .twi, .mag
└── session.md             # Session save/load JSON format
```

---

## Key things to document

### Plot panel axis modes
- **Auto** — matplotlib autoscale every frame
- **Roll** — centred on beam mean, half-width smoothed over N frames
- **Track** — centred on mean, ±Nσ window, smoothed
- **Fixed** — lock button captures current limits, no update during playback
- **Roll+Δ / Track+Δ** — same as above but subtracts reference (p_central, t_central) first

### RF bucket
- Configured via RF Bucket dialog: voltage (V), harmonic h, synchronous phase φ_s
- Supports multi-cavity
- Supports ramped RF via CSV: columns = [Time, V1, h1, phi_s1, V2, h2, phi_s2, ...]
- Separatrix only shown when axis columns are `t` and `p` and Δ-mode is active

### Session file format (JSON)
Fields: `files`, `current_page`, `panels` (list of {file_label, x, y, ax_mode, bkt}),
`plot_mode`, `cmap`, `hmap_bins`, `smooth_sigma`, `log_scale`, `show_hist`,
`hist_bins`, `pt_size`, `alpha`, `smooth_n`, `sigma`, `overlay`,
`rf_params`, `show_rf`

### SDDS column layout
x, xp, y, yp, t, p, dt, particleID — 8 × float64 + 1 × uint64 = 64 bytes/particle

---

## Style notes (match RanOptics docs exactly)

- MkDocs Material theme
- Palette: `scheme: slate`, primary and accent colors matching RanOptics
- Same `extra_css` overrides as RanOptics
- Same admonition usage (note, tip, warning)
- Code blocks with `python` syntax highlighting throughout
- Same footer text format

---

## What NOT to include

- No API reference generation (no mkdocstrings) — prose docs only
- No lux_v6b.py references — that file is obsolete
- Do not mention RanBeam — that was a working folder name only

---

## Contact

randika@jlab.org
