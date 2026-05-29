# PlanMiner - Standalone Color Object Counter

PlanMiner is a standalone Windows desktop application built with **CustomTkinter** for high-precision, color-based object counting in large digital drawings (such as PDF schematics, fixtures, fire alarms, etc.).

## Key Features

- **Direct Interactive Color Targeting**: Click on any symbol/fixture in the drawing canvas to automatically extract HSV properties and auto-calibrate settings.
- **Smooth Navigation & Panning**: Integrates a custom Viewport Cropping algorithm natively allowing flawless panning and zooming of heavy PDF/image files (e.g. 15-25MB) using instantaneous rendering with a dynamic memory cache resolving OOM leaks.
- **Responsive Zooming**: Viewport Cropping computes fast preview scaling with deferred high-quality resampling keeping zoom controls entirely lag-free.
- **Live Mask Overlay**: Real-time translucent overlay showing selected colors directly on the canvas as you adjust sliders.
- **Interactive Box Overrides**: 
  - Left-click on a box to delete false positives.
  - Right-click on the canvas to manually place new detection boxes.
- **DPI-Aware PDF Rendering**: Directly renders PDF pages at customizable resolutions (150, 300, 450, 600 DPI) using **PyMuPDF** (no external Poppler dependencies required).
- **Settings Profiles**: Save settings and HSV boundary calibrations as profiles/presets (saved in `assets/presets/presets.json` with base64-encoded visual target previews) to reuse them across files.
- **Batch Exporting**: Scans all pages of a loaded document and exports a summary CSV alongside highlighted, annotated drawings to the `output` directory.
- **Premium About Dialog**: Features branding logo, license terms, and copyright validation under a unified CustomTkinter modal theme.

---

## Installation & Running

### Requirements

Ensure you have Python 3.8+ installed. Install the dependencies using:

```bash
pip install customtkinter opencv-python PyMuPDF numpy Pillow pyyaml
```

### Run the App

To run the application directly from the source code:

```bash
python app_gui.py
```

On Windows, the app launches maximized by default.

---

## Building Standalone Executable

The application can be compiled into a single, dependency-free `.exe` file for Windows:

```bash
python build.py
```

The compiled binary will be located in the `dist` folder:
- **Output File**: `dist/PlanMiner.exe`

---

## Project Structure

```text
planminer/
├── assets/
│   ├── config.yaml         # Default app thresholds & branding configs
│   ├── fonts/              # Custom application fonts
│   ├── logo/               # Branding logo and window icon (logo.png, favicon.ico)
│   └── presets/            # Preset files, including presets.json
├── input/                  # Local folder for source documents
├── output/                 # Destination folder for batch runs & CSVs
├── app_gui.py              # Main application entry point (loads and initializes mixins)
├── build.py                # Compilation automation script
├── VERSION                 # Version control file (currently 0.3.0)
├── spec.md                 # Technical specification document
├── README.md               # User manual / instructions
├── AGENT.md                # Developer / Agent handoff notes
└── lib/                    # Refactored modules (each file is strictly < 200 lines)
    ├── __init__.py         # Package initialization
    ├── batch_exporter.py   # Batch exporting and document scanning logic
    ├── canvas_events.py    # Canvas mouse click and interactive box overrides logic
    ├── canvas_navigation.py# Canvas zooming and panning controls
    ├── detector_engine.py  # HSV extraction and clustering algorithms
    ├── dialogs.py          # Custom Tkinter dialogs (message dialogs, input dialogs)
    ├── about_dialog.py     # Custom About dialog showcasing branding information
    ├── file_handler.py     # Document rendering, directory loading, and management logic
    ├── layout.py           # Custom Tkinter widget arrangement and main UI skeleton
    ├── presets_manager.py  # Profile serialization and deserialization (saves/loads targets via base64)
    └── utils.py            # Helper methods (coordinate conversions, path resolution, dialog icon retries)
```


