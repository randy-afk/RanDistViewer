# GUI Overview

The RanDistViewer window is divided into four main regions.

---

## Main window layout

```
┌─────────────────────────────────────────────────────┐
│  Menu bar  (File · View)                            │
├─────────────────────────────────────────────────────┤
│  Header  [logo] RanDistViewer  [toolbar buttons]    │
├──────────────────────────────────────┬──────────────┤
│                                      │              │
│   Panel grid                         │  Sidebar     │
│   (one or more PlotPanel widgets)    │  (scrollable)│
│                                      │              │
├──────────────────────────────────────┴──────────────┤
│  Status bar                                         │
└─────────────────────────────────────────────────────┘
```

---

## Menu bar

### File menu

| Item | Action |
|---|---|
| Open SDDS file… | Load a binary SDDS bunch file |
| Save Session… | Save full GUI state to JSON |
| Load Session… | Restore a saved session |
| Export panels… | Save all panels as interactive Plotly HTML |

### View menu

| Item | Action |
|---|---|
| + Panel | Add a new plot panel |
| − Panel | Remove the last plot panel |
| Lattice Optics… | Open the standalone optics viewer window |

---

## Header toolbar

The header row contains the logo, title, and the following action buttons:

| Button | Action |
|---|---|
| **◀◀** | Jump to first turn |
| **◀** | Step back one turn |
| **▶ / ⏸** | Play / Pause animation |
| **▶** | Step forward one turn |
| **▶▶** | Jump to last turn |
| Turn slider | Scrub to any turn |
| Speed | Playback FPS (frames per second) |
| **Loss** | Toggle beam-loss highlighting (red particles) |
| **Track…** | Open particle tracking configuration |
| **RF Bucket** | Open RF bucket configuration dialog |
| **Stats** | Open the stats-over-time panel |
| **Corr** | Open the correlation matrix dialog |

---

## Panel grid

The panel grid holds one or more [PlotPanel](plot_panel.md) widgets arranged
in a horizontal row. Each panel is self-contained: it has its own file
selector, axis selectors, axis-mode selector, and a lock button for Fixed mode.

Panels share the current turn number — advancing the turn slider updates all
panels simultaneously.

---

## Sidebar

The right-hand sidebar is a scrollable column of collapsible
[SidebarSection](sidebar.md) groups. Each group header is a pill-shaped toggle
button; clicking it collapses or expands the section body.

Available sections: **Files**, **Plot**, **Axis**, **Overlays**, **Export**.

---

## Status bar

The status bar at the bottom shows the current turn number, total number of
turns, particle count on the current page, and any transient status messages
(file load progress, export confirmation, etc.).
