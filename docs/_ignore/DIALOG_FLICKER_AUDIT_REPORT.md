# Dialog Flicker Audit Report

Date: 2026-05-31
Scope: Post-fix dialog behavior audit (no code changes)

## Executive Summary
- The flicker/glitch behavior is consistent with window lifecycle sequencing issues during dialog initialization.
- All dialogs are affected because they share the same icon helper and similar startup patterns.
- Primary root cause is repeated icon reapplication and post-creation geometry mutation.

## Files Reviewed
- `lib/dialogs.py`
- `lib/about_dialog.py`
- `lib/utils.py`

## Findings by Severity

### High

1) Repeated icon application causes redraw/flicker
- File: `lib/utils.py:53`, `lib/utils.py:54`, `lib/utils.py:55`
- Evidence:
```python
_apply()
window.after(delay_ms, _apply)
window.after(delay_ms * 4, _apply)
```
- Impact: Dialog repaints multiple times in first milliseconds of lifetime.
- Scope: Affects message dialogs, input dialogs, and about dialog.

2) Dialog geometry is changed after initial sizing
- Files:
  - `lib/dialogs.py:12`, `lib/dialogs.py:28`
  - `lib/dialogs.py:116`, `lib/dialogs.py:132`
  - `lib/about_dialog.py:10`, `lib/about_dialog.py:26`
- Evidence pattern:
```python
self.geometry("450x220")
...
self.update_idletasks()
...
self.geometry(f"+{x}+{y}")
```
- Impact: Window can appear then visibly jump/repaint when centered.

### Medium

1) Modal setup happens while startup mutations are still pending
- Files: `lib/dialogs.py:16-18`, `lib/dialogs.py:120-122`, `lib/about_dialog.py:14-16`
- Evidence:
```python
self.transient(parent)
self.grab_set()
apply_window_icon(self, parent.ico_path)
```
- Impact: Increases focus churn and visible startup instability.

2) Constructor-level wait with delayed callbacks increases timing sensitivity
- Files: `lib/dialogs.py:97`, `lib/dialogs.py:191`, `lib/about_dialog.py:112`
- Evidence:
```python
self.wait_window(self)
```
- Impact: Tight coupling of initialization + modal blocking can amplify flicker.

### Low

1) Dual icon APIs used in same startup path
- File: `lib/utils.py:42`, `lib/utils.py:49`
- Evidence:
```python
window.iconbitmap(ico_path)
...
window.iconphoto(True, photo)
```
- Impact: Not always problematic alone, but contributes when combined with retries.

## Cross-Dialog Correlation
- `CTkMessageDialog` calls `apply_window_icon(...)` in `lib/dialogs.py:18`
- `CTkInputDialog` calls `apply_window_icon(...)` in `lib/dialogs.py:122`
- `CTkAboutDialog` calls `apply_window_icon(...)` in `lib/about_dialog.py:16`
- Shared helper behavior in `lib/utils.py` explains why all dialogs show similar glitch behavior.

## Most Probable Root Cause Order
1. Triple icon reapplication (`_apply` + 2 delayed retries).
2. Initial paint then re-positioning (`geometry` called twice).
3. Modal/focus setup while visual mutations are still occurring.

## Repro Signature
- On open: brief flicker/flash.
- Then quick jump or repaint before settling.
- Reproduces on all custom dialogs (message/input/about).

## Conclusion
- This is a shared lifecycle issue, not an isolated dialog bug.
