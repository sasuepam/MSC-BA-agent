# What This Assistant Can Do

A complete picture of capabilities, with examples of what to type.

---

## 1. Generate Full Page Sets (New Endpoint)

**The big one.** From IA + Functional Spec + Solution Architecture → all 4 Confluence pages.

```
"Generate pages for INT006. Here's the IA: [url], Functional Spec: [url], SA: [url]"
"Create MUL, EAPI, PAPI, and SAPI for the new specialty restaurants endpoint"
"New endpoint: POST /bookings/{id}/hold, here's the IA page ID: 4502819234"
```

What happens:
1. Reads all source pages (deterministic extraction — no hallucination)
2. Shows you what was found: field counts, headers, downstream systems
3. Generates each page one at a time, showing you a preview
4. You approve → publishes to sandbox Confluence
5. Runs coverage check after each page
6. Final summary with all URLs and quality report

Time savings: **6-10 hours → 1-2 hours**

---

## 2. Add or Change Fields

**Daily bread and butter.** No need to regenerate the whole page.

```
"Add field couponCode to the MUL page. Here it is: [page_id]"
"Change passengerInformation.adults.total to Optional in INT004.4"
"Fix the description for returnPath in the PAPI page"
"Add 3 new fields from the updated IA to MUL and EAPI"
```

What happens:
1. Reads current page
2. Reads IA to confirm exact field name, type, requiredness
3. Shows before/after diff
4. You approve → applies the change
5. Asks if you want to propagate to other pages

---

## 3. Propagate Changes Across All Pages

**When the IA changes.** Push the change consistently to all layers.

```
"The IA changed couponCode to Required. Update all pages."
"Propagate: returnPath field added to IA. Push to MUL, EAPI, PAPI."
"Field renamed from bookingRef to reservationId everywhere"
```

What happens:
1. Reads all 4 pages
2. Computes the right change for each page's column format (MUL vs EAPI vs PAPI vs SAPI use different table layouts)
3. Shows diff for every page before touching anything
4. Applies changes one by one, with confirmation
5. Validates consistency after all changes

---

## 4. Validate Consistency

**Quality gate.** Catch issues before they reach developers.

```
"Validate INT004.4 — check all pages against the IA"
"Are MUL and EAPI consistent? MUL: [id], EAPI: [id], IA: [id]"
"Check for hallucinated fields in this page"
```

Output: structured report with severity levels (critical / warning / passing).

Checks:
- Field presence across all pages vs IA
- Requiredness exact text match
- Type consistency
- Hallucinated headers (MSC-Agency-Id etc.)
- Known field name traps (promotionalCode vs couponCode)
- SAPI scope (no cross-system fields)
- Nested field completeness (3+ levels)

---

## 5. Generate RAML Specifications

**Steps 2 and 5 of the design process.**

```
"Generate RAML for the EAPI of INT004.4"
"Create RAML specs for all three layers of INT006"
```

Generates full RAML 1.0 file set:
- `api.raml` — main spec with traits and endpoints
- `dataTypes/` — typed request/response objects
- `examples/` — named example files
- `traits/correlatable.raml` — MSC-Conversation-ID trait
- `CHANGELOG.raml` — mandatory release notes

Follows MSC RAML Design Guidelines and references MSC Exchange libraries.

---

## 6. Generate HLA Page

**Step 3 of the design process.**

```
"Create the HLA page for INT004.4. EAPI: [id], PAPI: [id], SAPI: [id]"
"Update the HLA with the sequence diagram for INT006"
```

Generates:
- Scope description
- Key information table (links to all pages)
- Architecture diagram placeholder
- PlantUML sequence diagram (consumer → EAPI → PAPI → SAPI → downstream)
- Alerts and monitoring specifications
- Internal APIs table

---

## 7. Create Jira Subtasks

**Step 6 of the design process.**

```
"Create Jira subtasks for INT004.4 under DTTP-1234"
"Generate implementation tickets from the INT006 design"
```

Creates one subtask per deliverable:
- EAPI implementation (with acceptance criteria from design)
- PAPI implementation (with orchestration steps)
- SAPI per downstream system (with field mappings and error codes)
- RAML specs task
- HLA update task

---

## 8. Answer Design Questions

**Instant answers.** No Confluence browsing needed.

```
"What is couponCode? What type is it and where should it appear?"
"Can EAPI expose downstream error causes?"
"What's the correct format for MSC-Country-Code?"
"Which source.name should I use for Datatrans errors?"
"What's the difference between PAPI and SAPI?"
"Should this field be in SAPI if it's passed through to Datatrans?"
"What ISO format should I use for dates?"
```

Claude reads the IA page for field-specific questions. For convention questions, cites the relevant design standard document.

---

## 9. Review Design Quality

```
"Review this PAPI page against MSC design standards"
"Does this EAPI follow conventions?"
"Check the error structure in this page"
```

Checks against all 13 MSC design standard documents:
- Naming conventions (`dtt-{consumer}-{domain}-{layer}`)
- Header correctness
- Data type standards (ISO formats, E.164 phones, etc.)
- Error response structure (MSC format, source.layer, source.name)
- Layer-specific rules (EAPI no causes, SAPI single system, etc.)

---

## 10. Design Status Dashboard

```
"/status INT004.4"
"What's done on INT006?"
"Which design steps are complete for the specialty restaurants interface?"
```

Shows progress against the 6-step MSC design process:
- Step 1: MUL page (with field coverage %)
- Step 2: EAPI RAML
- Step 3: HLA page
- Step 4: EAPI/PAPI/SAPI pages
- Step 5: PAPI/SAPI RAML
- Step 6: Jira subtasks

---

## What It Does NOT Do

- **Write to production without explicit confirmation** — always drafts to sandbox first
- **Guess field names** — always reads IA before generating or answering
- **Add headers not in the IA** — strict blocked-header list enforced automatically
- **Mix downstream systems in SAPI** — one system per SAPI, always
- **Simplify requiredness text** — copies exact conditional strings from IA
- **Skip fields** — row count check before every publish
