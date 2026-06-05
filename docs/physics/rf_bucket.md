# RF Bucket

The RF bucket separatrix is computed in `physics/rf_bucket.py`. This module
is pure NumPy with no Qt dependency.

---

## Phase-space coordinates

The separatrix is computed in `(Δt, Δδ)` space where:

- **Δt** = time deviation from the synchronous particle (seconds)
- **Δδ** = `Δp / p₀` = fractional momentum deviation

In the viewer, this maps directly to the `t` and `p` columns after
subtracting the reference values `t_central` and `p_central` stored in the
SDDS page header. This is why the RF overlay requires **Roll+Δ** or **Track+Δ**
axis mode.

---

## Single-cavity separatrix

For a single RF cavity with peak voltage V, harmonic h, and synchronous phase
φs, the separatrix is the level curve of the Hamiltonian that passes through
the unstable fixed point (UFP).

The UFP occurs at φUFP = π − φs. The Hamiltonian at the separatrix satisfies:

```
H(φ, δ) = H(φUFP, 0)
```

The code parameterises the separatrix by scanning φ over the stable phase
interval and solving for the corresponding δ at each point using:

```python
F(phi) = -cos(phi) - cos(phi_s)
       + (pi - phi - phi_s) * sin(phi_s)

delta(phi) = sqrt(2 * eV / (omega_rev * h * eta * E0) * F(phi))
```

where η = αc − 1/γ² is the phase-slip factor and E0 is the particle energy.

---

## Multi-cavity separatrix

When more than one cavity is configured, the Hamiltonian is extended by
summing the contributions from each cavity. For a second cavity with voltage
V₂, harmonic h₂, and synchronous phase φs₂, the ratio h₂/h₁ determines
the phase relationship between cavities:

```python
phi_2 = (h2 / h1) * phi + (phi_s2 - (h2 / h1) * phi_s1)
```

and the Hamiltonian term for cavity 2 is scaled by V₂/V₁. The separatrix
shape changes significantly — in particular, it can develop additional stable
islands — so care is needed in interpreting the overlay.

---

## Ramped RF

When a ramp CSV is loaded, the viewer linearly interpolates all cavity
parameters (V, h, φs) to the current page's `t_central` value and recomputes
the separatrix. This allows tracking the changing bucket shape during energy
ramps in multi-turn simulations.

!!! warning "Stationary bucket test"
    If the separatrix appears misaligned at the start of a ramp, first verify
    the static (non-ramped) case with known parameters. A common source of
    error is incorrect units for the revolution frequency or momentum
    compaction factor.

---

## Output

`compute_rf_separatrix()` returns a pair of NumPy arrays `(dt_sep, delta_sep)`
that can be passed directly to `ax.plot()`. If the separatrix cannot be
computed (e.g. above transition with no stable bucket, or zero cavity voltage),
both arrays are `None`.

---

## Function signature

```python
def compute_rf_separatrix(
    cavities,     # list of (V_volts, harmonic_h, phi_s_rad)
    alphac,       # momentum compaction factor (float)
    p_central,    # central momentum in units of m·βγ (float)
    mass_mev,     # particle rest mass in MeV (float)
    f_rev_hz,     # revolution frequency in Hz (float)
    n_points=600, # number of output curve points
) -> tuple[np.ndarray | None, np.ndarray | None]:
```
