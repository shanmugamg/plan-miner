# PlanMiner User Guide (v0.5.3)

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
*   **Left Sidebar Panel**: Hosts drawing loading controls, detection parameter sliders (Tolerance, Proximity, Size Scales), target previews, preset profile managers, and batch exporting triggers.
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
*   **Color Tolerance**: Widens or narrows the HSV color extraction band. Drag it right if symbols are slightly different shades (due to scanning noise/gradients), or drag it left to restrict matches to a very specific color.
*   **Min / Max Area Scale**: Constrains the size of detected candidates relative to the target symbol. If larger or smaller objects of the same color are showing up as matches, adjust these sliders to filter them out.
*   **Proximity Cluster**: Controls how close separate pixels must be to be grouped as a single symbol. (This defaults to 1.25x the target's physical size, which is optimal for most drawings).

---

## 4. Interactive Detection Adjustments
Even with perfect calibration, text overlays or noisy scans may cause minor detection discrepancies. PlanMiner lets you modify results directly on the canvas:

*   **Remove False Positives (Left-Click)**: Simply left-click on any highlighted detection box to delete it from the current count.
*   **Insert Missing Symbols (Right-Click)**: If a symbol was missed (e.g., it is obscured by lines or text), right-click directly on the symbol's center in the canvas to manually insert a new detection box.
*   *Note*: The current count label on the screen updates dynamically to reflect your manual overrides.

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
Once you have calibrated a symbol's color tolerance and area scales, save them to avoid repeating the configuration:
1. Go to the **Presets** section in the sidebar.
2. Enter a descriptive name (e.g., "Red Fire Extinguisher") and click **Save Preset**.
3. The preset will be added to the drop-down menu, storing the sliders and a visual image preview of the target.
4. Next time you open a drawing, select your preset from the dropdown menu to apply the configuration instantly.

---

## 7. Running Batch Exports
To count symbols across all pages of a multi-page document:
1. Once you are satisfied with your detection parameters on the active page, click the green **Batch Scan & Export** button in the sidebar.
2. The progress bar will update as PlanMiner scans each page using your settings.
3. Once complete, navigate to the `output/` folder located in the project directory:
    *   **CSV Summary**: Contains page-by-page and total counts, complete with symbol coordinates and areas.
    *   **Visual Overlays**: Annotated PDF or image pages showing red outline boxes highlighting every detected object.
