# Sidebar

The sidebar sits on the **left** side of the main window. It contains four
collapsible sections with pill-shaped header buttons — click a header to
collapse or expand that section.

---

## DISPLAY

| Control | Type | Description |
|---|---|---|
| Marginal histograms | Checkbox | 1D histograms along both axes of each panel |
| Stats overlay | Checkbox | Courant-Snyder parameters and emittance ellipse |
| Point size | Slider | Scatter marker size |
| Alpha | Slider | Scatter point transparency (0 – 1) |
| Histogram bins | Slider | Bin count for marginal histograms |
| Axis smoothing (frames) | Slider | Number of frames averaged for Roll/Track axis smoothing |
| Track window (±σ) | Slider | Half-width in σ units for Track axis mode |

---

## PLOT MODE

| Control | Type | Description |
|---|---|---|
| Scatter | Radio | Individual particle scatter plot |
| Heatmap 2D | Radio | 2D histogram rendered as a colour image |
| Colormap | Combo | Matplotlib colormap name (default: `turbo`) |
| Heatmap bins | Slider | Histogram bin count per axis |
| Smoothing (sigma) | Slider | Gaussian smoothing kernel width in bin units |
| Log color scale | Checkbox | Logarithmic colour normalisation |
| Show colorbar | Checkbox | Display colour scale bar on heatmap panels |

---

## PLAYBACK

| Control | Type | Description |
|---|---|---|
| **▶ Play** | Button | Start / pause turn-by-turn animation |
| Speed (fps) | Slider | Playback frame rate |

---

## PARTICLE TRACKING

| Control | Type | Description |
|---|---|---|
| ID entry | Text field | Comma-separated particle IDs to track (e.g. `42, 100, 283`) |
| **Track** | Button | Activate tracking for entered IDs |
| **Clear tracking** | Button | Remove all tracking trails |

When tracking is active, trail lines connect each particle's position across
the last N frames and a dot marks the current position. The status line below
the buttons shows which particles are currently being tracked.
