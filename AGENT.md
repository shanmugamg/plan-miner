# Agent Notes & Implementation Details (v0.3.0)

This document contains key engineering notes, architectural details, layout adjustments, and multi-monitor DPI findings for developers and agents working on the **PlanMiner** project.

---

## Technical Architecture

In version 0.3.0, the codebase has been fully refactored into a highly modular, mixin-based architecture. To maintain exceptional readability and ease of maintenance, **no code file in the repository exceeds 200 lines**.

### 1. Main Entrypoint: `app_gui.py`
- Inherits from multiple mixins in the `lib` package to construct the full application state, canvas controls, and event handler loops while keeping the `self` context fully cohesive.
- Handles initialization, theme configuration (from `assets/config.yaml`), and main Tkinter runtime loop.
- App starts maximized via a deferred `self.state("zoomed")` callback to ensure it reliably applies after the window is fully mapped, matching large-document workflows.
- Structured logging is initialized to `logs/planminer.log` for audit-friendly event tracking.

### 2. Modular Mixin Package (`lib/`)
- [layout.py](file:///d:/python-projects/raghu-software/planminer/lib/layout.py): Builds the UI sidebar, frames, sliders, buttons, canvas setup, and premium styling tokens.
- [file_handler.py](file:///d:/python-projects/raghu-software/planminer/lib/file_handler.py): Manages document loading (PDF, PNG, JPG), page-rendering resolution calibrations via PyMuPDF, and navigation state.
- [canvas_navigation.py](file:///d:/python-projects/raghu-software/planminer/lib/canvas_navigation.py): Implements high-performance panning and mouse-wheel zooming routines (using canvas coordinates shifting to avoid scaling lag).
- Uses explicit Viewport Cropping. Redraws only the visible coordinates bound to the viewport canvas rather than resizing the entire image dynamically. This leads to a >10x rendering speed improvement when zooming into high resolution images.
- [canvas_events.py](file:///d:/python-projects/raghu-software/planminer/lib/canvas_events.py): Manages click-to-target color sampling, boundary adjustments, and user override interactions (left-click delete box, right-click insert box).
- Live preview masks are cached and recomputed only on parameter changes.
- [presets_manager.py](file:///d:/python-projects/raghu-software/planminer/lib/presets_manager.py): Handles profile serialization and saves profiles into `assets/presets/presets.json`. Includes **base64 serialization** for image patch preview buffers to visually recover target selections upon preset load.
- [batch_exporter.py](file:///d:/python-projects/raghu-software/planminer/lib/batch_exporter.py): Orchestrates scanning and detection across all document pages, generating a summary CSV alongside visual overlays outputted to the `output/` directory.
- Implements a sliding window memory approach via explicit `doc_pages[idx] = None` caching limits and forces `gc.collect()` to resolve critical Out-Of-Memory (OOM) memory leak vulnerabilities for large PDF documents.
- [detector_engine.py](file:///d:/python-projects/raghu-software/planminer/lib/detector_engine.py): Hosts OpenCV-based processing code. Performs HSV extraction, contour extraction, bounding box calculations, and proximity-based clustering (merging close targets).
- Proximity clustering strictly uses a Python Breadth-First Search (BFS) combined with grid buckets for scaling vs. O(n^2) adjacency checks. Open-CV Morphological closing operations are strictly avoided due to their propensity to distort geometry boundaries which break the aspect-ratio sanity checks.
- [dialogs.py](file:///d:/python-projects/raghu-software/planminer/lib/dialogs.py): Houses customtkinter modal screens, including custom themed message boxes and centered input prompts.
- [about_dialog.py](file:///d:/python-projects/raghu-software/planminer/lib/about_dialog.py): Contains the custom themed application About Dialog featuring branding details and license terms.
- [utils.py](file:///d:/python-projects/raghu-software/planminer/lib/utils.py): Provides helper utilities for coordinate mapping and DPI-safe path resolution.
- Dialog icon handling retries icon application (iconbitmap + iconphoto) to override CustomTkinter defaults.

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

## Lessons Learned & Best Practices

- **Avoid Per-Monitor DPI Awareness Level 2**: While Level 2 is technically the most granular, dragging a Tkinter canvas across mixed-resolution displays causes standard Python hooks to hang or lock threads during `WM_DPICHANGED` messages. System-level scaling (Level 1) handles bitmap scaling seamlessly.
- **Canvas Panning & Zoom Performance**: Resizing or redrawing images during high-frequency panning events introduces significant lag. We shift objects using a Viewport Cropping mechanism combined with a fast `NEAREST` resize path during interactions and schedule `LANCZOS` high-quality resamples after short 150ms idle windows.
- **Handling Closing Events**: Reassigned `WM_DELETE_WINDOW` to a unified prompt that ensures the application explicitly asks for closing confirmation.
- **Enterprise Security Overrides**: Log files are sanitized with SHA-256 hashes of input filenames to comply with PII data exposure laws.
- **Proximity Slider Auto-Calibration**: Because proximity clustering is highly sensitive to object size, clicking a target symbol auto-calibrates the proximity slider value to exactly `1.25x` of the extracted symbol's diameter.
- **Visual Presets Recovery**: When storing custom templates inside presets, we serialize both the target patch and the target mask as base64-encoded PNG strings. When the preset is loaded, these are decoded and restored to display in the Selected Object Preview frame.
