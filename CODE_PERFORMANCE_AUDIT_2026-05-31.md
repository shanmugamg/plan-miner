# Code + Performance Audit Report (Post-Fix)

Date: 2026-05-31  
Project: `pixelquant` / PlanMiner  
Scope: refreshed code audit + performance audit after recent fixes

## Executive Summary
- Overall quality has improved significantly: test layout exists (`tests/` + `pytest.ini`), CI workflow exists, password-based signing path was removed, and detector BFS queue was optimized with `deque`.
- Current risk posture is now **Medium** (previously higher), with remaining issues mostly around runtime resilience, minor logic hygiene, and UI/performance hot paths.
- Core detection pipeline remains practical and performant for this app class, but a few paths still do avoidable work on the UI thread and force frequent garbage collection.

## Validation Performed
- `python -m pytest -q` -> **8 passed**.
- `python -m pytest --cov=lib --cov=app_gui tests -q` -> failed because `pytest-cov` is not installed in current environment.
- `python -m bandit -r lib app_gui.py build.py -f txt` -> tool not installed in current environment.
- `python -m safety check -r requirements.txt --full-report` -> tool not installed in current environment.

## Findings by Severity

### High

1) Broad exception handling still masks runtime failures in security/time-validation path
- Files: `lib/date_check.py:26`, `lib/date_check.py:36`, `lib/date_check.py:50`, `lib/date_check.py:61`
- Evidence:
```python
except Exception:
    continue
```
and
```python
except Exception:
    pass
```
- Why this matters: license validity logic silently falls back when external time parsing/network checks fail, making root-cause diagnosis difficult and potentially weakening anti-tamper guarantees.
- Recommendation: catch expected exceptions (`requests.RequestException`, `ValueError`, decoding errors), log structured reasons, and track fallback reason in status telemetry.

2) Build script imports `.env` directly into process environment
- File: `build.py:7-15`
- Evidence:
```python
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        ...
        os.environ[key.strip()] = val.strip().strip('"').strip("'")
```
- Why this matters: convenient for local builds, but in enterprise environments this can accidentally elevate local unmanaged secrets over CI-managed secrets.
- Recommendation: gate local `.env` loading behind explicit dev flag, and prefer CI secret provider precedence.

### Medium

1) Forced full-list scan + `gc.collect()` on each page navigation can add UI jitter
- File: `lib/file_handler.py:77-83`
- Evidence:
```python
for i in range(self.total_pages):
    if i != index and self.doc_pages[i] is not None:
        self.doc_pages[i] = None
import gc
gc.collect()
```
- Impact: O(total_pages) sweep + explicit GC on each navigation can cause stutter on large documents.
- Recommendation: use bounded LRU/sliding window (current/adjacent pages) and avoid explicit `gc.collect()` on every navigation.

2) Live preview detection still executes synchronously on UI interaction path
- Files: `lib/canvas_events.py:329-336`, `lib/canvas_events.py:275-278`
- Evidence:
```python
_, mask = ColorDetectorEngine.detect_objects(...)
```
- Impact: slider adjustments and live preview can block UI on high DPI pages.
- Recommendation: dispatch preview computation to worker thread and publish result via `after()`; cancel stale preview jobs when parameters change quickly.

3) Progress window still has two-step geometry set (show then reposition)
- File: `lib/batch_exporter.py:50`, `lib/batch_exporter.py:63`
- Evidence:
```python
progress_win.geometry("400x150")
...
progress_win.geometry(f"+{x}+{y}")
```
- Impact: can produce minor visual jump/flicker, similar to previous dialog lifecycle issue.
- Recommendation: set final geometry in one call (`"{w}x{h}+{x}+{y}"`) before deiconify.

4) Reset path still contains one bare `except`
- File: `lib/file_handler.py:226`
- Evidence:
```python
except:
    pass
```
- Impact: hides cleanup failures and complicates support diagnostics.
- Recommendation: use explicit exception and log warning.

5) Coverage is configured in CI but not enforceable in this environment
- Files: `.github/workflows/main.yml:34`, `requirements-dev.txt:2`
- Observation: local run failed because `pytest-cov` is not installed in active environment.
- Recommendation: ensure developer onboarding script installs dev requirements and add minimum coverage threshold in CI (e.g., `--cov-fail-under=80`).

### Low

1) Minor duplicate tooltip binding
- File: `lib/layout.py:335`, `lib/layout.py:352`
- Impact: no major bug, but redundant code indicates minor UI wiring drift.
- Recommendation: remove duplicate call.

2) Documentation inconsistency in versions
- Files: `README.md:75` (0.5.3), `USER-GUIDE.md:1` (0.5.6)
- Impact: support confusion and release artifact ambiguity.
- Recommendation: single source of truth from `VERSION` propagated to docs during release.

3) Network dependency in license check has no explicit trust policy documentation
- File: `lib/date_check.py:6-9`
- Impact: operational unpredictability if APIs throttle/change schema.
- Recommendation: document SLA/fallback behavior and consider enterprise-controlled time source endpoint.

## Positive Improvements Confirmed
- `deque` queue optimization in detector clustering (`lib/detector_engine.py:210-214`).
- Secure signing path now thumbprint-only (no password CLI arg) in `build.py:59-63`, `build.py:85-86`.
- File magic-number checks added in input validation (`lib/file_handler.py:200-212`).
- Page-specific detection state dictionaries introduced in app state (`app_gui.py:92-95`, properties at `app_gui.py:269-297`).
- CI pipeline added with Bandit/Safety/Pytest stages (`.github/workflows/main.yml`).

## Performance Audit Focus (Current)
- Detection algorithm complexity is acceptable for expected use; main remaining latency comes from synchronous preview runs and repeated image conversions.
- Canvas viewport strategy is good (`lib/canvas_navigation.py:162-190`), but frequent `PhotoImage` recreation and HQ rerender scheduling can still consume CPU during aggressive navigation.
- Batch export memory behavior improved (page release after use), but explicit `gc.collect()` per page in export path (`lib/batch_exporter.py:133-137`) may trade memory safety for throughput.

## Priority Remediation Plan
1. Replace remaining broad exceptions in `lib/date_check.py` and `lib/file_handler.py` with typed exceptions + logging.
2. Move live preview mask generation to background worker with cancellation/debouncing.
3. Replace full sweep + forced GC on navigation with bounded page cache policy.
4. Stabilize progress/dialog lifecycle geometry handling to avoid visual jumps.
5. Enforce CI quality gates: install dev deps consistently, add `--cov-fail-under`, and keep Bandit/Safety runnable in all developer environments.

## Audit Verdict
- Post-fix status: **Good progress, not yet fully enterprise-hardened**.
- Recommended release posture: acceptable for controlled internal usage; complete medium-priority items before broader production deployment.
