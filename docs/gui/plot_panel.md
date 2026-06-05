# Plot Panel

Each **PlotPanel** widget displays one phase-space projection for one loaded
file. Panels update every frame during playback using a blit pipeline that
avoids re-drawing static elements.

---

## Panel anatomy

```
┌────────────────────────────────────────────────────────┐
│  [File ▾]  X: [x ▾]  Y: [xp ▾]  Mode: [Auto ▾]  [🔒] │  ← per-panel controls
├────────────────────────────────────────────────────────┤
│                                                        │
│   Matplotlib canvas (scatter or heatmap)               │
│   + optional marginal histograms                       │
│   + optional stats/ellipse overlay                     │
│   + optional RF separatrix overlay                     │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## Plot modes

### Scatter

Particles are drawn as individual points. The panel toolbar provides:

| Setting | Default | Description |
|---|---|---|
| Point size | 2 | Marker area in screen pixels |
| Alpha | 0.6 | Point transparency |

Scattered particles are coloured by the file colour assigned at load time.
Lost particles (when loss mode is active) are drawn in red on top.

### Heatmap

A 2D histogram is computed for the current page and rendered as a
`imshow` image. Settings:

| Setting | Default | Description |
|---|---|---|
| Bins | 64 | Number of bins per axis |
| Gaussian σ | 1.0 | Smoothing kernel width in bin units |
| Log scale | off | Use logarithmic colour normalisation |
| Colorbar | on | Show colour scale bar |

Heatmap images are cached per (page, bins, sigma, log) key so scrubbing
backwards does not recompute.

---

## Axis modes

The axis mode dropdown controls how plot limits update between turns.

### Auto

Matplotlib `autoscale()` is called each frame. Limits follow the data
distribution exactly. Useful for initial exploration; can feel unstable for
halo particles.

### Roll

The axis is centred on the per-frame beam mean. The half-width is computed
as the maximum absolute deviation smoothed over the last *N* frames
(controlled by the **Smooth N** spinner in the sidebar). The window grows
but never shrinks, giving a rolling view that tracks the beam without
jumping.

### Track

The axis is centred on the beam mean with a symmetric window of ±*Nσ*
where *N* is set by the **σ multiplier** spinner. The standard deviation is
also smoothed over *N* frames. This mode is best for watching the beam
breathe at a fixed scale.

### Fixed

The current axis limits are captured and locked. No update occurs during
playback. Activate by clicking the **🔒** lock button in the panel header,
which freezes the limits at whatever the current view is.

Click the lock button again to release.

### Roll+Δ and Track+Δ (offset modes)

These are variants of Roll and Track that subtract a reference offset before
plotting:

- For the **p** (momentum) axis: the reference is the `p_central` parameter
  stored in the SDDS page header.
- For the **t** (time) axis: the reference is `t_central` from the page
  header.

Offset modes are required to display the RF bucket separatrix correctly,
because the separatrix is computed in `(Δt, Δp)` coordinates.

!!! tip "RF bucket visibility"
    The RF separatrix overlay is only shown when the panel axes are `t` and
    `p` **and** an offset mode (Roll+Δ or Track+Δ) is active. If the
    separatrix is not appearing, check both conditions.

---

## Marginal histograms

Toggle via the **Histograms** checkbox in the sidebar Overlays section.
When enabled, 1D histograms are drawn along the top and right edges of the
phase-space plot. The bin count is shared with the heatmap bins setting.

Enabling or disabling histograms triggers a full figure redraw because the
`GridSpec` layout changes.

---

## Stats and ellipse overlay

Toggle via the **Twiss overlay** checkbox. When the selected axes are a
conjugate pair `(x, xp)` or `(y, yp)`, the overlay draws:

- Courant-Snyder parameters: ε, β, α, γ in the top-left corner
- 1-sigma RMS covariance ellipse (solid)
- 95% emittance ellipse (dashed, scaled by √(−2 ln 0.05) ≈ 2.45)

For non-conjugate pairs the overlay shows only beam centroid (μ) and
standard deviation (σ) for each axis.

---

## Blit pipeline

The blit pipeline is the key performance mechanism. On the **first render**
after any layout or settings change, a full `canvas.draw()` is called, which
caches the background (axes, ticks, grid, labels). On every subsequent frame:

1. `canvas.restore_region()` paints the cached background.
2. Scatter/heatmap artist data is updated in-place (`set_offsets` / `set_data`).
3. Only the changed artists are redrawn with `ax.draw_artist()`.
4. `canvas.blit(ax.bbox)` flushes the result.

This skips re-rendering the static chrome entirely, allowing smooth
playback even at high particle counts.

A full redraw is triggered only when layout actually changes (histogram toggle,
colorbar toggle, axis mode switch, settings change).

---

## Particle tracking

Individual particles can be tracked across turns. Open the **Track…** dialog
from the toolbar, enter comma-separated particle IDs, and confirm. During
playback, trail lines connect the particle's positions across the last
*N* frames and a dot marks the current position. Trail colours cycle through a
fixed palette distinct from the main scatter colour.

---

## Beam loss highlighting

Press the **Loss** button in the toolbar to toggle loss mode. Particles
present in turn 0 but absent in the current turn are highlighted in red.
The red overlay uses a separate scatter artist rendered on top of the main
scatter.
