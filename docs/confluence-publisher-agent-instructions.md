# Confluence Publisher Agent — Instructions Reference

This document lists all instructions embedded in the BA `confluence-publisher` agent and maps them to what an SA publisher agent would need.

---

## Instructions in the BA confluence-publisher

| # | Instruction | Category |
|---|---|---|
| 1 | Only update BA-owned sections — never overwrite SA sections | Boundary rule |
| 2 | Always save as draft (v2 API, `status: "draft"`, `version: 1`) | Save rule |
| 3 | Never create, delete, or publish a page | Boundary rule |
| 4 | Fetch current page — record version, status, body | Operational |
| 5 | Check for concurrent edit lock before proceeding | Operational |
| 6 | Extract SA-owned sections verbatim from current page | Protection rule |
| 7 | Preserve all `ac:` / `ri:` macros verbatim in original position | Macro rule |
| 8 | Append new Document History row — never edit existing rows | Document History rule |
| 9 | Date in Document History uses `<time datetime="YYYY-MM-DD" />` macro | Formatting rule |
| 10 | All URLs must be hyperlinked `<a href="URL">display text</a>` | Formatting rule |
| 11 | Assemble page in correct section order (11 sections) | Structure rule |
| 12 | Confirm with user before writing | Safety rule |
| 13 | Verify draft saved and report result | Operational |

---

## Section Order (11 sections)

| # | Section | Owner |
|---|---|---|
| 1 | Document History | BA |
| 2 | Reference Documentation | BA |
| 3 | Feature Summary | BA |
| 4 | Business Requirements | BA |
| 5 | Use Cases | BA |
| 6 | Solution Overview | SA |
| 7 | Involved Interfaces | SA |
| 8 | Sequence Diagrams | SA |
| 9 | Non-Functional Requirements | BA |
| 10 | Monitoring and Alerting Guidelines | SA |
| 11 | Test Scenarios & Acceptance Criteria | BA |

---

## Instructions the SA publisher agent must inherit

All 13 instructions above apply unchanged — only the boundary and protection rules are reversed.

| Rule | BA publisher | SA publisher |
|---|---|---|
| Sections it **may update** | Reference Documentation, Feature Summary, Business Requirements, Use Cases, Non-Functional Requirements, Test Scenarios & Acceptance Criteria | Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring and Alerting Guidelines |
| Sections it **must never touch** | Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring and Alerting Guidelines | Reference Documentation, Feature Summary, Business Requirements, Use Cases, Non-Functional Requirements, Test Scenarios & Acceptance Criteria |
| Document History | Append new row only — never edit existing rows | Append new row only — never edit existing rows |
| Always save as draft | Yes — v2 API, `status: "draft"`, `version: 1` | Yes — v2 API, `status: "draft"`, `version: 1` |
| Preserve all `ac:` / `ri:` macros | Yes | Yes |
| Date macro in Document History | `<time datetime="YYYY-MM-DD" />` | `<time datetime="YYYY-MM-DD" />` |
| All URLs hyperlinked | Yes | Yes |
| Edit lock check before writing | Yes | Yes |
| Confirm with user before writing | Yes | Yes |
| Never create, delete, or publish | Yes | Yes |

---

## Document History Row Format (both agents)

| Field | Rule |
|---|---|
| VERSION | Previous highest version number + 1 |
| AUTHOR(S) | Name of the author invoking the agent |
| DATE | Confluence date macro: `<time datetime="YYYY-MM-DD" />` |
| REMARKS | Short summary of sections updated |
| STATUS | Draft |
| TICKETS | Blank unless explicitly provided |

---

## Draft Save — API Details

Use the Confluence **v2 API** for saving drafts on this tenant. The v1 API does not support drafts on published pages.

| Field | Value |
|---|---|
| Method | PUT |
| Endpoint | `/wiki/api/v2/pages/{id}` |
| status | `"draft"` — never `"current"` or `"published"` |
| version.number | `1` — always 1 for drafts, independent of published version |
| body.storage.representation | `"storage"` |
| Published page | Remains untouched — a human must manually publish the draft in Confluence |
