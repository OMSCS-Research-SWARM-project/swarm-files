This directory contains a small labeled realistic practice dataset. Use it to test whether your agent generalizes beyond the honeypot examples. Events with the same scenario_id should be analyzed together before assigning per-event classifications.

The dataset files are sanitized to match output_spec.md.

Required classification fields:
- event_id
- classification
- scenario_id
- cve

The local checker currently scores classification labels only. CVE values are included for compatibility with the spec and future scoring, but CVE attribution is not currently scored.

Do not output events from your agent. The agent should output classifications only.