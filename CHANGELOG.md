# Changelog

All notable changes to RanDistViewer will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026

### Added
- Initial release
- Binary SDDS bunch file parser (ELEGANT watch/buncher output)
- Multi-file, multi-panel phase-space plot grid
- Scatter and 2D heatmap modes with Gaussian smoothing
- Blit-based turn-by-turn animation for fast playback
- Marginal histograms and Courant-Snyder / sigma stats overlay
- Axis modes: Auto, Roll, Track, Fixed, Roll+Δ, Track+Δ
- RF bucket separatrix overlay (static and CSV-ramped)
- Particle tracking across turns with trajectory trails
- Beam loss highlighting
- Stats-over-time panel (σ, emittance evolution across turns)
- Correlation matrix dialog
- Lattice optics viewer (.twi binary SDDS + .mag ASCII)
- Session save/load (JSON)
- Plotly HTML export
- Catppuccin Mocha dark theme (matching RanOptics)
- Keyboard shortcuts: Space (play/pause), ←/→ (step frames), Ctrl+O (open)
