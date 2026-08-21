Generate a weekly BA metrics report from all files in `output/metrics/`. Can be run manually at any time. Also invoked automatically by the scheduled task every Friday at 5pm GMT+1.

---

## Step 1 — Locate metrics files

```bash
ls output/metrics/*.json 2>/dev/null || echo "NO_FILES"
```

If `NO_FILES`, print: "No metrics records found. Nothing to report." and stop.

---

## Step 2 — Determine report scope

If called with `--week`, filter to features where `timestamp_created` or `session_start` falls within the current week (Monday to today).

If called with no flag, include all features (all-time summary).

---

## Step 3 — Aggregate metrics

Run:

```bash
python3 -c "
import json, glob, sys
from datetime import datetime, timedelta, timezone

files = sorted(glob.glob('output/metrics/*.json'))
features = []
for f in files:
    with open(f) as fh:
        m = json.load(fh)
    features.append(m)

# --- per-feature stats ---
rows = []
for m in features:
    slug = m.get('feature_slug', '—')
    name = m.get('feature_name', slug)
    status = m.get('status', '—')
    loops = m.get('feedback_loops', 0)
    dur = m.get('total_duration_minutes')

    phases = m.get('phases', {})
    spec = phases.get('spec', {})
    stories = phases.get('stories', {})
    val_runs = phases.get('validation', {}).get('runs', [])
    amend_runs = phases.get('amend', {}).get('runs', [])

    spec_auto = spec.get('template_auto_fixes', 0) or 0
    spec_manual = spec.get('template_manual_fixes', 0) or 0
    stories_auto = stories.get('stories_auto_fixed', 0) or 0
    stories_manual = stories.get('stories_manual_fixed', 0) or 0
    total_auto = spec_auto + stories_auto
    total_manual = spec_manual + stories_manual
    total_fixes = total_auto + total_manual
    compliance_pct = round((total_auto / total_fixes * 100) if total_fixes > 0 else 100)

    struct_violations = sum(
        (r.get('structural_violations', {}).get('blockers', 0) or 0) +
        (r.get('structural_violations', {}).get('warnings', 0) or 0)
        for r in val_runs
    )
    content_violations = sum(
        (r.get('content_violations', {}).get('blockers', 0) or 0) +
        (r.get('content_violations', {}).get('warnings', 0) or 0)
        for r in val_runs
    )
    amend_struct = sum(r.get('structural_fixes', 0) or 0 for r in amend_runs)
    amend_content = sum(r.get('content_fixes', 0) or 0 for r in amend_runs)

    rows.append({
        'slug': slug,
        'name': name,
        'status': status,
        'loops': loops,
        'duration_min': dur,
        'compliance_pct': compliance_pct,
        'struct_violations': struct_violations,
        'content_violations': content_violations,
        'amend_struct': amend_struct,
        'amend_content': amend_content,
    })

# --- aggregate totals ---
avg_loops = round(sum(r['loops'] for r in rows) / len(rows), 1) if rows else 0
avg_compliance = round(sum(r['compliance_pct'] for r in rows) / len(rows), 1) if rows else 100
total_struct = sum(r['struct_violations'] for r in rows)
total_content = sum(r['content_violations'] for r in rows)
total_amend = sum(r['amend_struct'] + r['amend_content'] for r in rows)
struct_ratio = round(total_struct / (total_struct + total_content) * 100) if (total_struct + total_content) > 0 else 0

print(json.dumps({'rows': rows, 'totals': {
    'feature_count': len(rows),
    'avg_loops': avg_loops,
    'avg_compliance_pct': avg_compliance,
    'total_structural_violations': total_struct,
    'total_content_violations': total_content,
    'structural_ratio_pct': struct_ratio,
}}, indent=2))
"
```

---

## Step 4 — Format the report

Build the report text using the aggregated data:

```
Weekly BA Metrics Report
Generated: [DD/MMM/YYYY] at [HH:MM] GMT+1

Features Processed:
[For each feature:]
├─ [feature_name]: [loops] iteration(s), [compliance_pct]% template compliance, [duration_min or —] min

Trends:
├─ Total features: [feature_count]
├─ Average iterations per feature: [avg_loops] (target: <1.5)
├─ Average template compliance: [avg_compliance_pct]% (target: >90%)
├─ Structural vs content fix ratio: [structural_ratio_pct]% structural (target: <10%)
├─ Total structural violations found: [total_structural_violations]
└─ Total content violations found: [total_content_violations]

Recommendations:
[Generate 1–3 specific recommendations based on the data, e.g.:]
├─ Features with >2 iterations: [list slugs] — review input quality or template guidance
├─ Template compliance below 80%: [list slugs] — consider running /intake to clean inputs first
└─ High structural violation count — ensure spec_validator.py auto-fix is enabled in spec generator
```

---

## Step 5 — Save report

```bash
REPORT_DATE=$(date -u +"%Y_%m_%d")
mkdir -p output/metrics/weekly_reports
REPORT_FILE="output/metrics/weekly_reports/ba_metrics_${REPORT_DATE}.md"
```

Write the formatted report text to `$REPORT_FILE`.

---

## Step 6 — Report to the user

Print the full report text to the terminal.

Then say:
> "Report saved to `output/metrics/weekly_reports/ba_metrics_[date].md`"

If this is the scheduled Friday run, also say:
> "Scheduled weekly report complete. You can email this report to sarah_suda@epam.com if needed."

---

## Notes

- This command does not send email automatically. Email delivery requires an email MCP tool or manual action.
- Run `/ba-metrics-report` at any time to regenerate the report on demand.
- The report uses all metrics files in `output/metrics/` regardless of feature status (in_progress or published).
