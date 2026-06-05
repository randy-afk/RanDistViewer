"""
RanBeam — physics/rf_bucket.py
================================
Pure RF bucket physics. Zero Qt. Zero GUI.
All functions take plain Python/numpy values and return numpy arrays.
"""

import numpy as np


def compute_rf_separatrix(cavities, alphac, p_central, mass_mev,
                           f_rev_hz, n_points=600):
    """
    Compute the RF separatrix curve in (dt, delta_p) space.

    Parameters
    ----------
    cavities   : list of (V_volts, harmonic_h, phi_s_rad)
    alphac     : momentum compaction factor
    p_central  : central momentum in units of m*beta*gamma
    mass_mev   : particle rest mass in MeV
    f_rev_hz   : revolution frequency in Hz
    n_points   : number of curve points

    Returns
    -------
    (dt_sep, delta_sep) : numpy arrays, or (None, None) if separatrix
                          cannot be computed (e.g. above transition with
                          no stable bucket).
    """
    if not cavities:
        return None, None

    bg        = float(p_central)
    gamma     = np.sqrt(1.0 + bg**2)
    E0_eV     = mass_mev * 1e6 * gamma
    eta       = float(alphac) - 1.0 / gamma**2
    omega_rev = 2.0 * np.pi * f_rev_hz

    V1, h1, phi_s = cavities[0]
    phi_ufp = np.pi - phi_s

    def _F_single(phi):
        return (-np.cos(phi) - np.cos(phi_s)
                + (np.pi - phi - phi_s) * np.sin(phi_s))

    if len(cavities) > 1:
        def _F(phi):
            val = _F_single(phi)
            for V, h, phi_sv in cavities[1:]:
                ratio = h / h1
                phi_i = ratio * phi + (phi_sv - ratio * phi_s)
                val += (V / V1) * (
                    -np.cos(phi_i) - np.cos(phi_sv)
                    + (np.pi - phi_i - phi_sv) * np.sin(phi_sv)
                )
            return val
    else:
        _F = _F_single

    factor  = V1 / (np.pi * h1 * abs(eta) * E0_eV)
    eps     = 0.002
    phi_arr = np.linspace(phi_ufp + eps, 2.0 * np.pi - phi_ufp - eps, n_points)
    Fvals   = np.array([_F(p) for p in phi_arr])
    delta2  = factor * Fvals
    mask    = delta2 >= 0

    if not mask.any():
        return None, None

    phi_v   = phi_arr[mask]
    dv      = np.sqrt(np.maximum(delta2[mask], 0))
    dt_v    = (phi_v - phi_s) / (h1 * omega_rev)

    dt_sep    = np.concatenate([dt_v,   dt_v[::-1]])
    delta_sep = np.concatenate([dv,    -dv[::-1]])
    return dt_sep, delta_sep


def bucket_half_height(cavities, alphac, p_central, mass_mev, f_rev_hz):
    """
    Return the maximum delta (momentum deviation) of the separatrix,
    or None if the bucket cannot be computed.
    Used for autoscaling bucket view.
    """
    dt, dl = compute_rf_separatrix(
        cavities, alphac, p_central, mass_mev, f_rev_hz)
    if dl is None:
        return None
    return float(np.abs(dl).max())
