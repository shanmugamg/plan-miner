# Agent Notes & Implementation Details (v0.5.3)

This document contains key engineering notes, architectural details, layout adjustments, and multi-monitor DPI findings for developers and agents working on the **PlanMiner** project.

---

## Technical Architecture

In version 0.5.3, the codebase has been fully refactored into a highly modular, mixin-based architecture. To maintain exceptional readability and ease of maintenance, the project strives to keep code files concise and under 200 lines where possible.

### 1. Main Entrypoint: `app_gui.py`
- Inherits from multiple mixins in the `lib` package to construct the full application state, canvas controls, and event handler loops while keeping the `self` context fully cohesive.
- Handles initialization, theme configuration (from `assets/config.yaml`), and main Tkinter runtime loop.
- App starts maximized via a deferred `self.state("zoomed")` callback to ensure it reliably applies after the window is fully mapped, matching large-document workflows.
- Structured logging is initialized to `logs/planminer.log` for audit-friendly event tracking.

### 2. Modular Mixin Package (`lib/`)
- [layout.py](file:///d:/python-projects/raghu-software/pixelquant/lib/layout.py): Builds the UI sidebar, frames, sliders, buttons, canvas setup, and premium styling tokens. Fixes button icon spacing by removing emoji variations (like `\uFE0F`).
- [file_handler.py](file:///d:/python-projects/raghu-software/pixelquant/lib/file_handler.py): Manages document loading (PDF, PNG, JPG, BMP), page-rendering resolution calibrations via PyMuPDF, and navigation state.
  - Implements **Magic-number byte validation** for PDF (`%PDF`), PNG (`\x89PNG`), and JPG/JPEG (`\xFF\xD8`) to prevent extension-spoofing attacks.
  - Enforces hard file size limits (300MB max limit, 200MB warning threshold) to preserve system stability.
  - Sanitizes log filenames by hashing them using SHA-256 (`doc_<hash>.<ext>`) to prevent PII exposure.
- [canvas_navigation.py](file:///d:/python-projects/raghu-software/pixelquant/lib/canvas_navigation.py): Implements high-performance panning and mouse-wheel zooming routines (using canvas coordinates shifting to avoid scaling lag).
  - Uses explicit Viewport Cropping. Redraws only the visible coordinates bound to the viewport canvas rather than resizing the entire image dynamically. This leads to a >10x rendering speed improvement when zooming into high resolution images.
- [canvas_events.py](file:///d:/python-projects/raghu-software/pixelquant/lib/canvas_events.py): Manages click-to-target color sampling, boundary adjustments, and user override interactions (left-click delete box, right-click insert box).
  - Live preview masks are cached and recomputed only on parameter changes.
- [presets_manager.py](file:///d:/python-projects/raghu-software/pixelquant/lib/presets_manager.py): Handles profile serialization and saves profiles into `assets/presets/presets.json`. Includes **base64 serialization** for image patch preview buffers to visually recover target selections upon preset load.
- [batch_exporter.py](file:///d:/python-projects/raghu-software/pixelquant/lib/batch_exporter.py): Orchestrates scanning and detection across all document pages, generating a summary CSV alongside visual overlays outputted to the `output/` directory.
  - Implements a sliding window memory approach via explicit `doc_pages[idx] = None` caching limits and forces `gc.collect()` to resolve critical Out-Of-Memory (OOM) memory leak vulnerabilities for large PDF documents.
- [detector_engine.py](file:///d:/python-projects/raghu-software/pixelquant/lib/detector_engine.py): Hosts OpenCV-based processing code. Performs HSV extraction, contour extraction, bounding box calculations, and proximity-based clustering (merging close targets).
  - **Performance Optimization**: Proximity clustering uses `collections.deque.popleft()` for BFS queue operations, guaranteeing O(1) queue popping complexity compared to standard list `pop(0)` operations.
  - Proximity clustering strictly uses a Python Breadth-First Search (BFS) combined with grid buckets for scaling vs. O(n^2) adjacency checks. OpenCV Morphological closing operations are strictly avoided due to their propensity to distort geometry boundaries which break the aspect-ratio sanity checks.
- [dialogs.py](file:///d:/python-projects/raghu-software/pixelquant/lib/dialogs.py): Houses customtkinter modal screens, including custom themed message boxes and centered input prompts.
  - **UI/UX Optimization**: Mitigates CustomTkinter modal flicker on Windows by mapping the window with `alpha=0.0` and scaling transparency smoothly up to `1.0` during display updates.
- [about_dialog.py](file:///d:/python-projects/raghu-software/pixelquant/lib/about_dialog.py): Contains the custom themed application About Dialog featuring branding details and license terms.
- [logger.py](file:///d:/python-projects/raghu-software/pixelquant/lib/logger.py): Structured application logger.
  - In compiled PyInstaller builds (`sys.frozen`), writes logs using a `RotatingFileHandler` (max size 5MB, up to 2 backups).
  - Employs a custom `RedactingFilter` to identify and scrub Windows username path patterns (e.g. `C:\Users\username\`) replacing them with `C:\Users\<REDACTED>\` to secure customer PII.
- [utils.py](file:///d:/python-projects/raghu-software/pixelquant/lib/utils.py): Provides helper utilities for coordinate mapping and DPI-safe path resolution.
  - Dialog icon handling retries icon application (iconbitmap + iconphoto) to override CustomTkinter defaults.

### 3. Platform Support Matrix
- **Supported OS**: Windows 10/11 (due to UI/DPI integration, specific `ctypes` hooks, and Codesign execution paths).
- **Unsupported OS**: macOS, Linux. (The headless detection logic may function, but the GUI and build script are Windows-specific).

---

## Layout & Cosmetic Adjustments

1. **Sidebar Width & Layout Constraints**:
   - Sidebar width is fixed at `280px` (reduced from `340px`).
   - Root column weights are locked (`0` for sidebar, `1` for canvas) so that window expansions only size the main viewer.
   - Text items are wrapped (`wraplength` constraints on `lbl_status` and `lbl_file_info`) to prevent long text from stretching the sidebar horizontally.
   - Redundant 4-directional arrow pan buttons were removed in favor of the active mouse-drag tool.

2. **DPI-Aware Text Background Box Sizing**:
   - Fixed text background boxes (`25px` / `35px` widths) were replaced with a dynamic formula: `len(text) * 8 + 10` on the Tkinter canvas and `cv2.getTextSize` in OpenCV outputs.
   - This ensures labels like `#30` or `+#10` never overflow their colored borders, keeping the font background completely visible on all monitor configurations.

3. **Branding & Dialog Boxes**:
    - Generic standard Python modal warning and dialog boxes are overridden with dark-themed customtkinter components.
    - Redundant elements (such as company details in the sidebar footer) were purged to streamline vertical space.
    - Sidebar title uses smaller app font and shows version as a subdued label.

---

## Testing Framework

To replace fragile ad-hoc testing, PlanMiner uses a standard `pytest` testing suite:
- Configured in [pytest.ini](file:///d:/python-projects/raghu-software/pixelquant/pytest.ini).
- Tests are contained under [tests/](file:///d:/python-projects/raghu-software/pixelquant/tests/).
- Leverages synthetic image arrays generated via `numpy` to test color detection boundaries, layout parsing, and clustering accuracy without checking in bulky PDF assets.
- Dependency verification checks via `bandit` and `safety` integrated into dev tooling (`requirements-dev.txt`).

---

## Lessons Learned & Best Practices

- **Avoid Per-Monitor DPI Awareness Level 2**: While Level 2 is technically the most granular, dragging a Tkinter canvas across mixed-resolution displays causes standard Python hooks to hang or lock threads during `WM_DPICHANGED` messages. System-level scaling (Level 1) handles bitmap scaling seamlessly.
- **Canvas Panning & Zoom Performance**: Resizing or redrawing images during high-frequency panning events introduces significant lag. We shift objects using a Viewport Cropping mechanism combined with a fast `NEAREST` resize path during interactions and schedule `LANCZOS` high-quality resamples after short 150ms idle windows.
- **Handling Closing Events**: Reassigned `WM_DELETE_WINDOW` to a unified prompt that ensures the application explicitly asks for closing confirmation.
- **Enterprise Security Overrides**: Log files are sanitized with SHA-256 hashes of input filenames to comply with PII data exposure laws.
- **Proximity Slider Auto-Calibration**: Because proximity clustering is highly sensitive to object size, clicking a target symbol auto-calibrates the proximity slider value to exactly `1.25x` of the extracted symbol's diameter.
- **Visual Presets Recovery**: When storing custom templates inside presets, we serialize both the target patch and the target mask as base64-encoded PNG strings. When the preset is loaded, these are decoded and restored to display in the Selected Object Preview frame.
- **Page-Indexed State Persistence**: To prevent manual overrides from resetting when users change pages, state is tracked in page-indexed dictionaries (`page_manual_added`, `page_manual_deleted_ids`, `page_detections`) rather than flat lists. Navigating pages preserves these edits, and the batch exporter processes them per-page.
- **Legend & Added Objects CSV Columns**: Built a configurable `Legend` toggle switch and maintained default values via `config.yaml`. The CSV export aligns columns strictly to `Page, File_Path, Detected_Object, Added_Object, Legend_Count, Total`.

