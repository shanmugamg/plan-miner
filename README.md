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

Ensure you have Python 3.8+ installed. Install the dependencies using the provided requirements file:

```bash
pip install -r requirements.txt
```

To install development dependencies (for testing and code auditing):

```bash
pip install -r requirements-dev.txt
```

### Run the App

To run the application directly from the source code:

```bash
python app_gui.py
```

On Windows, the app launches maximized by default.

---

## Running Tests

To run the automated test suite:

```bash
pytest
```

To check test coverage:

```bash
pytest --cov=lib
```

---

## Building & Codesigning

The application can be compiled into a single, dependency-free `.exe` file for Windows:

```bash
python build.py
```

The compiled binary will be located in the `PlanMiner_Dist` folder:
- **Output File**: `PlanMiner_Dist/PlanMiner_v0_5_3.exe`

### Configuring Codesigning
To sign the built executable using a certificate from the Windows Certificate Store:
1. Locate or install your signing certificate (e.g., a self-signed cert for development or an enterprise cert) in the Windows Certificate Store (Current User or Local Machine).
2. Retrieve its SHA-1 thumbprint.
3. Create a `.env` file in the project root folder.
4. Set the thumbprint environment variable:
   ```text
   PLANMINER_SIGN_THUMBPRINT=your_sha1_certificate_thumbprint_here
   ```
5. Run `python build.py`. The build pipeline will automatically locate `signtool.exe` and sign the generated binary.

---

## Project Structure

```text
pixelquant/
├── assets/
│   ├── config.yaml         # Default app thresholds & branding configs
│   ├── fonts/              # Custom application fonts
│   ├── logo/               # Branding logo and window icon (logo.png, favicon.ico)
│   └── presets/            # Preset files, including presets.json
├── docs/                   # Documentation & security architecture notes
│   ├── LOGGING.md          # Logging framework & PII redaction details
│   └── SECURITY_NOTES.md   # Codesigning & file validation notes
├── tests/                  # Pytest unit tests using synthetic datasets
├── input/                  # Local folder for source documents
├── output/                 # Destination folder for batch runs & CSVs
├── app_gui.py              # Main application entry point (loads and initializes mixins)
├── build.py                # Compilation automation script
├── VERSION                 # Version control file (currently 0.5.3)
├── README.md               # Developer manual / technical setup instructions
├── USER-GUIDE.md           # Getting started manual for end-users
├── AGENT.md                # Developer / Agent handoff notes
├── pytest.ini              # Pytest configuration file
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development/Testing dependencies
└── lib/                    # Refactored modules (each file is strictly < 200 lines)
    ├── __init__.py         # Package initialization
    ├── batch_exporter.py   # Batch exporting and document scanning logic
    ├── canvas_events.py    # Canvas mouse click and interactive box overrides logic
    ├── canvas_navigation.py# Canvas zooming and panning controls
    ├── detector_engine.py  # HSV extraction and clustering algorithms (O(1) deque BFS)
    ├── dialogs.py          # Custom Tkinter dialogs (flicker-free modal transitions)
    ├── about_dialog.py     # Custom About dialog showcasing branding information
    ├── file_handler.py     # Document rendering, directory loading, and magic-number validation
    ├── layout.py           # Custom Tkinter widget arrangement and main UI skeleton
    ├── logger.py           # Structured logging utility with PII scrubbing rules
    ├── presets_manager.py  # Profile serialization and deserialization (saves/loads targets via base64)
    └── utils.py            # Helper methods (coordinate conversions, path resolution)
```


