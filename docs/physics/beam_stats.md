# Beam Statistics

All beam statistics are computed in `physics/beam_stats.py`. This module
is pure NumPy/SciPy with no Qt dependency.

---

## Courant-Snyder parameters

Given a distribution of particles with positions `x` and angles `x'`,
the Courant-Snyder (Twiss) parameters are derived from the sigma matrix:

```
σ₁₁ = ⟨x²⟩      (mean-subtracted)
σ₁₂ = ⟨xx'⟩
σ₂₂ = ⟨x'²⟩

ε   = sqrt(σ₁₁ σ₂₂ − σ₁₂²)    ← RMS emittance
β   = σ₁₁ / ε
α   = −σ₁₂ / ε
γ   = σ₂₂ / ε
```

`compute_twiss(xd, yd)` returns a dict `{emit, beta, alpha, gamma}` or `None`
if the distribution is degenerate (fewer than 3 particles or zero determinant).

Conjugate pairs for which Twiss parameters are meaningful:
`(x, xp)` and `(y, yp)`.

---

## Emittance ellipses

Two ellipses are drawn as overlays on the phase-space plot.

### 1-sigma ellipse

The covariance ellipse is constructed from the eigendecomposition of the 2×2
covariance matrix. It encloses the 1-sigma RMS distribution and is drawn as a
solid line.

```python
def compute_covariance_ellipse(xd, yd, n_pts=200) -> tuple[np.ndarray, np.ndarray]:
    ...
```

Returns `(ex, ey)` arrays ready for `ax.plot()`, centred at
`(xd.mean(), yd.mean())`.

### 95% emittance ellipse

A second dashed ellipse is drawn scaled by the factor:

```
k₉₅ = sqrt(−2 ln(0.05)) ≈ 2.4477
```

This is the scaling factor that maps the 1-sigma ellipse to the ellipse
containing 95% of a 2D Gaussian distribution.

---

## Stats overlay

The `draw_stats_overlay()` function renders text and ellipses directly onto
a Matplotlib `Axes` object. For conjugate pairs it shows:

```
ε = 1.23e-06 m·rad
β = 12.4 m
α = -0.31
γ = 0.087 m⁻¹
```

For non-conjugate pairs it shows:

```
μ_x = 0.000 mm    σ_x = 0.123 mm
μ_y = 0.000 mrad  σ_y = 1.45 mrad
```

Units are chosen automatically: metres → mm → µm based on the magnitude.

---

## Pre-computed statistics cache

`compute_all_stats(pages, stat_cols, conj_pairs)` iterates all pages of a
loaded file and computes per-page mean, σ, and emittance for each column.
The result is stored in `BunchFile.stats_cache` at load time and used by:

- The **Stats-Over-Time** panel (emittance and σ evolution plots)
- Initial axis limit estimation for Roll/Track modes

---

## Function reference

```python
def compute_twiss(xd, yd) -> dict | None:
    """Courant-Snyder parameters from a particle distribution."""

def compute_covariance_ellipse(xd, yd, n_pts=200) -> tuple:
    """1-sigma covariance ellipse centred at the beam centroid."""

def draw_stats_overlay(ax, xd, yd, xcol, ycol, color) -> dict:
    """Draw Twiss stats text and emittance ellipses onto ax.
    Returns a dict of artist handles for blit re-use."""

def compute_all_stats(pages, stat_cols, conj_pairs) -> dict:
    """Pre-compute per-page statistics for all columns in a BunchFile."""
```
