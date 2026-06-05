# Installation

## Requirements

RanDistViewer requires Python 3.10 or later. The following packages are needed:

| Package | Minimum version | Role |
|---|---|---|
| `PySide6` | 6.5.0 | GUI framework |
| `matplotlib` | 3.7.0 | Plot rendering, blit animation |
| `numpy` | 1.24.0 | Numerical computation |
| `scipy` | 1.10.0 | Gaussian smoothing, statistics |
| `plotly` | 5.14.0 | HTML export |

---

## Install dependencies

```bash
pip install PySide6 matplotlib numpy scipy plotly
```

Or if you use conda/miniforge:

```bash
conda install -c conda-forge pyside6 matplotlib numpy scipy plotly
```

---

## Clone the repository

```bash
git clone https://github.com/randy-afk/RanDistViewer.git
cd RanDistViewer
```

---

## Launch

```bash
python main.py
```

The main window opens immediately. No additional configuration is required.

---

## Platform notes

RanDistViewer is developed and tested on **Linux (Ubuntu)**. PySide6 and
Matplotlib are cross-platform, so macOS and Windows should work, but are not
actively tested.

!!! tip "Qt backend"
    `main.py` sets `QT_API=pyside6` and `matplotlib.use("QtAgg")` before any
    other imports, so the correct backend is selected automatically. Do not
    override these environment variables.
