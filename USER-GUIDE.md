# PlanMiner User Guide (v0.5.6)

Welcome to **PlanMiner**! This guide is designed to help new users get started with loading drawings, auto-calibrating color selectors, executing high-precision object counts, and exporting results.

---

## Table of Contents
1. [Overview](#1-overview)
2. [Interface Layout](#2-interface-layout)
3. [Step-by-Step Counting Workflow](#3-step-by-step-counting-workflow)
4. [Interactive Detection Adjustments & Mode Safety](#4-interactive-detection-adjustments--mode-safety)
5. [Canvas Navigation & Performance Tips](#5-canvas-navigation--performance-tips)
6. [Saving and Reusing Presets](#6-saving-and-reusing-presets)
7. [Running Batch Exports](#7-running-batch-exports)

---

## 1. Overview
PlanMiner is a standalone Windows desktop application for high-precision, color-based object counting in digital drawings (e.g., PDF blueprints, schematics, fire alarm layouts, piping schematics, or PNG/JPG/BMP images). Instead of manual counting, PlanMiner allows you to click a sample symbol on your canvas and automatically locate all matching symbols on the page.

---

## 2. Interface Layout
The application layout is divided into three key sections:
*   **Left Sidebar Panel**: Hosts drawing loading controls, page navigation, detection parameter sliders (Color Tolerance, Object Size Filters, Proximity Clustering), target previews, preset profile managers, and batch exporting triggers.
*   **Top Action Bar**: Provides view and tool navigation controls:
    *   **◀ Hide/Show Sidebar**: Toggles the visibility of the left control panel.
    *   **🔍 Box Zoom**: Activates window-select zoom. Drag a box on the canvas to zoom directly into that area.
    *   **➕ Zoom In / ➖ Zoom Out**: Fixed increment zoom adjustment.
    *   **🖐 Hand Panning**: Toggles left-drag panning mode.
    *   **↺ Fit Page to Screen**: Instantly fits the entire drawing page within your screen boundaries.
    *   **➕ Add Box / ➖ Delete Box**: Active tool modes to manually place or remove detections.
    *   **🗑 Reset**: Prompts to reset the document and all configuration settings.
    *   **About info**: Displays branding details and version information.
*   **Main Workspace Canvas**: The interactive display where you view drawings, click target objects, see live detection overlays, and edit bounding boxes.

---

## 3. Step-by-Step Counting Workflow

### Step 1: Load a Document
1. Click the **Load PDF / Image** button in the sidebar.
2. Select your drawing file (supported formats: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.bmp`).
   *   *Security & Stability Limits*: The application enforces a hard file size limit of **300MB** (with warnings starting at **200MB**). It also executes **Magic-number byte validation** (e.g., checking for `%PDF`, `\x89PNG`, `\xFF\xD8`) to ensure file extensions match actual content.
   *   *Tip for PDFs*: You can adjust the rendering DPI menu (150, 300, 450, 600) next to the load button. Choose **150 DPI** for fast loading on large files, or **300+ DPI** if your target symbols are tiny or require fine rendering detail.

### Step 2: Target a Symbol
1. Click the orange **🎯 Click to Select Target Object** button.
2. Move your cursor to the drawing canvas and click directly on the colored symbol or fixture you want to count.
3. The application will instantly:
    *   Extract the HSV color profile of your symbol.
    *   Show a zoomed preview and mask of the target in the **Selected Object Preview** window.
    *   **Auto-calibrate** the proximity clustering slider to exactly **1.25x** of the extracted symbol's physical diameter.
    *   Apply a live translucent colored mask overlay on all matching symbols across the current page.

### Step 3: Calibrate Parameter Sliders
If some matching symbols are missed or if wrong objects are highlighted, adjust the sliders in the sidebar. Dragging a slider automatically schedules a background preview update:
*   **Color Tolerance (Range Extension)**: Widens or narrows the HSV color extraction band. Drag it right if symbols are slightly different shades (due to scanning noise/gradients), or drag it left to restrict matches to a very specific color.
*   **Min Object Size Filter**: Constrains the minimum size of detected candidates relative to the target symbol. Adjust this slider to filter out smaller objects of the same color.
*   **Max Object Size Filter**: Constrains the maximum size of detected candidates relative to the target symbol. Adjust this slider to filter out larger objects of the same color.
*   **Proximity Clustering**: Controls how close separate pixels must be (in pixels) to be grouped as a single symbol. When a target is selected, this is auto-calibrated to match the physical diameter of the clicked object.

---

## 4. Interactive Detection Adjustments & Mode Safety

PlanMiner enforces **strict tool-driven click routing** to avoid accidental layout overrides:
*   **Add Box Mode**: Click the **➕ Add Box** tool icon in the top header. With this mode active, left-click anywhere on the canvas to manually insert a new detection box (highlighted in red).
*   **Delete Box Mode**: Click the **➖ Delete Box** tool icon in the top header. With this mode active, left-click on any highlighted box on the canvas to remove it (either a auto-detected box or a manually added box).
*   **Conflict Prevention**: Activating any edit mode (Add, Delete), navigation mode (Hand Pan, Box Zoom), or selection mode (🎯 Click to Select) automatically deactivates all other modes.
*   **Right-Click Protection**: Under these modes, left-click performs the selected task and right-click has no action.

---

## 5. Canvas Navigation & Performance Tips

Navigating high-resolution drawings is optimized to be fluid:
*   **Mouse Wheel Zooming**: Scroll your mouse wheel forward to zoom in on your cursor's position, or scroll backward to zoom out.
*   **Panning (Dragging)**: 
    *   *Option A*: Click and drag using your mouse's **scroll wheel button** (middle click) or **right mouse button**.
    *   *Option B*: Click the **🖐 Hand Panning** button in the top action bar to activate mouse-drag panning using the primary left-click, then drag the page around. Click it again to deactivate.
*   **Box Zoom (Zoom Window)**: Click the **Box Zoom** button (orange/yellow magnifier icon). Left-click and drag a dotted box over any region on the canvas; releasing the mouse zooms the viewport to fit that region, and the tool turns off automatically.
*   **Viewport Cropping**: For massive drawings, PlanMiner only crops and redraws the visible viewport rather than resizing the entire document. This yields a >10x rendering speed improvement.
*   **Smooth High-Quality Rendering**: High-frequency panning and zooming actions use a fast `NEAREST` neighbor resize path to maintain fluid responsiveness. Once interaction stops for **150ms**, PlanMiner automatically triggers a high-quality `LANCZOS` resampling pass for crisp rendering.

---

## 6. Page-Indexed State Persistence
*   **Per-Page Tracking**: Unlike applications that wipe manual edits when navigating, PlanMiner tracks manual additions and deletions in page-indexed dictionaries (`page_manual_added`, `page_manual_deleted_ids`).
*   **Navigation Preservation**: You can switch between pages using the navigation arrows in the sidebar, and your edits will be saved and restored as you move back and forth.
*   **Export Verification**: The batch exporter respects these manual modifications per-page, incorporating them into final counts.

---

## 7. Saving and Reusing Presets
Once you have calibrated a symbol's parameters, save them to avoid repeating the configuration:
1. Go to the **Presets** section in the sidebar.
2. Click **Save As...**, enter a descriptive name (e.g., "Red Fire Extinguisher"), and save.
3. Profiles are stored in `assets/presets/presets.json` and include **base64 serialization** for image patch preview buffers.
4. When you load a preset from the dropdown menu, both the parameter sliders and the visual target/mask previews are fully restored.

---

## 8. Running Batch Exports
To count symbols across all pages of a multi-page document:
1. Once you are satisfied with your detection parameters on the active page, click the green **Export Batch Results (All Pages)** button in the sidebar.
2. Toggle the **Legend** switch in the sidebar if needed:
    *   **Legend ON (Default)**: Exports a CSV containing the `Legend_Count` column and subtracts 1 from the raw page count to exclude the reference legend/template item.
    *   **Legend OFF**: Removes the `Legend_Count` column from the CSV summary. The total counts will reflect the raw detected objects without subtracting the reference template.
3. The progress bar will update as PlanMiner scans each page using your settings.
4. Once complete, navigate to the selected output folder:
    *   **CSV Summary**: Generates a page-by-page table containing:
        *   `Page`: The page number index.
        *   `File_Path`: The name of the annotated result file.
        *   `Detected_Object`: Counts matching components discovered automatically by the model.
        *   `Added_Object`: Counts manually placed boxes (remains blank if none were added on that page).
        *   `Legend_Count` (Only when Legend toggle is ON): Reserves `1` count if objects were found to exclude the legend template.
        *   `Total`: The calculated net sum (either `Detected_Object + Added_Object - Legend_Count` or `Detected_Object + Added_Object`).
    *   **Visual Overlays**: Annotated PDF or image pages showing outline boxes highlighting every detected object.
