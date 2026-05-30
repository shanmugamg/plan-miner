# PlanMiner User Guide (v0.5.6)

Welcome to **PlanMiner**! This guide is designed to help new users get started with loading drawings, auto-calibrating color selectors, executing high-precision object counts, and exporting results.

---

## Table of Contents
1. [Overview](#1-overview)
2. [Interface Layout](#2-interface-layout)
3. [Step-by-Step Counting Workflow](#3-step-by-step-counting-workflow)
4. [Interactive Detection Adjustments](#4-interactive-detection-adjustments)
5. [Canvas Navigation Tips](#5-canvas-navigation-tips)
6. [Saving and Reusing Presets](#6-saving-and-reusing-presets)
7. [Running Batch Exports](#7-running-batch-exports)

---

## 1. Overview
PlanMiner is a standalone Windows desktop application for high-precision, color-based object counting in digital drawings (e.g., PDF blueprints, schematics, fire alarm layouts, piping schematics, or PNG/JPG/BMP images). Instead of manual counting, PlanMiner allows you to click a sample symbol on your canvas and automatically locate all matching symbols on the page.

---

## 2. Interface Layout
The application layout is divided into three key sections:
*   **Left Sidebar Panel**: Hosts drawing loading controls, detection parameter sliders (Color Tolerance, Object Size Filters, Proximity Clustering), target previews, preset profile managers, and batch exporting triggers.
*   **Top Action Bar**: Provides view navigation controls (Sidebar toggle, Zoom In/Out, Fit to screen, Hand Panning toggle, Reset layout, and the About info button).
*   **Main Workspace Canvas**: The interactive display where you view drawings, click target objects, see live detection overlays, and edit bounding boxes.

---

## 3. Step-by-Step Counting Workflow

### Step 1: Load a Document
1. Click the **Load PDF / Image** button in the sidebar.
2. Select your drawing file (supported formats: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.bmp`).
   *   *Tip for PDFs*: You can adjust the rendering DPI menu (150, 300, 450, 600) next to the load button. Choose **150 DPI** for fast loading on large files, or **300+ DPI** if your target symbols are tiny or require fine rendering detail.

### Step 2: Target a Symbol
1. Click the orange **🎯 Click to Select Target Object** button.
2. Move your cursor to the drawing canvas and click directly on the colored symbol or fixture you want to count.
3. The application will instantly:
    *   Extract the HSV color profile of your symbol.
    *   Show a zoomed preview of the target in the **Selected Object Preview** window.
    *   Auto-calibrate the proximity slider to match the physical diameter of the clicked object.
    *   Apply a live translucent colored mask overlay on all matching symbols across the current page.

### Step 3: Calibrate Parameter Sliders
If some matching symbols are missed or if wrong objects are highlighted, adjust the sliders in the sidebar:
*   **Color Tolerance (Range Extension)**: Widens or narrows the HSV color extraction band. Drag it right if symbols are slightly different shades (due to scanning noise/gradients), or drag it left to restrict matches to a very specific color.
*   **Min Object Size Filter**: Constrains the minimum size of detected candidates relative to the target symbol. Adjust this slider to filter out smaller objects of the same color.
*   **Max Object Size Filter**: Constrains the maximum size of detected candidates relative to the target symbol. Adjust this slider to filter out larger objects of the same color.
*   **Proximity Clustering**: Controls how close separate pixels must be (in pixels) to be grouped as a single symbol. When a target is selected, this is auto-calibrated to match the physical diameter of the clicked object.

---

## 4. Interactive Detection Adjustments
Even with perfect calibration, text overlays or noisy scans may cause minor detection discrepancies. PlanMiner lets you modify results directly on the canvas using toolbar modes:

*   **Add Box Mode**: Click the green Add tool icon in the top header. With this mode active, left-click anywhere on the canvas to manually insert a new detection box (highlighted in red).
*   **Delete Box Mode**: Click the red Delete tool icon in the top header. With this mode active, left-click on any highlighted box on the canvas to remove it.
*   *Note*: The current count label updates dynamically. Under these modes, left-click performs the selected task and right-click has no action.

---

## 5. Canvas Navigation Tips
Navigating high-resolution drawings is optimized to be fluid:
*   **Zooming**: Scroll your mouse wheel forward to zoom in on your cursor's position, or scroll backward to zoom out.
*   **Panning (Dragging)**: 
    *   *Option A*: Click and drag using your mouse's **scroll wheel button** (middle click) or **right mouse button**.
    *   *Option B*: Click the **🖐 Pan** button in the top action bar to activate mouse-drag panning using the primary left-click, then drag the page around. Click it again to deactivate.
*   **Fit Page**: Click the **↺ Fit** button in the top action bar to instantly fit the entire drawing page within your screen boundaries.

---

## 6. Saving and Reusing Presets
Once you have calibrated a symbol's parameters, save them to avoid repeating the configuration:
1. Go to the **Presets** section in the sidebar.
2. Enter a descriptive name (e.g., "Red Fire Extinguisher") and click **Save Preset**.
3. The preset will be added to the drop-down menu, storing the sliders and a visual image preview of the target.
4. Next time you open a drawing, select your preset from the dropdown menu to apply the configuration instantly.

---

## 7. Running Batch Exports
To count symbols across all pages of a multi-page document:
1. Once you are satisfied with your detection parameters on the active page, click the green **Batch Scan & Export** button in the sidebar.
2. Under the export button, toggle the **Legend** switch:
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
