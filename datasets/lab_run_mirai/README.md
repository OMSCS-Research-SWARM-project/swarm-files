This directory contains the labeled lab run Mirai training dataset. Use these events and classifications to teach your agent the original Mirai behavior.

The dataset files are sanitized to match output_spec.md.

Required classification fields:
- event_id
- classification
- scenario_id
- cve

The local checker currently scores classification labels only. CVE values are included for compatibility with the spec and future scoring, but CVE attribution is not currently scored.

Do not output events from your agent. The agent should output classifications only.