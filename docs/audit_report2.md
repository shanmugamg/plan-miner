# Enterprise Code Audit Report: PixelQuant

**Auditor:** Senior Software Code Auditor  
**Date:** May 29, 2026  
**Target:** PixelQuant (Python Object Detection Software)  
**Scope:** Architecture, Security, Performance, ML Pipeline  

## Executive Summary
This audit evaluated the PixelQuant codebase against enterprise-grade security, performance, and maintainability standards. The application establishes a solid foundation for color-based object detection using OpenCV and PyMuPDF. However, the audit revealed several critical vulnerabilities concerning memory management and clustering algorithms that fundamentally degrade scalability and performance on large files. Addressing the findings below, particularly the OOM risks and algorithmic bottlenecks, is imperative for production readiness.

---

## 1. Critical Severity

### 1.1 Memory Leak via Uncompressed Image Caching
*   **Location:** `lib/file_handler.py`, Lines 111-122
*   **Finding:** Every page of a loaded PDF is rendered into an uncompressed OpenCV BGR numpy array and permanently cached in the `self.doc_pages` list. For large PDFs, this caches gigabytes of uncompressed data into RAM, leading to immediate Out-Of-Memory (OOM) crashes.
    ```python
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 3)
    img_bgr = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
    ...
    self.doc_pages[index] = img_bgr
    ```
*   **Recommendation:** Implement a sliding window cache (e.g., retaining only the current, previous, and next pages). Release uncompressed arrays to the garbage collector (`self.doc_pages[idx] = None`) immediately after a page is no longer in view.

---

## 2. High Severity

### 2.1 Algorithmic Inefficiency in Object Detection Clustering
*   **Location:** `lib/detector_engine.py`, Lines 188-219
*   **Finding:** The spatial proximity grouping algorithm iterates over connected components using a custom Python Breadth-First Search (BFS) and manual Euclidean distance calculations. For images with noise, this `O(V^2 + E)` pure Python loop blocks the processing thread significantly.
    ```python
    visited = set()
    clusters = []
    for node in candidate_indices:
        if node not in visited:
            cluster = []
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop(0)
    ```
*   **Recommendation:** Offload spatial clustering to the OpenCV C++ backend. Utilize morphological operations (e.g., `cv2.dilate` or `cv2.morphologyEx`) before executing `connectedComponentsWithStats` to merge nearby blobs natively.

### 2.2 Insecure File & Credential Handling
*   **Location:** `build.py` (Referenced)
*   **Finding:** The build script securely retrieves the code-signing password via the `PLANMINER_PFX_PASS` environment variable, but invokes `signtool.exe` using `subprocess.run()`. Passing passwords as command-line arguments can expose them to process monitors during the build lifecycle.
*   **Recommendation:** Use secure secret-injection mechanisms or Azure Key Vault / AWS KMS for CI/CD signing, bypassing CLI-based password arguments.

---

## 3. Medium Severity

### 3.1 GUI Rendering & Zooming Bottleneck
*   **Location:** `lib/canvas_navigation.py` (Referenced)
*   **Finding:** The entire source image is resized dynamically upon every pan and zoom event. Resizing massive images on the UI thread for every pixel of mouse drag causes extreme UI stuttering and unresponsiveness.
*   **Recommendation:** Utilize Viewport Cropping. Calculate the bounding box of the canvas view, crop only that specific region from the original PIL image, and scale/render only the crop.

### 3.2 Data Retention & Local Storage Exposure
*   **Location:** `lib/batch_exporter.py` / `lib/presets_manager.py` (Referenced)
*   **Finding:** The application processes potentially sensitive documents and exports outputs to a local, unencrypted `output/` directory. Presets are saved locally as Base64 strings without an explicit data retention or cleanup policy.
*   **Recommendation:** Implement an auto-cleanup procedure for temporary processing files. Ensure output locations prompt the user rather than defaulting to the installation directory. 

---

## 4. Low / Informational Severity

### 4.1 Unsanitized Logging
*   **Location:** `lib/file_handler.py`, Line 39
*   **Finding:** While there is a hashing mechanism present (`safe_name_hash`), older logging statements or error logs might still inadvertently leak PII if not consistently applied across all exception handlers.
*   **Recommendation:** Ensure all filenames are scrubbed or hashed before logging. Only log file extensions, sizes, and anonymized identifiers.

### 4.2 PDF Parsing Vulnerabilities
*   **Location:** `lib/file_handler.py`, Line 54
*   **Finding:** `fitz.open()` (PyMuPDF) is used directly on user-provided files. Maliciously crafted PDFs can crash the parsing thread.
*   **Recommendation:** Enforce strict file size limits and parser timeouts. Ensure PyMuPDF is running with secure flags that disable embedded scripting/actions.
