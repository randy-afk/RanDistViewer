# Sidebar

The sidebar is a scrollable column of collapsible **SidebarSection** groups on
the right side of the main window. Each section has a pill-shaped header button
— click it to collapse or expand the section body.

---

## Files section

Lists all currently loaded files. Each entry shows the file label (derived from
the filename) and its assigned colour swatch.

Use the **Remove** button next to an entry to unload that file and release its
memory.

---

## Plot section

Controls that affect all panels globally.

| Control | Type | Description |
|---|---|---|
| Plot mode | Combo | `Scatter` or `Heatmap` |
| Point size | Spinner | Scatter marker size (pixels) |
| Alpha | Slider | Scatter point transparency (0 – 1) |
| Heatmap bins | Spinner | Histogram bin count per axis |
| Smooth σ | Spinner | Gaussian smoothing width (bin units) |
| Log scale | Checkbox | Log colour normalisation in heatmap |

---

## Axis section

| Control | Type | Description |
|---|---|---|
| Smooth N | Spinner | Frames averaged for Roll/Track axis smoothing |
| σ multiplier | Spinner | Half-width in σ units for Track mode |

---

## Overlays section

| Control | Type | Description |
|---|---|---|
| Histograms | Checkbox | Marginal 1D histograms on both axes |
| Twiss overlay | Checkbox | Courant-Snyder stats and emittance ellipse |
| RF bucket | Checkbox | Show RF separatrix (requires RF config) |

---

## Export section

| Button | Action |
|---|---|
| **Export HTML** | Save all visible panels as a single interactive Plotly HTML file |

---

## SidebarSection widget

Each section is implemented as a `SidebarSection` widget with a collapsible
body. The pill header uses `ACCENT2` (`#cba6f7`) as its background colour,
matching the RanOptics sidebar style exactly. Clicking the pill toggles
visibility of the body `QWidget`.

Individual rows inside a section are laid out with `add_row(label, widget)`,
which creates a `QHBoxLayout` with a fixed-width label on the left and the
control widget on the right.
