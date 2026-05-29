# Security and Compliance Notes (v0.5.3)

This document details the security posture, defensive configurations, and codesigning guidelines implemented in **PlanMiner**.

---

## 1. Code Signing and Binary Integrity

PlanMiner executables distributed to enterprise environments must be signed to prevent tempering and satisfy Windows Defender SmartScreen filters.

### Secure Thumbprint Codesigning
- **Mechanism**: Instead of storing sensitive PFX certificate files or passwords in configuration/source files (which risk credential leakage), the build pipeline uses **Windows Certificate Store Thumbprint Signing**.
- **Configuration**: The builder looks for `PLANMINER_SIGN_THUMBPRINT` in the `.env` file or environment.
- **Execution**: The build script utilizes `signtool.exe` with the `/sha1 <thumbprint>` switch. Signing occurs entirely within the Windows Certificate Store, ensuring private keys remain secure.
- **Self-Signed Certificates**: For development and testing environments, self-signed certificates can be generated, exported as a `.cer` file, and distributed alongside the binary. The build process copies `codesign.cer` and `CERT_DEPLOYMENT_GUIDE.html` directly to the `PlanMiner_Dist` output folder to assist users with importing the certificate into their *Trusted Root Certification Authorities* store.

---

## 2. Input File Parsing and Content Validation

To defend against file-format exploits and malicious payloads disguised as drawing files (e.g., polyglot files or double-extension tricks), PlanMiner validates files before processing them:

### Magic Number Validation
Before attempting to parse files using PyMuPDF or OpenCV, the application reads the first 4 bytes of the file and validates the file header matches its extension:
- **PDF files (`.pdf`)**: Must begin with `b"%PDF"`
- **PNG files (`.png`)**: Must begin with `b"\x89PNG"`
- **JPEG files (`.jpg`, `.jpeg`)**: Must begin with `b"\xFF\xD8"`
Files failing this check are rejected with a user warning, preventing the execution of unexpected binary parser routines on malformed or malicious inputs.

### File Size Constraints
To mitigate Denial of Service (DoS) attacks caused by memory exhaustion (OOM) when loading massive images/documents, the following thresholds are enforced in [file_handler.py](file:///d:/python-projects/raghu-software/pixelquant/lib/file_handler.py):
- **Warning Threshold**: 200 MB (Warns the user that loading may be slow)
- **Hard Limit**: 300 MB (Blocks loading completely to maintain UI thread and system stability)

---

## 3. Safe Error Handling & Stability

Bare `except:` blocks are prohibited. They mask logic bugs, cause infinite loops, or make troubleshooting impossible.
- **Remediation**: All catch-all handlers are replaced with explicit typed exceptions or log tracebacks via `logger.exception()` using sanitized/redacted error formats.
- **State Cleanup**: Window closing requests (`WM_DELETE_WINDOW`) and exception states trigger clean garbage collection (`gc.collect()`) and release underlying fitz/document locks to prevent memory leakage and file locking.

---

## 4. Data Privacy & Logs Sanitization

- **No Plaintext Path Logs**: Full local file paths of input files are hashes of the filename to protect PII.
- **PII Scrubbing**: Logs redact system profile paths (e.g., Windows username) when compiled via `RedactingFilter`.
- **Local Data Retention**: Settings profiles (`assets/presets/presets.json`) store HSV parameters and small base64-encoded PNG patch images of targeted symbols. These presets do not contain network paths or local identity data. Presets should be regularly audited or cleared based on company data-retention schedules.
