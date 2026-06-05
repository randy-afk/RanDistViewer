# Sessions

RanDistViewer can save and restore the complete GUI state as a JSON session
file.

---

## Save and load

- **Save:** File → Save Session… — prompts for a filename and writes JSON.
- **Load:** File → Load Session… — reloads all files, restores panel
  configuration, and applies all settings.

There is no fixed extension requirement, but `.json` is conventional.

---

## Session file format

Top-level fields:

| Field | Type | Description |
|---|---|---|
| `files` | list[str] | Absolute paths of all loaded SDDS files |
| `current_page` | int | Current turn number at save time |
| `panels` | list[object] | Per-panel configuration (see below) |
| `plot_mode` | string | `"scatter"` or `"heatmap"` |
| `cmap` | string | Matplotlib colormap name for heatmap mode |
| `hmap_bins` | int | Heatmap bin count |
| `smooth_sigma` | float | Gaussian smoothing sigma (bin units) |
| `log_scale` | bool | Logarithmic colour scale in heatmap |
| `show_hist` | bool | Marginal histograms enabled |
| `hist_bins` | int | Histogram bin count |
| `pt_size` | float | Scatter point size |
| `alpha` | float | Scatter point alpha |
| `smooth_n` | int | Axis smoothing window (Roll/Track) |
| `sigma` | float | σ multiplier (Track mode) |
| `overlay` | bool | Twiss/stats overlay enabled |
| `rf_params` | object\|null | RF bucket configuration (see below) |
| `show_rf` | bool | RF separatrix overlay enabled |

### Per-panel fields (`panels` list entries)

| Field | Type | Description |
|---|---|---|
| `file_label` | string | Label of the assigned file (matches filename stem) |
| `x` | string | X-axis column name |
| `y` | string | Y-axis column name |
| `ax_mode` | string | Axis mode: `"Auto"`, `"Roll"`, `"Track"`, `"Fixed"`, `"Roll+Δ"`, `"Track+Δ"` |
| `bkt` | bool | RF separatrix shown in this panel |

### RF parameters (`rf_params` object)

| Field | Type | Description |
|---|---|---|
| `cavities` | list[[V, h, phi_s]] | List of cavity triples: [voltage (V), harmonic, synchronous phase (rad)] |
| `mass_mev` | float | Particle rest mass (MeV) |
| `alphac` | float | Momentum compaction factor |
| `f_rev_hz` | float | Revolution frequency (Hz) |
| `mode` | string | `"Static"` or `"Ramped"` |

---

## Example

```json
{
  "files": ["/data/runs/run042/watch_end.bun"],
  "current_page": 150,
  "plot_mode": "scatter",
  "cmap": "viridis",
  "hmap_bins": 64,
  "smooth_sigma": 1.0,
  "log_scale": false,
  "show_hist": true,
  "hist_bins": 64,
  "pt_size": 2,
  "alpha": 0.6,
  "smooth_n": 10,
  "sigma": 3.0,
  "overlay": true,
  "show_rf": true,
  "rf_params": {
    "cavities": [[1500000, 1, 0.0]],
    "mass_mev": 0.51099895,
    "alphac": 0.00657,
    "f_rev_hz": 499425000,
    "mode": "Static"
  },
  "panels": [
    {"file_label": "watch_end", "x": "x",  "y": "xp", "ax_mode": "Track", "bkt": false},
    {"file_label": "watch_end", "x": "y",  "y": "yp", "ax_mode": "Track", "bkt": false},
    {"file_label": "watch_end", "x": "t",  "y": "p",  "ax_mode": "Track+Δ", "bkt": true},
    {"file_label": "watch_end", "x": "x",  "y": "y",  "ax_mode": "Auto",    "bkt": false}
  ]
}
```

!!! tip "Portability"
    Session files store absolute file paths. If you move your data directory,
    edit the `files` list to point to the new locations before loading.
