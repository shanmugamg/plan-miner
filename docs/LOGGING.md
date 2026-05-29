# Logging and Audit Notes (v0.5.3)

PlanMiner writes structured, audit-ready logs to `logs/planminer.log`.

## Captured Events
- `app_start`
- `file_load`
- `page_show`
- `page_rendered` / `page_render_failed`
- `template_extracted` / `template_extract_failed`
- `detection_complete` / `detection_failed`
- `preset_saved` / `preset_save_failed` / `preset_applied`
- `batch_export_complete` / `batch_export_failed`
- `manual_box_added` / `manual_box_removed`

## Log Format
`YYYY-MM-DDTHH:MM:SS LEVEL planminer message`

Example:
`2026-05-30T07:12:34 INFO planminer page_show index=0`

---

## PII and Data Sanitization

To comply with enterprise security standards and data privacy regulations, PlanMiner implements strict sanitization overrides:

### 1. Filename Hashing (SHA-256)
When loading drawings or documents, the absolute file path and raw filename are never printed in plain text to the log file. Instead, the filename is hashed using SHA-256 and truncated to an 8-character identifier.
- **Log Format**: `file_load sanitized_name=doc_<sha256_hash_prefix>.<extension>`
- **Example**: `file_load sanitized_name=doc_a1b2c3d4.pdf`

### 2. Path Redaction Filter (`RedactingFilter`)
When running as a compiled standalone executable (`sys.frozen`), logs are processed through a custom `RedactingFilter`. This filter detects Windows home directory paths and replaces the username with `<REDACTED>`.
- **Target Pattern**: `C:\Users\<username>\`
- **Output Pattern**: `C:\Users\<REDACTED>\`
This prevents logs from exposing corporate Windows usernames or profile names when troubleshooting builds on client machines.

### 3. Log Rotation
In frozen builds, logging switches to a `RotatingFileHandler` with:
- **Maximum File Size**: 5 MB (`maxBytes=5242880`)
- **Backup Count**: 2 files
This bounds the application's disk footprint and prevents disk-exhaustion vulnerabilities.

### 4. Exception Handling
Instead of bare `except:` blocks that mask bugs, PlanMiner catches typed exceptions and logs them via `logger.exception()` (which logs the full traceback with redacted paths) to ensure maximum observability without compromising security.
