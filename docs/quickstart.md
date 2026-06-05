# Quickstart

This guide walks through the most common workflow: opening an SDDS bunch file,
playing through turns, and exporting a panel.

---

## 1. Launch the viewer

```bash
python main.py
```

The main window opens with one empty panel and a collapsed sidebar on the right.

---

## 2. Open an SDDS file

Go to **File → Open SDDS file…** and select a binary SDDS bunch file produced
by ELEGANT (`.bun`, `.wat`, or any file with the standard 8-column particle
layout).

The file is loaded, pre-computed statistics are cached, and the panel
immediately renders page 0 (turn 0).

!!! note "Multiple files"
    You can open several files in the same session. Each file is assigned a
    distinct colour from the palette (`#89b4fa`, `#fab387`, `#a6e3a1`, …).
    Use **View → + Panel** to add panels and assign each panel to a different
    file via its file selector at the top of the panel.

---

## 3. Choose phase-space axes

Each panel has **X axis** and **Y axis** dropdowns. The available columns are:

`x`, `xp`, `y`, `yp`, `t`, `p`, `dt`, `particleID`

The default layout for the first four panels is:
`(x, xp)` · `(y, yp)` · `(t, p)` · `(x, y)`.

---

## 4. Play through turns

The playback toolbar at the top of the window contains:

| Control | Action |
|---|---|
| **◀◀** | Jump to first turn |
| **◀** | Step back one turn |
| **▶ / ⏸** | Play / pause |
| **▶** | Step forward one turn |
| **▶▶** | Jump to last turn |
| Turn slider | Drag to any turn |
| Speed control | Adjust playback frames per second |

During playback the blit pipeline repaints only the particle data pixels —
axes, ticks, and grid are cached and not redrawn — so even large files animate
smoothly.

---

## 5. Switch plot mode

Open the **Plot** section in the sidebar and choose between:

- **Scatter** — individual particle dots. Point size and alpha are adjustable.
- **Heatmap** — 2D histogram rendered as an image. Bin count, Gaussian
  smoothing sigma, and linear/log colour scale are all configurable.

---

## 6. Select an axis mode

Axis mode controls how the plot limits update from turn to turn (see
[Plot Panel](gui/plot_panel.md#axis-modes) for full details):

- **Auto** — Matplotlib autoscale every frame
- **Roll** — centred on beam mean, smoothed half-width
- **Track** — centred on mean, ±Nσ window
- **Fixed** — lock current limits, no update during playback
- **Roll+Δ / Track+Δ** — same as Roll/Track but the reference offset
  (`p_central`, `t_central`) is subtracted first

---

## 7. Export

Go to **File → Export panels…** to save all visible panels as an interactive
Plotly HTML file. The file can be opened in any browser and supports zoom,
pan, and hover.

---

## 8. Save your session

Go to **File → Save Session…** to save the complete GUI state — loaded files,
panel layout, axis modes, RF parameters, and all settings — to a JSON file
(`.json`). Reload it later with **File → Load Session…**.

See the [Sessions](session.md) page for the full format description.
