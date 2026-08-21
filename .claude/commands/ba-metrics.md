Display a metrics summary for all tracked BA workflow artifacts stored in `output/metrics/`.

---

## How to invoke

```
/ba-metrics                    — summary table for all features (all time)
/ba-metrics --week             — this week's features only (Mon–today)
/ba-metrics --detail [slug]    — per-phase breakdown for one feature
/ba-metrics --csv              — export all metrics as CSV
/ba-metrics --trend            — show improvement trends over time
```

---

## Step 1 — Locate metrics files

Run:
```bash
ls output/metrics/*.json 2>/dev/null || echo "NO_FILES"
```

If `NO_FILES` is returned, tell the user:
> "No metrics records found. Run the `/ba-workflow` to start tracking your first feature."
Then stop.

---

## Step 2 — Load all metrics files

For each `.json` file found, read it and parse the fields needed for display.

Use this Python snippet to extract a summary row per file:

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
    status = m.get('status', '—')
    total_min = m.get('total_duration_minutes')
    loops = m.get('feedback_loops', 0)
    tokens_total = m.get('tokens', {}).get('total')
    cost = m.get('estimated_cost_usd')

    rows.append({
        'slug': slug,
        'status': status,
        'total_min': str(total_min) + ' min' if total_min is not None else '—',
        'loops': str(loops),
        'tokens': '{:,}'.format(tokens_total) if tokens_total else '—',
        'cost': '\$' + '{:.3f}'.format(cost) if cost else '—',
    })

print(json.dumps(rows))
"
```

---

## Step 3 — Display summary table

Print the following table using the extracted data:

```
## BA Workflow Metrics

| Feature slug          | Status      | Total time | Feedback loops | Tokens  | Cost    |
|-----------------------|-------------|------------|----------------|---------|---------|
| [slug]                | [status]    | [total_min]| [loops]        | [tokens]| [cost]  |
```

After the table, print:
```
Run `/ba-metrics --detail [slug]` to see the per-phase breakdown for any feature.
```

---

## Step 4 — Detail view (when --detail [slug] is provided)

Find the file `output/metrics/metrics_[slug].json`. If not found, say:
> "No metrics file found for '[slug]'. Check the slug name with `/ba-metrics`."

Then print the full per-phase breakdown:

```bash
python3 -c "
import json

slug = '[SLUG]'   # replace with the provided slug
with open(f'output/metrics/metrics_{slug}.json') as f:
    m = json.load(f)

print(json.dumps(m, indent=2))
"
```

Present the output in this format:

```
## Metrics detail — [feature_name]

**Status:** [status]
**Session start:** [session_start]
**Session end:** [session_end or —]
**Total duration:** [total_duration_minutes] min

### Phases

| Phase      | Started at       | Completed at     | Duration  | Notes                                   |
|------------|------------------|------------------|-----------|-----------------------------------------|
| Spec       | [started_at]     | [completed_at]   | [min]     | Iterations: [iterations], File: [file]  |
| Stories    | [started_at]     | [completed_at]   | [min]     | Iterations: [iterations], CRs: [n], USs: [n] |
| Validation | —                | —                | —         | [n] run(s): [list blockers/warnings per run] |
| Amend      | —                | —                | —         | [n] run(s): [applied/edited/skipped per run] |
| Publish    | [started_at]     | [completed_at]   | —         | Jira: [tickets], Confluence: [page]     |

### Quality
- **Feedback loops:** [feedback_loops]

### Token usage
- **Input tokens:** [input or —]
- **Output tokens:** [output or —]
- **Total tokens:** [total or —]
- **Model:** [model]
- **Estimated cost:** [estimated_cost_usd or —]
```

For Validation runs, list each run on a separate line:
```
Run 1: [blockers] blocker(s), [warnings] warning(s), [infos] info(s) — completed [completed_at]
```

For Amend runs:
```
Run 1: [applied] applied, [edited] edited, [skipped] skipped — completed [completed_at]
```

If any field is `null`, display `—`.

---

## --week flag

Filter to features where `timestamp_created` or `session_start` falls in the current ISO week (Monday–Sunday). Display the same summary table but labelled "This week's features". If no features this week: "No features processed this week."

---

## --csv flag

Export all metrics as a CSV file. Run:

```bash
python3 -c "
import json, glob, csv, sys
from io import StringIO

files = sorted(glob.glob('output/metrics/*.json'))
if not files:
    print('NO_FILES')
    sys.exit(0)

output = StringIO()
writer = csv.writer(output)
writer.writerow([
    'feature_slug', 'feature_name', 'status', 'session_start', 'session_end',
    'total_duration_minutes', 'feedback_loops',
    'spec_iterations', 'spec_auto_fixes', 'spec_manual_fixes',
    'stories_input_source', 'cr_count', 'us_count', 'stories_auto_fixed', 'stories_manual_fixed',
    'validation_mode', 'intake_enabled',
    'tokens_total', 'estimated_cost_usd'
])
for f in files:
    with open(f) as fh:
        m = json.load(fh)
    ph = m.get('phases', {})
    spec = ph.get('spec', {})
    stories = ph.get('stories', {})
    intake = m.get('intake_phase', {})
    writer.writerow([
        m.get('feature_slug',''), m.get('feature_name',''), m.get('status',''),
        m.get('session_start',''), m.get('session_end',''),
        m.get('total_duration_minutes',''), m.get('feedback_loops',0),
        spec.get('iterations',0), spec.get('template_auto_fixes',0), spec.get('template_manual_fixes',0),
        stories.get('input_source','spec'), stories.get('cr_count',''), stories.get('us_count',''),
        stories.get('stories_auto_fixed',0), stories.get('stories_manual_fixed',0),
        m.get('validation_mode',''), intake.get('enabled', False),
        m.get('tokens',{}).get('total',''), m.get('estimated_cost_usd','')
    ])
print(output.getvalue())
"
```

Save the output to `output/metrics/metrics_export.csv` and tell the user the file path.

---

## --trend flag

Show improvement trends across all features. Run:

```bash
python3 -c "
import json, glob
files = sorted(glob.glob('output/metrics/*.json'))
features = []
for f in files:
    with open(f) as fh:
        m = json.load(fh)
    features.append(m)

if len(features) < 2:
    print('Not enough data for trend analysis. Need at least 2 completed features.')
else:
    # Sort by session_start
    features.sort(key=lambda m: m.get('session_start','') or '')
    loops = [m.get('feedback_loops',0) for m in features]
    slugs = [m.get('feature_slug','?') for m in features]

    # Structural fix ratio
    struct_ratios = []
    for m in features:
        ph = m.get('phases',{})
        amend_runs = ph.get('amend',{}).get('runs',[])
        struct = sum(r.get('structural_fixes',0) or 0 for r in amend_runs)
        content = sum(r.get('content_fixes',0) or 0 for r in amend_runs)
        total = struct + content
        struct_ratios.append(round(struct/total*100) if total > 0 else None)

    print(json.dumps({'slugs': slugs, 'loops': loops, 'struct_ratios': struct_ratios}, indent=2))
"
```

Present results as:

```
## BA Metrics Trends

Features (oldest → newest): [slug1], [slug2], [slug3] ...

Feedback loops per feature:
  [slug1]: [n] | [slug2]: [n] | [slug3]: [n]
  Trend: ↑ increasing / ↓ decreasing / → stable

Structural fix ratio (% of amend fixes that were structural):
  [slug1]: [n]% | [slug2]: [n]% | [slug3]: [n]%
  Target: <10%
  Trend: ↓ improving / ↑ worsening

Recommendation:
  [1–2 lines based on the data, e.g. "Feedback loops are decreasing — template validation is working."]
```
