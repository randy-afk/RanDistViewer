# Dialogs

RanDistViewer has three auxiliary dialogs accessible from the main toolbar.

---

## RF Bucket Configuration

Open via the **RF Bucket** toolbar button.

Configures the RF separatrix overlay for the `(t, p)` phase-space panel.
The separatrix is only visible when the panel axes are `t` and `p` and an
offset mode (Roll+Δ or Track+Δ) is active.

### Parameters

| Field | Description |
|---|---|
| Particle species | Electron or Proton (sets rest mass automatically) |
| Custom mass (MeV) | Override for other species |
| Momentum compaction αc | Lattice momentum compaction factor |
| Revolution frequency (MHz) | Design revolution frequency |
| Mode | `Static` or `Ramped` |

### Cavities (Static mode)

Add one or more RF cavities. Each cavity requires:

| Field | Description |
|---|---|
| Voltage V (volts) | Peak cavity voltage |
| Harmonic h | RF harmonic number |
| Synchronous phase φs (deg) | Synchronous phase angle |

Click **+ Cavity** to add further cavities. Multi-cavity separatrices are
computed by superposition.

### Ramped RF (CSV mode)

Switch Mode to **Ramped** and click **Load CSV…** to provide a ramp schedule.
The CSV file must have the following column layout:

```
Time, V1, h1, phi_s1[, V2, h2, phi_s2, ...]
```

- `Time` — ramp time in seconds (must match the turn-by-turn time axis)
- Each additional group of three columns defines one cavity: voltage,
  harmonic, synchronous phase

During playback the viewer interpolates the ramp schedule to the current turn's
time coordinate and recomputes the separatrix each frame.

### Apply / Clear / Cancel

- **Apply** — saves the configuration and enables the overlay
- **Clear** — removes the current RF configuration and hides the overlay
- **Cancel** — discards changes

---

## Correlation Matrix

Open via the **Corr** toolbar button.

Displays a 7×7 Pearson correlation matrix for the columns
`x, xp, y, yp, t, p, dt` computed from the particles in the current turn.
The matrix is rendered as a colour-mapped heatmap with values annotated in each
cell. Strongly correlated pairs appear in warm colours; anti-correlated pairs in
cool colours.

The matrix updates automatically when the turn changes while the dialog is open.

---

## Stats-Over-Time Panel

Open via the **Stats** toolbar button.

Plots beam statistics as a function of turn number for all loaded files.
For each file, the following quantities are shown as separate subplots:

| Quantity | Description |
|---|---|
| σx | RMS horizontal beam size (m) |
| σy | RMS vertical beam size (m) |
| σp | RMS momentum spread (m·βγ) |
| σt | RMS bunch length (s) |
| εx | Horizontal RMS emittance (m·rad) |
| εy | Vertical RMS emittance (m·rad) |

Statistics are pre-computed at file load time and cached, so the panel renders
instantly without re-scanning the data.

The emittance values use the Courant-Snyder formula:
ε = √(⟨x²⟩⟨x'²⟩ − ⟨xx'⟩²) for the respective conjugate pair.
