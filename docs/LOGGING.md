# Logging and Audit Notes

PlanMiner writes structured logs to `logs/planminer.log`.

Events captured:
- app_start
- file_load
- page_show
- page_rendered / page_render_failed
- template_extracted / template_extract_failed
- detection_complete / detection_failed
- preset_saved / preset_save_failed / preset_applied
- batch_export_complete / batch_export_failed
- manual_box_added / manual_box_removed

Log format:
`YYYY-MM-DDTHH:MM:SS LEVEL planminer message`

PII and data handling:
- File paths are logged for diagnostics. Avoid logging sensitive paths in regulated environments.
- If needed, replace paths with hashes or redacted values.
