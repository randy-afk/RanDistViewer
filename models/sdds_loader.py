"""
RanBeam — models/sdds_loader.py
================================
Binary SDDS parser for ELEGANT bunch files (.bun, .wat, etc.)
Zero Qt. Returns plain Python dicts and numpy arrays.
"""

import struct
import re
from pathlib import Path

import numpy as np

# ── Particle layout ───────────────────────────────────────────────────────────

COLUMNS = ["x", "xp", "y", "yp", "t", "p", "dt", "particleID"]

COL_UNITS = {
    "x":          "m",
    "xp":         "",
    "y":          "m",
    "yp":         "",
    "t":          "s",
    "p":          "m·βγ",
    "dt":         "s",
    "particleID": "",
}

PARTICLE_DTYPE = np.dtype([
    ("x",          "<f8"),
    ("xp",         "<f8"),
    ("y",          "<f8"),
    ("yp",         "<f8"),
    ("t",          "<f8"),
    ("p",          "<f8"),
    ("dt",         "<f8"),
    ("particleID", "<u8"),
])
PARTICLE_SIZE = PARTICLE_DTYPE.itemsize   # 64 bytes

DEFAULT_PAIRS = [("x", "xp"), ("y", "yp"), ("t", "p"), ("x", "y")]


# ── Header parser ─────────────────────────────────────────────────────────────

def _parse_header(raw: bytes) -> tuple:
    """
    Parse the ASCII header of a binary SDDS file.

    Returns
    -------
    (binary_start, param_defs, fixed_params, col_defs)

    binary_start : int   — byte offset where binary data begins
    param_defs   : list  — [(name, type), ...] for non-fixed parameters
    fixed_params : dict  — {name: value} for fixed_value parameters
    col_defs     : list  — [(name, type), ...] column definitions from header
    """
    data_pos = raw.find(b"&data")
    if data_pos == -1:
        raise ValueError("Could not find '&data' — not a valid SDDS file.")
    nl = raw.find(b"\n", data_pos)
    if nl == -1:
        raise ValueError("Malformed header: no newline after '&data'.")
    binary_start = nl + 1
    header_text  = raw[:binary_start].decode("latin-1", errors="replace")

    # Parameters
    param_defs, fixed_params = [], {}
    for block in re.findall(r'&parameter(.*?)&end', header_text, re.DOTALL):
        name_m  = re.search(r'name\s*=\s*([\w/]+)', block)
        type_m  = re.search(r'type\s*=\s*(\w+)',    block)
        fixed_m = re.search(r'fixed_value\s*=\s*(\S+)', block)
        if not name_m or not type_m:
            continue
        name, ptype = name_m.group(1), type_m.group(1)
        if fixed_m:
            fv = fixed_m.group(1).rstrip(',')
            try:
                fixed_params[name] = float(fv) if ptype == "double" else int(fv)
            except ValueError:
                fixed_params[name] = fv
        else:
            param_defs.append((name, ptype))

    # Columns (used by twi reader and generic SDDS files)
    col_defs = []
    for block in re.findall(r'&column(.*?)&end', header_text, re.DOTALL):
        name_m = re.search(r'name\s*=\s*(\w+)', block)
        type_m = re.search(r'type\s*=\s*(\w+)', block)
        if name_m and type_m:
            col_defs.append((name_m.group(1), type_m.group(1)))

    return binary_start, param_defs, fixed_params, col_defs


def _read_param(f, ptype: str):
    """Read one parameter value from the binary stream."""
    if ptype == "double":
        raw = f.read(8)
        if len(raw) < 8:
            raise EOFError
        return struct.unpack("<d", raw)[0]
    elif ptype in ("long", "short"):
        raw = f.read(4)
        if len(raw) < 4:
            raise EOFError
        return struct.unpack("<i", raw)[0]
    elif ptype == "string":
        raw = f.read(4)
        if len(raw) < 4:
            raise EOFError
        slen = struct.unpack("<i", raw)[0]
        if slen < 0 or slen > 1_000_000:
            raise ValueError(f"String length out of range: {slen}")
        return f.read(slen).decode("latin-1", errors="replace")
    else:
        return None


# ── Bunch file reader ─────────────────────────────────────────────────────────

def read_sdds_file(filepath: str) -> list[dict]:
    """
    Read a binary SDDS bunch file (all pages).

    Each page is a dict:
        {
            "params": {name: value, ...},
            "data":   np.ndarray shape (N, len(COLUMNS)),  float64
        }

    Raises ValueError on malformed files.
    """
    filepath = str(filepath)
    with open(filepath, "rb") as f:
        header_raw = f.read(65536)
    binary_start, param_defs, fixed_params, _ = _parse_header(header_raw)

    pages = []
    with open(filepath, "rb") as f:
        f.seek(binary_start)
        while True:
            hdr = f.read(4)
            if len(hdr) < 4:
                break
            n_rows = struct.unpack("<i", hdr)[0]
            if n_rows < 0 or n_rows > 10_000_000:
                break
            if n_rows == 0:
                continue

            params = dict(fixed_params)
            ok = True
            for pname, ptype in param_defs:
                try:
                    params[pname] = _read_param(f, ptype)
                except (EOFError, struct.error, ValueError):
                    ok = False
                    break
            if not ok:
                break

            byte_count = n_rows * PARTICLE_SIZE
            chunk = f.read(byte_count)
            if len(chunk) < PARTICLE_SIZE:
                break
            if len(chunk) < byte_count:
                n_rows = len(chunk) // PARTICLE_SIZE
                chunk  = chunk[:n_rows * PARTICLE_SIZE]

            structured = np.frombuffer(chunk, dtype=PARTICLE_DTYPE).copy()
            data = np.column_stack(
                [structured[col].astype(np.float64) for col in COLUMNS])
            del structured, chunk
            pages.append({"params": params, "data": data})

    return pages
