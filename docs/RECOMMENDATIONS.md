# Recommendations & Best Practices

Guidance for getting the best results from the BA Agent.

---

## Before You Start Any Feature

### Use intake for PDFs and meeting recordings
If your input materials include PDFs or meeting recordings (VTT + video), run `/intake` before the spec phase. The intake phase produces clean, structured Markdown that the spec generator reads far more reliably than a raw binary.

For plain text, emails, or Confluence URLs — you can skip intake and paste directly.

### Provide everything, not just a summary
The agent cannot invent content. A full email thread is better than a paraphrase. A Confluence page URL is better than "the page says X". Multiple sources are better than one — paste the stakeholder email, link the Confluence page, and attach the meeting notes all at once.

### Resolve TBCs before generating stories
Stories inherit `[TO BE CONFIRMED]` fields from the spec, which then become BLOCKERs in validation. It is faster to fill in TBCs in the spec first than to resolve them as individual validation flags later.

```
List all [TO BE CONFIRMED] markers currently in the spec with the section and field name.
```

---

## During Spec Generation

### Check the template validation result
The agent runs `spec_validator.py` before saving the spec. If it reports violations — even after an auto-retry — review them before moving to stories. A structural issue in the spec will cascade into story validation BLOCKERs.

### Don't manually edit the spec HTML after generation
If the spec needs changes, ask the agent to make them in Codemie. Manual HTML edits can break table structure or introduce inline styles that `spec_validator.py` will flag. If you must edit manually, run `/ba-workflow` → option 4 → choose automated validation to recheck structure afterwards.

### Name the MuleSoft API explicitly in use cases
The Use Cases section requires the responsible API in the "Functionality Expected" column. If your source materials don't name it clearly, tell the agent:

```
The responsible MuleSoft API for all use cases in this feature is [API name].
```

---

## During Story Generation

### Verify the CR / US split before proceeding
After stories are generated, ask the agent to explain its split decisions before moving to validation:

```
Walk me through why each interface was given a CR versus a US.
```

This catches misclassifications early — it is much faster to correct a story type before validation than after a round of BLOCKERs.

### Check the ADF exclusion list
After generation, verify the excluded interfaces list matches your expectations. If a non-ADF interface was accidentally excluded, correct it before publishing:

```
INT[number] was excluded. Can you confirm whether it was ADF-prefixed or explain why?
```

### Use direct input for quick stories
If you only need stories and don't need a full spec (e.g. for a small change request), use direct input mode — no spec file needed. Provide a list of interfaces and brief requirements and the agent will generate and validate stories directly.

---

## Validation

### Choose your validation mode deliberately
After spec and story generation the agent asks how you'd like to review output. Don't default to "Skip" for complex features:

- **Conversational** — fastest; good for features you know well and simple changes
- **Automated** — catches structural and traceability issues you might miss in chat
- **Both** — safest for complex features or specs going to a new Solution Architect

### Run structural rules separately from content rules
If you suspect a template issue, run structural rules first and resolve them before content rules. Content BLOCKERs in a structurally broken file are harder to reason about.

```
Run validation — structural rules only (Rules 9–14).
```

### Always re-validate after amendments
The amend phase can resolve some flags while inadvertently introducing others (e.g. editing a BDD criterion to fix vague language but accidentally breaking the Given/When/Then format). A quick re-validation confirms you're clean before publishing.

---

## Known Issues to Watch For

### Stories with vague BDD language (Rule 14 WARNING → BLOCKER)
**Symptom:** Acceptance criteria contain phrases like "works correctly", "system responds", "data is saved".
**Cause:** The model sometimes generates plausible but untestable BDD criteria when source materials don't provide specific expected outcomes.
**Fix:** Rule 14 catches these. In `/ba-amend`, provide the specific measurable outcome when prompted.
**Prevention:** If your input materials include explicit expected outcomes (e.g. HTTP response codes, field values, timing SLAs), paste them in. The more specific the input, the more testable the generated criteria.

### TBC fields in critical positions (Rule 1 BLOCKER)
**Symptom:** Summary field or User Story Statement contains `[TO BE CONFIRMED]`.
**Cause:** The model could not derive the value from input materials.
**Fix:** Provide the value explicitly during the amend phase.
**Prevention:** Before generating stories, ask the agent to list all TBC markers in the spec. Resolve the ones in Feature Summary and Business Requirements first — they feed directly into story summaries and statements.

### SA-owned sections flagged as empty (Rule 10)
**Symptom:** Rule 10 flags a missing or empty SA section.
**Cause:** The spec was generated on a feature where no SA has contributed yet, or the spec template was not read before generation.
**Fix:** These sections are SA responsibility. Add the standard placeholder text: `Populated by Solution Architect.` This satisfies Rule 10 while making the ownership clear.
**Prevention:** The spec generator reads the template before generating. If Rule 10 still fires, it means the SA section placeholder is missing entirely — check that the spec template is intact.

### ADF interface slipping into stories (Rule 4 BLOCKER)
**Symptom:** A story references an ADF-prefixed interface.
**Cause:** The input materials listed the ADF interface without clearly flagging it as ADF-owned, or the exclusion rule was applied inconsistently.
**Fix:** In `/ba-amend`, find the Rule 4 flag and choose "Accept fix" to remove the ADF story.
**Prevention:** If your feature involves a mix of INT and ADF interfaces, call it out explicitly when starting the workflow: "Exclude all ADF-prefixed interfaces. INT-prefixed interfaces only."

---

## Metrics and Improvement

### Watch the structural fix ratio in trends
`/ba-metrics --trend` shows what percentage of amendment fixes were structural (template) vs content. A structural ratio above ~15% suggests input materials are thin — the agent is generating with insufficient context and the template validator is catching structural gaps.

If structural ratio is high: try running `/intake` preprocessing, or provide more complete input materials before spec generation.

### Use the weekly report for team check-ins
`/ba-metrics-report` (also auto-generated every Friday at 5pm) gives a feature-by-feature view of iteration counts, template compliance rate, and fix ratios. Useful for spotting patterns — e.g. a specific feature type that consistently needs more amend cycles.

### Track feedback loops per feature
A feedback loop = one amend + re-validate cycle. More than 2 loops on a feature is a signal to investigate root cause — it usually means input materials were thin, or TBC fields were not resolved before story generation.

---

## Publishing

### Review Document History before SA publishes to production
The agent adds a Document History row automatically when publishing to Confluence. Review the version number, date, and "Sections Updated" field before the Solution Architect publishes the draft — this row is the audit trail and should be accurate.

### Provide all Jira ticket keys upfront
If you have multiple CRs and USs to publish to Jira, list all ticket keys at once:

```
Publish to DTTP25-1234, DTTP25-1235, and DTTP25-1236.
```

This is faster than publishing one ticket at a time and lets the agent confirm story-to-ticket mapping in a single step.

### Use sandbox Confluence for unfamiliar features
If this is your first time publishing a feature type you haven't done before, publish to the Confluence sandbox first. Verify the page structure and Document History look correct before publishing to the production space.
