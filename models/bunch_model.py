"""
RanBeam — models/bunch_model.py
================================
BunchFile dataclass and the compute engine.
Owns all pre-computation that happens once on file load
(stats cache, trajectory cache, loss map).
Zero Qt.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .sdds_loader import COLUMNS
from theme import FILE_COLORS
from physics.beam_stats import compute_all_stats

# Conjugate pairs used for emittance tracking
_CONJ = [("x", "xp"), ("y", "yp")]
_STAT_COLS = ["x", "xp", "y", "yp", "t", "p", "dt"]


@dataclass
class BunchFile:
    """
    Represents one loaded SDDS bunch file plus all derived caches.
    Created by BunchModel.load_file(); never instantiated directly by GUI.
    """
    label:   str
    path:    str
    color:   str
    pages:   list          # list of {"params": dict, "data": ndarray}

    # Pre-computed (filled by _precompute)
    stats_cache: dict | None = field(default=None, repr=False)
    traj_cache:  dict        = field(default_factory=dict, repr=False)
    loss_map:    dict        = field(default_factory=dict, repr=False)

    @property
    def n_pages(self) -> int:
        return len(self.pages)

    def page(self, idx: int) -> dict:
        return self.pages[min(idx, self.n_pages - 1)]

    def precompute_stats(self) -> None:
        """Compute and cache per-column statistics across all pages."""
        if self.stats_cache is not None:
            return
        self.stats_cache = compute_all_stats(
            self.pages, _STAT_COLS, _CONJ)

    def precompute_trajectories(self, particle_ids: list[int]) -> None:
        """
        Build trajectory arrays for the requested particle IDs.
        traj_cache[pid] = list of (row_array | None) per page.
        """
        pid_col_idx = COLUMNS.index("particleID")
        for pid in particle_ids:
            if pid in self.traj_cache:
                continue
            traj = []
            for pg in self.pages:
                pid_col = pg["data"][:, pid_col_idx].astype(int)
                hits    = np.where(pid_col == pid)[0]
                traj.append(pg["data"][hits[0]] if len(hits) else None)
            self.traj_cache[pid] = traj

    def precompute_loss_map(self) -> None:
        """
        Identify lost particles (present in some page but absent in the last).
        loss_map = {pid: last_page_index_seen}
        """
        pid_col_idx = COLUMNS.index("particleID")
        lmap = {}
        for pg_idx, pg in enumerate(self.pages):
            for pid in pg["data"][:, pid_col_idx].astype(int):
                lmap[pid] = pg_idx
        last_pids = set(
            self.pages[-1]["data"][:, pid_col_idx].astype(int))
        self.loss_map = {
            pid: pg for pid, pg in lmap.items() if pid not in last_pids}

    def clear_trajectory_cache(self) -> None:
        self.traj_cache.clear()


class BunchModel:
    """
    Central model: manages a list of BunchFile objects and provides
    accessors used by the GUI via signals.  Zero Qt widgets here.
    """

    def __init__(self):
        self._files: list[BunchFile] = []

    # ── File management ───────────────────────────────────────────────────

    def load_file(self, path: str, pages: list) -> BunchFile:
        """Register a newly loaded file and return the BunchFile."""
        label = Path(path).stem[:18]
        # Ensure unique label
        existing = {f.label for f in self._files}
        base, n = label, 1
        while label in existing:
            label = f"{base}_{n}"
            n += 1
        color = FILE_COLORS[len(self._files) % len(FILE_COLORS)]
        bf    = BunchFile(label=label, path=path, color=color, pages=pages)
        self._files.append(bf)
        return bf

    def remove_file(self, label: str) -> None:
        self._files = [f for f in self._files if f.label != label]

    def clear(self) -> None:
        self._files.clear()

    # ── Accessors ─────────────────────────────────────────────────────────

    @property
    def files(self) -> list[BunchFile]:
        return list(self._files)

    @property
    def labels(self) -> list[str]:
        return [f.label for f in self._files]

    def file_by_label(self, label: str) -> BunchFile | None:
        for f in self._files:
            if f.label == label:
                return f
        return None

    @property
    def n_files(self) -> int:
        return len(self._files)

    @property
    def max_pages(self) -> int:
        if not self._files:
            return 0
        return max(f.n_pages for f in self._files)

    # ── Serialisation (session save/load) ─────────────────────────────────

    def to_session(self) -> list[dict]:
        return [{"path": f.path, "label": f.label} for f in self._files]

    def restore_session_files(self, entries: list[dict],
                               loader_fn) -> list[str]:
        """
        Re-load files from a session dict.
        loader_fn(path) must return a list of pages or raise.
        Returns list of paths that failed (file not found / parse error).
        """
        failed = []
        for entry in entries:
            fpath = entry.get("path", "")
            if not Path(fpath).exists():
                failed.append(fpath)
                continue
            try:
                pages = loader_fn(fpath)
                bf    = self.load_file(fpath, pages)
                # Override label from session
                bf.label = entry.get("label", bf.label)
            except Exception:
                failed.append(fpath)
        return failed
