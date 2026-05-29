# Security and Compliance Notes

## Signing and Distribution
- Code signing password must be provided via `PLANMINER_PFX_PASS`.
- Do not store signing credentials in the repository.

## Data Handling
- Presets store base64-encoded patch images in `assets/presets/presets.json`.
- Output files are written under `output/` with no retention policy.

## Recommendations
- Implement secure update verification (signed updates, hash checks).
- Add dependency pinning and SBOM generation.
- Maintain a data retention policy for presets and output artifacts.
