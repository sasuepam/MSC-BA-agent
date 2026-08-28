Display a metrics summary for all tracked BA workflow artifacts stored in `output/metrics/`.

---

## How to invoke

```
/ba-metrics                        — summary table for all features
/ba-metrics --week                 — this week's features (Mon–Fri 6pm cutoff)
/ba-metrics --detail [slug]        — per-phase breakdown for one feature
/ba-metrics --csv                  — export all metrics to CSV
/ba-metrics --trend                — improvement trends across all features
```

---

## Step 1 — Locate metrics files

```bash
ls output/metrics/*.json 2>/dev/null || echo "NO_FILES"
```

If `NO_FILES` is returned, tell the user:
> "No metrics records found. Run `/ba-workflow` to start tracking your first feature."
Then stop.

---

## Step 2 — Summary view (default)

Load all `.json` files and display:

```bash
python3 -c "
import json, glob, sys, os

files = sorted(glob.glob('output/metrics/*.json'))
if not files:
    print('NO_FILES')
    sys.exit(0)

rows = []
for f in files:
    with open(f) as fh:
        m = json.load(fh)

    slug = m.get('feature_slug', os.path.basename(f).replace('metrics_','').replace('.json',''))
    req_id = m.get('feature_requirement_id') or '—'
    status = m.get('status', '—')
    total_min = m.get('total_duration_minutes')
    loops = m.get('feedback_loops', 0)
    spec_iter = m.get('phases', {}).get('spec', {}).get('iterations', 0)
    stories_iter = m.get('phases', {}).get('stories', {}).get('iterations', 0)

    # Template compliance: 1 - (structural_fixes / total_fixes) across all amend runs
    amend_runs = m.get('phases', {}).get('amend', {}).get('runs', [])
    total_struct = sum(r.get('structural_fixes', 0) for r in amend_runs)
    total_content = sum(r.get('content_fixes', 0) for r in amend_runs)
    total_fixes = total_struct + total_content
    compliance = str(round((1 - total_struct / total_fixes) * 100)) + '%' if total_fixes else '—'

    rows.append({
        'slug': slug,
        'req_id': req_id,
        'status': status,
        'total_min': str(total_min) + ' min' if total_min is not None else '—',
        'loops': str(loops),
        'spec_iter': str(spec_iter),
        'stories_iter': str(stories_iter),
        'compliance': compliance,
    })

print(json.dumps(rows))
"
```

Display:

```
## BA Workflow Metrics

| Feature slug | Req ID   | Status | Total time | Feedback loops | Spec iter | Stories iter | Template compliance |
|---|---|---|---|---|---|---|---|
| [slug] | [req_id] | [status] | [total_min] | [loops] | [spec_iter] | [stories_iter] | [compliance] |
```

---

## --week view

Filter metrics files where `timestamp_created` falls within the current week (Monday 00:00 to Friday 18:00 local time).

```bash
python3 -c "
import json, glob, sys
from datetime import datetime, timedelta, timezone

files = sorted(glob.glob('output/metrics/*.json'))
now = datetime.now()
# Week window: Monday 00:00 to Friday 18:00
monday = now - timedelta(days=now.weekday())
monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
friday_cutoff = monday + timedelta(days=4, hours=18)

weekly = []
for f in files:
    with open(f) as fh:
        m = json.load(fh)
    ts = m.get('timestamp_created')
    if not ts:
        continue
    created = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
    if monday <= created <= friday_cutoff:
        weekly.append(m)

print(json.dumps(weekly))
"
```

Display the same summary table as the default view, filtered to this week's features only. If none found, say: "No features processed this week."

---

## --detail [slug] view

Find `output/metrics/metrics_[slug].json`. If not found:
> "No metrics file found for '[slug]'. Check the slug with `/ba-metrics`."

Display the full per-phase breakdown:

```
## Metrics detail — [feature_name] ([req_id])

**Status:** [status]
**Session start:** [session_start]
**Session end:** [session_end or —]
**Total duration:** [total_duration_minutes] min

### Phases

| Phase      | Started at | Completed at | Duration | Notes |
|---|---|---|---|---|
| Spec | [started_at] | [completed_at] | [min] | Iterations: [n] · Auto fixes: [n] · Manual fixes: [n] |
| Stories | [started_at] | [completed_at] | [min] | Iterations: [n] · CRs: [n] · USs: [n] · Source: [input_source] · Auto fixed: [n] · Manual fixed: [n] |
| Validation | — | — | — | [n] run(s) — see below |
| Amend | — | — | — | [n] run(s) — see below |
| Publish | [started_at] | [completed_at] | — | Jira: [tickets] · Confluence: [page] |

### Validation runs
For each run:
Run [N]: Structural — [blockers] blockers, [warnings] warnings · Content — [blockers] blockers, [warnings] warnings, [infos] infos · Completed [completed_at]

### Amend runs
For each run:
Run [N]: Applied [n] · Edited [n] · Skipped [n] · Structural fixes [n] · Content fixes [n] · Completed [completed_at]

### Quality
- **Feedback loops:** [feedback_loops]
- **Template compliance:** [calculated as above]

### Token usage
- **Input tokens:** [input or —]
- **Output tokens:** [output or —]
- **Total tokens:** [total or —]
- **Model:** [model]
- **Estimated cost:** [estimated_cost_usd or —]
```

---

## --csv export

Export all metrics to `output/metrics/exports/metrics_export_[YYYY-MM-DD].csv`:

```bash
mkdir -p output/metrics/exports
python3 -c "
import json, glob, csv, sys
from datetime import datetime

files = sorted(glob.glob('output/metrics/*.json'))
if not files:
    print('No metrics files found.')
    sys.exit(0)

date_str = datetime.now().strftime('%Y-%m-%d')
out_path = f'output/metrics/exports/metrics_export_{date_str}.csv'

fieldnames = [
    'feature_slug', 'req_id', 'feature_name', 'status',
    'total_duration_minutes', 'feedback_loops',
    'spec_iterations', 'stories_iterations', 'cr_count', 'us_count', 'input_source',
    'struct_violations_blockers', 'struct_violations_warnings',
    'content_violations_blockers', 'content_violations_warnings', 'content_violations_infos',
    'structural_fixes', 'content_fixes', 'template_compliance_pct',
    'total_tokens', 'estimated_cost_usd', 'timestamp_created'
]

rows = []
for f in files:
    with open(f) as fh:
        m = json.load(fh)
    phases = m.get('phases', {})
    amend_runs = phases.get('amend', {}).get('runs', [])
    val_runs = phases.get('validation', {}).get('runs', [])
    total_struct_fix = sum(r.get('structural_fixes', 0) for r in amend_runs)
    total_content_fix = sum(r.get('content_fixes', 0) for r in amend_runs)
    total_fixes = total_struct_fix + total_content_fix
    compliance = round((1 - total_struct_fix / total_fixes) * 100, 1) if total_fixes else None
    total_sv_b = sum(r.get('structural_violations', {}).get('blockers', 0) for r in val_runs)
    total_sv_w = sum(r.get('structural_violations', {}).get('warnings', 0) for r in val_runs)
    total_cv_b = sum(r.get('content_violations', {}).get('blockers', 0) for r in val_runs)
    total_cv_w = sum(r.get('content_violations', {}).get('warnings', 0) for r in val_runs)
    total_cv_i = sum(r.get('content_violations', {}).get('infos', 0) for r in val_runs)
    rows.append({
        'feature_slug': m.get('feature_slug'),
        'req_id': m.get('feature_requirement_id'),
        'feature_name': m.get('feature_name'),
        'status': m.get('status'),
        'total_duration_minutes': m.get('total_duration_minutes'),
        'feedback_loops': m.get('feedback_loops', 0),
        'spec_iterations': phases.get('spec', {}).get('iterations', 0),
        'stories_iterations': phases.get('stories', {}).get('iterations', 0),
        'cr_count': phases.get('stories', {}).get('cr_count'),
        'us_count': phases.get('stories', {}).get('us_count'),
        'input_source': phases.get('stories', {}).get('input_source'),
        'struct_violations_blockers': total_sv_b,
        'struct_violations_warnings': total_sv_w,
        'content_violations_blockers': total_cv_b,
        'content_violations_warnings': total_cv_w,
        'content_violations_infos': total_cv_i,
        'structural_fixes': total_struct_fix,
        'content_fixes': total_content_fix,
        'template_compliance_pct': compliance,
        'total_tokens': m.get('tokens', {}).get('total'),
        'estimated_cost_usd': m.get('estimated_cost_usd'),
        'timestamp_created': m.get('timestamp_created'),
    })

with open(out_path, 'w', newline='') as csvf:
    writer = csv.DictWriter(csvf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f'Exported {len(rows)} record(s) to {out_path}')
"
```

Tell the user the export path.

---

## --trend view

Read all metrics files sorted by `timestamp_created`. Display improvement trends across all features:

```bash
python3 -c "
import json, glob, sys
from datetime import datetime

files = sorted(glob.glob('output/metrics/*.json'))
if len(files) < 2:
    print('Need at least 2 features to show trends.')
    sys.exit(0)

records = []
for f in files:
    with open(f) as fh:
        m = json.load(fh)
    ts = m.get('timestamp_created', '')
    amend_runs = m.get('phases', {}).get('amend', {}).get('runs', [])
    val_runs = m.get('phases', {}).get('validation', {}).get('runs', [])
    total_struct = sum(r.get('structural_fixes', 0) for r in amend_runs)
    total_content = sum(r.get('content_fixes', 0) for r in amend_runs)
    total_fixes = total_struct + total_content
    compliance = round((1 - total_struct / total_fixes) * 100, 1) if total_fixes else None

    # Identify most common content issue from rule classification in val runs
    # (structural rules 3,4,5,8 — content rules 1,2,6,7)
    records.append({
        'slug': m.get('feature_slug'),
        'ts': ts,
        'loops': m.get('feedback_loops', 0),
        'duration': m.get('total_duration_minutes'),
        'compliance': compliance,
        'struct_pct': round(total_struct / total_fixes * 100, 1) if total_fixes else None,
    })

records.sort(key=lambda r: r['ts'])

avg_loops = round(sum(r['loops'] for r in records) / len(records), 1)
avg_duration = round(sum(r['duration'] for r in records if r['duration']) / max(1, sum(1 for r in records if r['duration'])), 1)

# Rolling 5-feature trend for compliance
recent = [r['compliance'] for r in records[-5:] if r['compliance'] is not None]
if len(recent) >= 2:
    trend = 'improving' if recent[-1] > recent[0] else ('declining' if recent[-1] < recent[0] else 'stable')
else:
    trend = 'insufficient data'

avg_compliance = round(sum(recent) / len(recent), 1) if recent else None
avg_struct_pct = round(sum(r['struct_pct'] for r in records if r['struct_pct'] is not None) / max(1, sum(1 for r in records if r['struct_pct'] is not None)), 1)

print(json.dumps({
    'total_features': len(records),
    'avg_loops': avg_loops,
    'avg_duration_min': avg_duration,
    'avg_compliance_pct': avg_compliance,
    'compliance_trend': trend,
    'avg_structural_fix_pct': avg_struct_pct,
}))
"
```

Display:

```
## BA Metrics — Trends ([N] features)

Average feedback loops per feature : [avg_loops]  (target: <1.5)
Average total duration per feature  : [avg_duration_min] min
Template compliance rate            : [avg_compliance_pct]%  (trend: [↑ improving / ↓ declining / → stable])
Structural fix rate                 : [avg_structural_fix_pct]%  (target: <10%)
```

If fewer than 2 features are recorded, tell the user trends are not yet available.
