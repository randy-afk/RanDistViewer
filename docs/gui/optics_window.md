# Optics Window

The **Optics Window** is a standalone floating window that displays ELEGANT
Twiss functions and a magnet layout strip. Open it from **View → Lattice
Optics…**.

---

## Overview

The window contains a two-row Matplotlib figure:

- **Top row** — β functions (βx in blue, βy in peach) and dispersion (Dx, Dy)
  plotted against the longitudinal coordinate *s*.
- **Bottom row** — magnet layout strip: coloured rectangles representing
  quadrupoles, dipoles, sextupoles, and other elements.

A vertical cursor line appears when hovering over the plot, showing the *s*
position and element name in the status bar.

---

## Loading files

### Twiss file (`.twi`)

Click **Load .twi…** and select an ELEGANT `.twi` output file. This is a
binary SDDS file and is parsed by `models/twi_loader.py`.

The loader reads the columns `s`, `betax`, `betay`, `etax`, `etay` and
any available `alphax`, `alphay`.

### Magnet file (`.mag`)

Click **Load .mag…** and select an ELEGANT `.mag` ASCII file. This file
provides element names, types, and lengths for the magnet strip.

The `.mag` file is optional — if not loaded, the bottom strip is left blank.

---

## Element colour coding

| Element type | Colour |
|---|---|
| QUAD, KQUAD | `#f38ba8` (red) |
| SBEN, RBEN, CSBEND | `#89b4fa` (blue) |
| SEXT, KSEXT | `#a6e3a1` (green) |
| OCT, KOCT | `#f9e2af` (yellow) |
| KICKER, HKICK, VKICK | `#cba6f7` (mauve) |
| RFCA, RFCW | `#94e2d5` (teal) |
| SOLE, WIGGLER | `#fab387` (peach) |
| DRIF | transparent |
| MARK, MONI, WATCH | dark grey |

---

## Controls

| Button | Action |
|---|---|
| **Load .twi…** | Open a Twiss SDDS file |
| **Load .mag…** | Open a magnet description file |
| **βx / βy** | Toggle individual β function traces |
| **Dx / Dy** | Toggle individual dispersion traces |
| **Reset view** | Restore the original s-axis limits |

---

## Implementation notes

The optics window reads the `.twi` file via the binary SDDS parser in
`models/sdds_loader.py`, which is the same parser used for bunch files. The
`.mag` file is read by a separate ASCII parser in `models/twi_loader.py` that
handles ELEGANT's element description format.

Twiss column names (`betax`, `betay`, `etax`, `etay`) are matched
case-insensitively so variations in ELEGANT output are handled gracefully.
