# Recommendations & Best Practices

Lessons from 6 rounds of production testing. Read this before your first real interface.

---

## Before You Start Any Interface

### Always run /import-ia first
Before generating any pages, run `/import-ia` with the IA page ID. It shows:
- Exact field counts (verify these match what you see in Confluence)
- Headers found (check none are blocked/hallucinated)
- Downstream systems (if 2+ → you'll need 2+ SAPI pages)
- Deep nesting warnings (fields you'd otherwise miss)

This 30-second check prevents 90% of generation issues.

### Confirm field counts before generation
After `/import-ia`, Claude shows "Found 87 request fields, 64 response fields." 
Open the actual IA in Confluence and count — or spot-check 10 fields. 
If the counts diverge significantly, use `confluence_get_markdown` to inspect manually before proceeding.

---

## During Generation

### One page at a time — don't rush
The tool generates pages sequentially on purpose. Review each preview carefully before approving:
- MUL: check every field in Request Body and Response Body sections
- EAPI: verify all request fields are mapped, no extra headers
- PAPI: check the Overall Mapping section — it must have one row per IA field
- SAPI: confirm it covers only ONE downstream system's endpoint

### Use /preview before every publish
The preview renders the Confluence HTML in a browser panel. Issues visible in preview:
- Tables that don't render (malformed HTML)
- Missing sections
- Obvious hallucinated content
- Layout problems

Takes 10 seconds. Worth it every time.

### Validate immediately after generation
Right after all 4 pages are created, run `/validate` with all page IDs and the IA.
The coverage report will show exactly what's missing or wrong while the context is fresh.

---

## Known Issues to Watch For

### SAPI scope bleed (most common critical issue)
**Symptom:** SAPI page has 2x expected rows, contains fields from another downstream system.
**Cause:** arch-reader extracted both systems' mappings and sapi-generator included both.
**Fix:** Run `/validate` — it catches this. Then `/update` to remove wrong-system rows.
**Prevention:** After SAPI generation, manually check that every row in Data Mapping maps to `sapi_path` only.

### Hallucinated MSC headers
**Symptom:** MUL or EAPI page contains `MSC-Agency-Id`, `MSC-Market-Code`, etc. not in the IA.
**Cause:** These headers appear in other MSC interfaces, and the model sometimes adds them.
**Fix:** Pre-write hook catches these automatically. If a page already exists with them, `/validate` flags them.
**Prevention:** The pre-write hook blocks them. If you see a hook warning about blocked headers, always check if that header is actually in the IA before overriding.

### Requiredness text simplified
**Symptom:** Long conditional string like "Optional - Required for Lead Passenger if payment type is KLARNA" is shortened to just "Conditional".
**Cause:** The model summarizes rather than copies.
**Fix:** `/validate` catches requiredness mismatches. `/update` to fix with exact IA text.
**Prevention:** After generation, scan the Required column of MUL for any rows that look "too short" for what you know is a conditional field.

### Deep nested response fields missing
**Symptom:** `_warnings[]` has 4 rows but the IA has 16 (missing `_warnings[].causes[].source.name`, etc.)
**Cause:** The model stops extracting at 2 levels of nesting.
**Fix:** `/import-ia` now warns about deep nesting. After generation, manually count `_warnings` rows vs IA.
**Prevention:** If IA has `_warnings[].causes[].source.layer` in the response table — that's 5 levels. Explicitly tell Claude: "The response has deep nesting — make sure to include all levels."

---

## Working With Real Interfaces (Not INT004.4)

### First time with a new interface
1. Run `/import-ia` with the IA page ID
2. Read the output carefully — look for anything unexpected
3. Run `/status` to see what's already done
4. Start with `/generate` only if nothing exists yet
5. If pages exist but are outdated → use `/validate` first to see the gap, then `/propagate`

### When the IA changes mid-design
1. Read the new IA with `/import-ia` — see what changed
2. Run `/diff` between old and new IA (if you have the old page ID)
3. Use `/propagate` to push each changed field across all pages
4. Run `/validate` at the end to confirm consistency

### Multiple downstream systems
If the SA shows 2+ downstream systems (e.g., DTS + Datatrans):
- Expect 2 SAPI pages
- Tell Claude explicitly: "This interface has 2 downstream systems. Generate separate SAPI pages."
- After both SAPIs are created, verify each covers only its own system

---

## Performance Tips

### Provide all URLs upfront
The more context you give at the start, the fewer interruptions. Ideal `/generate` input:
```
Generate INT006. 
IA: [url or page ID]
Functional Spec: [url or page ID]  
Solution Architecture: [url or page ID]
Note: 2 downstream systems — ServiceNow and Salesforce.
```

### Use page IDs not URLs
`4476535093` is faster than the full Confluence URL. Claude accepts both but page IDs are cleaner.

### For incremental work, don't re-read what hasn't changed
If you're only fixing one field in PAPI, just provide the PAPI page ID. Claude will read it directly rather than re-reading all 4 pages.

---

## Quality Checklist Before Promoting to Production

Run through these before moving any page from sandbox to production:

- [ ] `/validate` passes with 0 critical issues
- [ ] All 4 pages created (MUL, EAPI, PAPI, SAPI)
- [ ] SAPI scope: each SAPI covers exactly one downstream system
- [ ] No blocked headers in any page
- [ ] Requiredness text matches IA exactly (especially conditional strings)
- [ ] Deep nested fields present (count `_warnings` rows if applicable)
- [ ] EAPI error section: no `causes[]` arrays
- [ ] PAPI has "Overall Mapping" H3 with one row per IA field
- [ ] Page titles follow MSC naming format
- [ ] Pages are under correct sandbox parent IDs
- [ ] Designer reviewed previews and approved each page

---

## Getting Help

**In Claude Code:** just ask. Examples:
```
"I'm confused about the SAPI scope — help me understand"
"What should the source.name be for DTS errors?"
"Is this page structure correct? [paste HTML snippet]"
```

**Reference implementation:** INT004.4 Klarna pages are in `knowledge/confluence-examples/`. 
These are the gold standard — compare your generated pages against them.

**Design standards:** all 13 official MSC documents are in `knowledge/design-standards/`.
Claude can answer any question from these, or you can read them directly.
