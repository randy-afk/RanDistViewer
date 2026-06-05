"""
RanBeam — physics/beam_stats.py
================================
Pure beam statistics and Courant-Snyder analysis.
Drawing helpers that operate on matplotlib Axes objects are here too,
since they are tightly coupled to the physics and contain no Qt widgets.
"""

import numpy as np

# Pulled up here so it's easy to find and change.
_RMS95 = 2.4477   # sqrt(-2 * ln(0.05)) — factor for 95% emittance ellipse

# Conjugate phase-space pairs for which Twiss parameters make sense.
CONJUGATE_PAIRS = frozenset([
    ("x", "xp"), ("xp", "x"),
    ("y", "yp"), ("yp", "y"),
])


# ── Twiss / sigma-matrix ──────────────────────────────────────────────────────

def compute_twiss(xd: np.ndarray, yd: np.ndarray) -> dict | None:
    """
    Compute Courant-Snyder parameters from a particle distribution.

    Returns a dict with keys: emit, beta, alpha, gamma
    or None if the distribution is degenerate (< 3 particles or zero determinant).
    """
    if len(xd) < 3:
        return None
    xc = xd - xd.mean()
    yc = yd - yd.mean()
    s11 = float(np.mean(xc ** 2))
    s12 = float(np.mean(xc * yc))
    s22 = float(np.mean(yc ** 2))
    det = s11 * s22 - s12 ** 2
    if det <= 0:
        return None
    emit = float(np.sqrt(det))
    return {
        "emit":  emit,
        "beta":  s11 / emit,
        "alpha": -s12 / emit,
        "gamma": s22 / emit,
    }


def compute_covariance_ellipse(xd: np.ndarray, yd: np.ndarray,
                                n_pts: int = 200):
    """
    Return (ex, ey) arrays for the 1-sigma covariance ellipse,
    centred at (xd.mean(), yd.mean()).
    """
    xdev = xd - xd.mean()
    ydev = yd - yd.mean()
    cov  = np.array([[np.mean(xdev ** 2), np.mean(xdev * ydev)],
                     [np.mean(xdev * ydev), np.mean(ydev ** 2)]])
    vals, vecs = np.linalg.eigh(cov)
    vals = np.maximum(vals, 0)
    theta = np.linspace(0, 2 * np.pi, n_pts)
    unit  = np.array([np.cos(theta), np.sin(theta)])
    basis = vecs @ (np.sqrt(vals)[:, None] * unit)
    return basis[0], basis[1]


# ── Per-column statistics ─────────────────────────────────────────────────────

def page_stats(data: np.ndarray, col_indices: list[int]) -> dict:
    """
    Compute mean, sigma, min, max for each column index.
    Returns dict: {col_idx: {"mean", "sigma", "min", "max"}}
    """
    result = {}
    for ci in col_indices:
        cd = data[:, ci]
        result[ci] = {
            "mean":  float(cd.mean()),
            "sigma": float(cd.std()),
            "min":   float(cd.min()),
            "max":   float(cd.max()),
        }
    return result


def compute_all_stats(pages: list, col_names: list[str],
                      conj_pairs: list[tuple]) -> dict:
    """
    Pre-compute statistics across all pages for a loaded file.
    Called once on file load, not per frame.

    Returns
    -------
    {
        "stats": {col: {"mean": array, "sigma": array, "min": array, "max": array}},
        "emit":  {(cn, cm): array},
        "n_pages": int,
    }
    """
    sc   = {col: {"mean": [], "sigma": [], "min": [], "max": []}
            for col in col_names}
    emit = {pair: [] for pair in conj_pairs}

    for pg in pages:
        data = pg["data"]
        for col in col_names:
            ci = col_names.index(col)
            cd = data[:, ci]
            sc[col]["mean"].append(float(cd.mean()))
            sc[col]["sigma"].append(float(cd.std()))
            sc[col]["min"].append(float(cd.min()))
            sc[col]["max"].append(float(cd.max()))
        for cn, cm in conj_pairs:
            xi = col_names.index(cn)
            yi = col_names.index(cm)
            xd = data[:, xi] - data[:, xi].mean()
            yd = data[:, yi] - data[:, yi].mean()
            det = (float(np.mean(xd ** 2)) * float(np.mean(yd ** 2))
                   - float(np.mean(xd * yd)) ** 2)
            emit[(cn, cm)].append(float(np.sqrt(max(det, 0))))

    for col in col_names:
        for k in sc[col]:
            sc[col][k] = np.array(sc[col][k])
    for pair in conj_pairs:
        emit[pair] = np.array(emit[pair])

    return {"stats": sc, "emit": emit, "n_pages": len(pages)}


# ── Matplotlib overlay drawing ────────────────────────────────────────────────
# These take an Axes object but contain zero Qt and zero GUI state.

def draw_stats_overlay(ax, xd, yd, color, xn="x", yn="y",
                        p_central=None,
                        artists: dict | None = None) -> dict:
    """
    Draw (or update) the stats overlay on *ax*:
      - Crosshairs at (mean_x, mean_y)
      - 1-sigma covariance ellipse
      - 95% emittance ellipse (dashed)
      - Twiss text box (conjugate pairs only)
      - RMS sigma text box

    Parameters
    ----------
    artists : dict of previously created artists (for in-place update).
              Pass None on first call; pass the returned dict on updates.

    Returns
    -------
    Updated artists dict.  Store this and pass it back next frame.
    """
    if artists is None:
        artists = {}

    xc = float(xd.mean());  yc = float(yd.mean())
    xs = float(xd.std()) or 1e-10
    ys = float(yd.std()) or 1e-10

    ex, ey = compute_covariance_ellipse(xd, yd)

    # ── Crosshairs ────────────────────────────────────────────────────────
    if "vline" not in artists:
        artists["vline"] = ax.axvline(
            xc, color=color, linewidth=0.8, linestyle="--", alpha=0.7, zorder=5)
        artists["hline"] = ax.axhline(
            yc, color=color, linewidth=0.8, linestyle="--", alpha=0.7, zorder=5)
    else:
        artists["vline"].set_xdata([xc, xc])
        artists["hline"].set_ydata([yc, yc])

    # ── 1-sigma ellipse ───────────────────────────────────────────────────
    if "ellipse1" not in artists:
        (artists["ellipse1"],) = ax.plot(
            xc + ex, yc + ey,
            color=color, linewidth=1.2, alpha=0.9, zorder=6)
    else:
        artists["ellipse1"].set_data(xc + ex, yc + ey)

    # ── 95% ellipse ───────────────────────────────────────────────────────
    if "ellipse95" not in artists:
        (artists["ellipse95"],) = ax.plot(
            xc + ex * _RMS95, yc + ey * _RMS95,
            color=color, linewidth=1.0, alpha=0.45,
            linestyle="--", zorder=6)
    else:
        artists["ellipse95"].set_data(xc + ex * _RMS95, yc + ey * _RMS95)

    # ── Twiss text (conjugate pairs only) ─────────────────────────────────
    if (xn, yn) in CONJUGATE_PAIRS:
        tw = compute_twiss(xd, yd)
        tw_txt = (f"emit = {tw['emit']:.3g} m\n"
                  f"beta = {tw['beta']:.3g} m\n"
                  f"alph = {tw['alpha']:.3g}\n"
                  f"gamm = {tw['gamma']:.3g} /m") if tw else ""
    else:
        tw_txt = ""

    _bbox = dict(boxstyle="round,pad=0.3", facecolor="#0a0a18",
                 edgecolor=color, alpha=0.75)
    if "twiss_txt" not in artists:
        artists["twiss_txt"] = ax.text(
            0.02, 0.98, tw_txt,
            transform=ax.transAxes, va="top", ha="left",
            fontsize=10.5, family="monospace", color=color,
            bbox=_bbox, zorder=10,
            visible=bool(tw_txt))
    else:
        artists["twiss_txt"].set_text(tw_txt)
        artists["twiss_txt"].set_visible(bool(tw_txt))

    # ── Sigma text ────────────────────────────────────────────────────────
    def _fmt_sigma(col, sigma):
        if col == "p" and p_central and float(p_central) != 0:
            return f"σ_δ = {sigma / abs(float(p_central)):.4g}"
        return f"σ_{col} = {sigma:.4g}"

    sig_txt = _fmt_sigma(xn, xs) + "\n" + _fmt_sigma(yn, ys) + "\n[RMS]"
    _bbox2  = dict(boxstyle="round,pad=0.3", facecolor="#0a0a18",
                   edgecolor="#555577", alpha=0.75)
    if "sigma_txt" not in artists:
        artists["sigma_txt"] = ax.text(
            0.98, 0.98, sig_txt,
            transform=ax.transAxes, va="top", ha="right",
            fontsize=10.5, family="monospace", color="white",
            bbox=_bbox2, zorder=10)
    else:
        artists["sigma_txt"].set_text(sig_txt)

    return artists
