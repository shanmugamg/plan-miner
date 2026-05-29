# Enterprise Code Audit Report - PixelQuant/PlanMiner

Date: 2026-05-30
Auditor mode: Senior enterprise code audit
Scope: End-to-end audit across architecture, security, performance, testing, ML-specific concerns, and operations.

## Executive Summary
- The codebase is modular and readable (mixin-based split across `app_gui.py` and `lib/*`) and includes practical performance work (viewport cropping, delayed high-quality render).
- The project is **not enterprise-ready** yet due to critical governance/security gaps: plaintext local secret in `.env`, no dependency lock/manifest/SBOM workflow, and no CI/CD quality/security gates.
- Testing maturity is low for production standards: no stable `tests/` structure, no coverage reporting, and pytest collection currently breaks on ad-hoc scripts under `scratch/`.
- Detection pipeline is functional and fairly robust for heuristic HSV workflows, but still has avoidable hot-path inefficiencies and weak contract validation around presets/configuration.

## Severity Findings

### Critical

1) Plaintext signing secret present locally
- File: `.env:1`
- Evidence:
```env
PLANMINER_PFX_PASS=GeoICON2026!
```
- Risk: credential compromise and malicious binary signing risk.
- Recommendation: remove immediately, rotate cert/password, enforce secret manager or secure CI secret injection only; add pre-commit secret scanning.

2) No authoritative dependency manifest/lockfile
- Evidence: no `requirements*.txt`, `pyproject.toml`, `poetry.lock`, or `Pipfile` in repo.
- Risk: non-reproducible builds, unknown vulnerability/license exposure.
- Recommendation: add pinned dependency definition + lockfile, generate SBOM, enforce in CI.

### High

1) Broad exception handling suppresses actionable failures
- Files: `app_gui.py:171`, `lib/file_handler.py:44`, `lib/file_handler.py:208`, `lib/file_handler.py:258`, `lib/file_handler.py:264`, `lib/presets_manager.py:15`
- Evidence:
```python
except:
    pass
```
- Risk: silent state corruption and poor incident triage.
- Recommendation: catch explicit exception types and log structured context.

2) Insecure legacy signing path still supports password CLI arg
- File: `build.py:95`
- Evidence:
```python
cmd = [signtool, "sign", "/f", os.path.abspath(pfx_path), "/p", pfx_pass, ...]
```
- Risk: password disclosure through process inspection/telemetry.
- Recommendation: remove this path; allow certificate store signing only (`/sha1`) or external signing service.

3) Test framework is not production quality
- Files: `scratch/test_detect.py`, `scratch/test_detect_after.py`, `scratch/test_wrap_algo.py`
- Evidence: `pytest -q` collection fails due to hardcoded absolute paths and missing local files.
- Risk: no reliable regression gate.
- Recommendation: create `tests/` with unit/integration tests, add `pytest.ini`, exclude `scratch/` from discovery.

4) Missing CI/CD and container/release controls
- Evidence: no `.github/workflows/*`, no `Dockerfile`, no `docker-compose*.yml`.
- Risk: manual, non-auditable release process.
- Recommendation: add CI pipeline for lint/test/security/license/SBOM and signed release artifacts.

### Medium

1) Architectural coupling via shared mutable mixin state
- Files: `app_gui.py:33-41` and cross-mixin state mutation in `lib/*`
- Risk: high change blast radius, hard unit testing.
- Recommendation: extract services (`DocumentService`, `DetectionService`, `PresetService`) and typed state models.

2) Queue implementation in detector hot path is suboptimal
- File: `lib/detector_engine.py:213`
- Evidence:
```python
curr = queue.pop(0)
```
- Risk: O(n) dequeue overhead under many components.
- Recommendation: switch to `collections.deque` + `popleft()`.

3) Live preview performs full detection synchronously
- Files: `lib/canvas_events.py:270-276`, `lib/canvas_navigation.py:6-11`
- Risk: UI latency for high-DPI pages.
- Recommendation: async worker for preview mask generation, cache by immutable signature, cancel stale jobs.

4) Frozen-build logging uses NullHandler (no production forensics)
- File: `lib/logger.py:34-37`
- Evidence:
```python
logger.addHandler(logging.NullHandler())
```
- Risk: missing operational observability.
- Recommendation: configurable secure rotating logs with redaction.

5) Input validation is extension/size-based only
- File: `lib/file_handler.py:182-201`
- Risk: malformed files may still stress parser path.
- Recommendation: add MIME/signature checks, parser guardrails, and failure quarantining.

6) Preset schema validation is minimal
- File: `lib/presets_manager.py:127-137`
- Risk: malformed preset payloads produce runtime instability.
- Recommendation: enforce strict schema/range validation (or pydantic/jsonschema).

7) Hardcoded absolute paths in scratch tests
- Files: `scratch/test_detect.py:2`, `scratch/test_detect.py:9`, `scratch/test_detect.py:12`
- Risk: non-portable automation.
- Recommendation: replace with project-relative fixtures.

8) Counting logic may be semantically fragile
- File: `lib/batch_exporter.py:146-153`
- Evidence:
```python
legend_count = 1 if visible_count > 0 else 0
total = visible_count - legend_count
```
- Risk: unclear business logic and report drift.
- Recommendation: define counting contract and add unit tests for CSV semantics.

9) Documentation mismatch
- File: `AGENT.md:9`
- Finding: claims no file exceeds 200 lines, but multiple files exceed this.
- Recommendation: update docs and add doc-review checklist in PR flow.

### Low

1) Import hygiene and style nits
- Examples: `lib/detector_engine.py:3` (`os` unused), `lib/dialogs.py:1` (`os` unused)
- Recommendation: run `ruff`/`flake8` and enforce style checks in CI.

2) Runtime `print()` bypasses centralized logger
- Files: `lib/about_dialog.py:62`, `lib/presets_manager.py:38`, `lib/presets_manager.py:93`
- Recommendation: route to `self.logger` with appropriate level.

3) Windows-only assumptions reduce portability
- Files: `app_gui.py:22`, `build.py`
- Recommendation: isolate platform-specific behavior and document support matrix.

### Informational

1) Security tooling unavailable in current environment
- Commands attempted:
```bash
python -m bandit -r . -f txt
python -m safety check --full-report
```
- Result: modules not installed.
- Recommendation: add Bandit/Safety (or pip-audit) to dev dependencies and CI.

2) Coverage metric unavailable
- Cause: no standard `tests/` suite and collection failures in `scratch/`.
- Recommendation: set up `pytest-cov` and enforce threshold.

3) ML/Object detection strengths and gaps
- Strengths: hue wrap handling and viewport-cropped rendering are good practical optimizations.
- Gaps: no benchmark corpus, no reproducibility harness, no model/config version contract beyond ad-hoc files.

## Area-by-Area Assessment
- Code Quality & Architecture: Moderate; readable, but too much shared mutable state.
- Security: Below enterprise baseline due to secret/dependency governance gaps.
- Performance: Good local optimizations, but UI-thread and algorithmic hot spots remain.
- Testing & QA: Weak and non-gating.
- Error Handling & Logging: Mixed; too many silent catches and missing prod logging.
- Documentation & Maintainability: Adequate but partially stale.
- Dependency Management: Insufficient for enterprise compliance.
- ML/Object Detection Specific: Functional heuristic pipeline; weak reproducibility controls.
- Deployment & Operations: Not enterprise-ready; no CI/CD governance.

## Prioritized Remediation Plan
1. Eliminate plaintext secrets and rotate signing credentials; enforce secure signing path.
2. Add dependency lockfile, SBOM, vulnerability and license scans in CI.
3. Establish `tests/` with deterministic fixtures; add `pytest.ini` and coverage gates.
4. Replace bare `except` blocks with explicit exceptions and structured logging.
5. Refactor toward service boundaries and typed validation for config/preset data.
6. Move live preview detection off UI thread and optimize queue/dequeue in detector clustering.
