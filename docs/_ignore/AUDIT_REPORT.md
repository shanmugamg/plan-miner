# PlanMiner Code Audit Report

Date: 2026-05-29
Scope: Security, Performance, Enterprise Compliance, 10x Improvement Plan

Files reviewed:
- app_gui.py
- lib/detector_engine.py
- lib/file_handler.py
- lib/canvas_navigation.py
- lib/canvas_events.py
- lib/batch_exporter.py
- lib/presets_manager.py
- lib/dialogs.py
- lib/about_dialog.py
- lib/utils.py
- build.py
- assets/config.yaml
- assets/presets/presets.json

---

## Security Audit

### Critical
1) Hardcoded code-signing password
- Location: build.py:49
- Evidence:
  pfx_pass = "GeoICON2026!"
- Risk: credential exposure, signing key compromise, supply-chain integrity loss.
- Recommendation: pull password from environment or secret store; rotate key.

### High
1) Untrusted file input handling without validation/sandboxing
- Location: lib/file_handler.py:10-91
- Risk: parser vulnerabilities in PDF/image stacks; denial of service.
- Recommendation: validate size/type, consider sandboxed parsing.

### Medium
1) Preset file integrity not enforced
- Location: lib/presets_manager.py:10-56
- Risk: tampering can alter detection parameters or inject malformed data.
- Recommendation: schema validation and checksum/HMAC.

2) PyInstaller hardening gaps
- Location: build.py
- Risk: easy unpacking, no runtime integrity checks.
- Recommendation: signed builds with secure key handling; optional runtime hash check.

### Low
1) Ad-hoc console logging
- Locations: app_gui.py:147-149, lib/presets_manager.py:38, lib/about_dialog.py:62
- Risk: inconsistent error handling and possible leakage in logs.
- Recommendation: structured logger with redaction controls.

### Not applicable
- Authentication/authorization: none present.
- Network communications: none detected.

---

## Performance Audit

### High
1) Full redraw and resize on every zoom/pan
- Location: lib/canvas_navigation.py:104-136
- Impact: high CPU and memory churn on large images.
- Recommendation: reuse canvas image item; avoid recreate on pan-only operations.

2) Live preview recomputes detection mask on every redraw
- Location: lib/canvas_navigation.py:114-129
- Impact: repeated full-frame processing causes latency.
- Recommendation: compute mask on parameter change; cache for redraw.

3) O(n^2) proximity clustering
- Location: lib/detector_engine.py:127-139
- Impact: slow scaling with large numbers of detections.
- Recommendation: spatial grid or KD-tree clustering.

### Medium
1) Batch export runs on UI thread
- Location: lib/batch_exporter.py:57-140
- Impact: UI stalls, reduced responsiveness.
- Recommendation: move to worker thread; update UI via after().

2) Full-resolution caching only
- Location: lib/file_handler.py:85-94
- Impact: memory growth with many pages.
- Recommendation: multi-resolution cache and eviction policy.

### Low
1) Redraw on every resize event
- Location: lib/layout.py:330
- Impact: excessive redraws during window resize.
- Recommendation: debounce redraw calls.

---

## Enterprise Compliance Review

### Gaps
- No audit logging or event trail (file load, presets, export).
- No data retention policy for presets/output.
- No dependency pinning or SBOM generation.
- No secure update mechanism or verification of updates.
- Minimal security documentation and hardening guidance.

### Partial
- User-facing error dialogs exist but no centralized logging.

---

## 10x Performance Improvement Plan

### Page/interface loading times
1) Render low-DPI preview first, then replace with high-DPI async.
2) Cache rendered pixmaps per DPI level (150/300/600).
3) Lazy-load pages only when viewed.

### Navigation responsiveness between views
1) Keep a single canvas image item; update via itemconfig.
2) Use canvas.move for panning; avoid image rescale on pan.
3) Cache PIL/NumPy conversions for nearby zoom steps.

### Zoom functionality smoothness and speed
1) Multi-resolution image pyramid and nearest cached scale.
2) Throttle mouse-wheel zoom events (16-32ms debounce).
3) Use cv2.resize on NumPy arrays and convert once per frame.

### Real-time detection latency
1) Move detection to background thread with cached results.
2) Spatial indexing for clustering; avoid O(n^2).
3) Run preview on downsampled image; full res for final run.

---

## Prioritized Recommendations

1) Remove hardcoded signing password; migrate to secrets and rotate key.
2) Cache detection masks and decouple redraw from detection.
3) Replace O(n^2) clustering with spatial indexing.
4) Add structured logging and audit events.
5) Document secure distribution and update verification.
6) Pin dependencies and add SBOM/vulnerability scanning.

---

## Example Before/After Snippets

### Hardcoded signing password
Before (build.py:49):
```python
pfx_pass = "GeoICON2026!"
```
After:
```python
pfx_pass = os.environ.get("PLANMINER_PFX_PASS")
if not pfx_pass:
    log_warn("PFX password missing; skipping signing.")
    return
```

### Live preview caching
Before (lib/canvas_navigation.py:114-122):
```python
if self.switch_live_preview.get() and self.template_info is not None:
    img_bgr = self.doc_pages[self.current_page_idx]
    _, mask = ColorDetectorEngine.detect_objects(...)
```
After (concept):
```python
# on_param_changed: compute once and store self.live_mask
# redraw: reuse cached mask
```
