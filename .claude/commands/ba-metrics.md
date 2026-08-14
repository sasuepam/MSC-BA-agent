Display a metrics summary for all tracked BA workflow artifacts stored in `output/metrics/`.

---

## How to invoke

```
/ba-metrics                    — summary table for all features
/ba-metrics --detail [slug]    — per-phase breakdown for one feature
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
