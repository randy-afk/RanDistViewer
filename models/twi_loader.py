"""
RanBeam — models/twi_loader.py
================================
Parsers for ELEGANT optics files:
  - .twi  (binary SDDS Twiss output)
  - .mag  (ASCII magnet profile file)
Zero Qt.
"""

import struct
from pathlib import Path

import numpy as np

from .sdds_loader import _parse_header, _read_param

# ── Twiss column list (fallback if header doesn't define columns) ─────────────

_TWI_FALLBACK_COLS = [
    ("s",                "double"),
    ("betax",            "double"),
    ("alphax",           "double"),
    ("psix",             "double"),
    ("etax",             "double"),
    ("etaxp",            "double"),
    ("xAperture",        "double"),
    ("betay",            "double"),
    ("alphay",           "double"),
    ("psiy",             "double"),
    ("etay",             "double"),
    ("etayp",            "double"),
    ("yAperture",        "double"),
    ("pCentral0",        "double"),
    ("ElementName",      "string"),
    ("ElementOccurence", "long"),
    ("ElementType",      "string"),
    ("ChamberShape",     "string"),
    ("dI1",              "double"),
    ("dI2",              "double"),
    ("dI3",              "double"),
    ("dI4",              "double"),
    ("dI5",              "double"),
]


# ── Twi reader ────────────────────────────────────────────────────────────────

def read_twi_file(path: str) -> dict:
    """
    Parse an ELEGANT .twi binary SDDS file.

    Returns
    -------
    {
        "data":   {col_name: array_or_list, ...},
        "params": {param_name: value, ...},
    }
    """
    path = str(path)
    with open(path, "rb") as f:
        header_raw = f.read(131072)

    binary_start, param_defs, fixed_params, col_defs = _parse_header(header_raw)
    params      = dict(fixed_params)
    actual_cols = col_defs if col_defs else _TWI_FALLBACK_COLS
    raw_data    = {c[0]: [] for c in actual_cols}

    with open(path, "rb") as f:
        f.seek(binary_start)

        # Row count
        hdr = f.read(4)
        if len(hdr) < 4:
            return {"data": {}, "params": params}
        n_rows = struct.unpack("<i", hdr)[0]
        if n_rows <= 0 or n_rows > 1_000_000:
            return {"data": {}, "params": params}

        # Parameters
        for pname, ptype in param_defs:
            try:
                params[pname] = _read_param(f, ptype)
            except Exception:
                break

        # Rows
        for _ in range(n_rows):
            try:
                for col_name, col_type in actual_cols:
                    if col_type == "double":
                        raw = f.read(8)
                        if len(raw) < 8:
                            raise EOFError
                        raw_data[col_name].append(struct.unpack("<d", raw)[0])
                    elif col_type == "long":
                        raw = f.read(4)
                        if len(raw) < 4:
                            raise EOFError
                        raw_data[col_name].append(struct.unpack("<i", raw)[0])
                    elif col_type == "string":
                        raw = f.read(4)
                        if len(raw) < 4:
                            raise EOFError
                        slen = struct.unpack("<i", raw)[0]
                        if slen < 0 or slen > 10000:
                            raw_data[col_name].append("")
                        else:
                            raw_data[col_name].append(
                                f.read(slen).decode("latin-1", errors="replace"))
            except (EOFError, struct.error):
                break

    # Convert numeric columns to numpy arrays
    result = {}
    for col_name, col_type in actual_cols:
        if col_type == "double":
            result[col_name] = np.array(raw_data[col_name], dtype=np.float64)
        elif col_type in ("long", "short"):
            result[col_name] = np.array(raw_data[col_name], dtype=np.int32)
        else:
            result[col_name] = raw_data[col_name]

    return {"data": result, "params": params}


# ── Mag file reader ───────────────────────────────────────────────────────────

def read_mag_file(path: str) -> dict:
    """
    Parse an ELEGANT .mag ASCII file.
    Columns: ElementName  ElementType  s  Profile

    Returns
    -------
    {
        "name":    list of str,
        "etype":   list of str,
        "s":       np.ndarray,
        "profile": np.ndarray,
    }
    """
    names, etypes, s_vals, profiles = [], [], [], []
    with open(str(path), "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("!") or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            try:
                names.append(parts[0])
                etypes.append(parts[1])
                s_vals.append(float(parts[2]))
                profiles.append(float(parts[3]))
            except (ValueError, IndexError):
                continue

    return {
        "name":    names,
        "etype":   etypes,
        "s":       np.array(s_vals,   dtype=np.float64),
        "profile": np.array(profiles, dtype=np.float64),
    }
