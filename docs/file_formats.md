# File Formats

RanDistViewer reads three external file formats.

---

## Binary SDDS bunch files

ELEGANT produces binary SDDS files from `watch` and `buncher` elements. These
are the primary input to RanDistViewer.

### Column layout

Each particle occupies exactly **64 bytes** with the following fixed layout:

| Column | Type | Unit | Size |
|---|---|---|---|
| `x` | float64 (LE) | m | 8 bytes |
| `xp` | float64 (LE) | — | 8 bytes |
| `y` | float64 (LE) | m | 8 bytes |
| `yp` | float64 (LE) | — | 8 bytes |
| `t` | float64 (LE) | s | 8 bytes |
| `p` | float64 (LE) | m·βγ | 8 bytes |
| `dt` | float64 (LE) | s | 8 bytes |
| `particleID` | uint64 (LE) | — | 8 bytes |

All float columns use IEEE 754 double precision, little-endian byte order.

!!! note "p column units"
    The `p` column stores normalised momentum m·βγ, not kinetic or total
    energy. To convert to momentum deviation δ = Δp/p₀, subtract the
    `p_central` parameter from the SDDS page header and divide by p₀.

### Multi-page structure

Each turn is stored as a separate **page** (SDDS terminology for a data
record). A single file can contain hundreds or thousands of pages. The loader
reads all pages into memory on open, building a list of
`{"params": dict, "data": ndarray}` entries.

### Page parameters

Each page header contains scalar parameters including:

| Parameter | Description |
|---|---|
| `Charge` | Total bunch charge (C) |
| `pCentral` | Central momentum (m·βγ) |
| `tCentral` | Central time (s) |
| `Pass` | Pass (turn) number |
| `n_particle` | Particle count for this page |

`pCentral` and `tCentral` are used by the Roll+Δ and Track+Δ axis modes to
subtract the reference offset before plotting.

### File extensions

ELEGANT uses various extensions for watch-point output. All are accepted:

`.bun`, `.wat`, `.wcp`, `.wfin`, and generic extensionless SDDS files.
The loader detects the SDDS binary signature regardless of extension.

---

## ELEGANT Twiss file (`.twi`)

Binary SDDS file produced by ELEGANT's Twiss output command. Parsed by
`models/twi_loader.py` using the same binary SDDS reader.

Required columns: `s`, `betax`, `betay`

Optional columns: `etax`, `etay`, `alphax`, `alphay`

---

## ELEGANT magnet file (`.mag`)

ASCII file describing lattice elements for the optics window magnet strip.
Each line contains whitespace-delimited fields:

```
ElementName   ElementType   s_begin   length
```

The loader matches element types against the colour table in `theme.py`
(`ELE_COLORS`) to assign display colours. Unrecognised types are rendered in
dark grey.

---

## Session file (`.json`)

See the [Sessions](session.md) page for the complete session file format.
