# MSC Mule BA Agent — Knowledge Base

## Project Context

**Client:** MSC Cruises (Italy) — large cruise operator  
**Team:** EINT (Enterprise Integration) team at EPAM  
**Platform:** MuleSoft Anypoint + Confluence (msccruises.atlassian.net) + Jira (msccruises.atlassian.net)  
**AI Platform:** Codemie (EPAM internal) / Claude Code  
**Program:** DTTP — Digital Transformation Program  
**Project location:** `C:\Users\[your_user]\MSC- Mule BA Agent`  

---

## What We're Building

AI-assisted BA toolkit for the MSC Cruises MuleSoft Integration team. The BA is embedded in the MuleSoft team and receives requirements from the broader DTTP programme. The toolkit translates those requirements into structured documentation scoped to what the MuleSoft team needs to deliver.

The toolkit generates and structures:
- **Functional Specifications** — structured HTML spec documents based on the MSC Mulesoft Requirements Template, covering the overall solution with NFRs and test scenarios scoped to the API layer
- **User Stories** — Jira-ready US stories for new interfaces
- **Change Requests** — Jira-ready CR stories for changes to existing interfaces
- **Validation reports** — quality checks flagging gaps, vague ACs, ADF slippage, and wrong CR/US splits
- **Confluence drafts** — updates to existing Confluence requirements pages (BA sections only, always saved as draft)
- **Jira updates** — updates to existing Jira ticket descriptions and acceptance criteria

---

## Pipeline

```
Input materials
      │
      ▼
functional-spec-generator  →  output/specs/functional_spec_[name].html
      │
      ▼
ba-story-generator         →  output/stories/[name].md
      │
      ▼
ba-validator               →  output/validation/validation-report.md
      │
      ▼
ba-amend (skill)           →  fixes applied interactively to specs and stories
      │
      ├──→ jira-publisher        →  updates existing Jira tickets
      └──→ confluence-publisher  →  saves draft to existing Confluence page
```

Orchestrated end-to-end via the `/ba-workflow` skill.

---

## Available Agents

### functional-spec-generator
**Agent file:** `.claude\agents\functional-spec-generator.md`  
**Output:** `output\specs\functional_spec_[feature_name].html`  
**Invoke when:** User wants to create a functional spec from raw input materials.

**Accepts:** Pasted text, file paths, Confluence page URLs, Miro board URLs, Jira tickets

**Output template — based on MSC Mulesoft Requirements Template:**

| Section | Scope |
|---|---|
| Document History | Version, Author, Date, Remarks, Status, Tickets |
| Reference Documentation | Links to source documents |
| Feature Summary | Overall solution context — business problem and value |
| Business Requirements | Solution-level user stories (As a… I want… So that…) — not API-specific |
| Use Cases | Functional solution flows — names the MuleSoft API called in Functionality Expected column |
| Non-Functional Requirements | **API-specific** — SLA, security, throughput, error handling |
| Test Scenarios & Acceptance Criteria | **API-specific** — HTTP request/response, status codes, error scenarios |

**Key rules:**
- Never invent content — gaps marked as `[TO BE CONFIRMED]`
- Business Requirements and Use Cases are solution-level (not API-specific)
- NFRs and Test Scenarios are scoped to the MuleSoft API layer
- Use Cases name the MuleSoft API called in the Functionality Expected column
- Output is a self-contained HTML file

---

### ba-story-generator
**Agent file:** `.claude\agents\ba-story-generator.md`  
**Input:** HTML spec from `output\specs\`  
**Output:** `output\stories\[feature_name].md`  
**Invoke when:** User wants to generate Jira-ready BA stories from a functional spec.

**Story types:**
- `CR` / Change Request → changes to existing interfaces
- `US` / User Story → new interfaces
- Auto-detect → reads spec and determines type automatically

**Splitting logic:**
- **ADF interfaces** (e.g. ADF108) → always excluded, owned by another team
- **New interfaces** → one individual User Story each, never grouped
- **Same change across multiple interfaces** → one CR
- **Multiple changes under same feature** → one CR
- **Different features** → separate CRs

**CR template fields:** Summary, Change Scope, Rationale, Resources (links), Acceptance Criteria (BDD)

**US template fields:** Summary, User Story Statement, Interface Name, Purpose, Users, Use Cases, Functionality (Auth / Happy Path / Alternative Paths / Error Scenarios), Documentation, Acceptance Criteria (BDD)

---

### ba-validator
**Agent file:** `.claude\agents\ba-validator.md`  
**Input:** All files in `output\specs\` and `output\stories\`  
**Output:** `output\validation\validation-report.md`  
**Invoke when:** User wants to validate quality of generated specs and stories before publishing.

**Validation rules:**

| Rule | Severity | Checks |
|---|---|---|
| 1 — TBC fields | BLOCKER | Any `[TO BE CONFIRMED]` still present |
| 2 — Vague ACs | WARNING | Missing Given/When/Then, no measurable outcome, happy-path only |
| 3 — Missing doc links | INFO | Blank Confluence/API doc/HLA fields |
| 4 — ADF slippage | BLOCKER | ADF-prefixed interfaces in any story |
| 5 — Wrong CR/US split | BLOCKER | New interface given CR, existing change given US, over/under-splitting |
| 6 — No system owner | WARNING | Users field blank, Change Scope missing owning system |
| 7 — Untested use cases | WARNING | UC-IDs in spec with no matching test scenario or story AC |
| 8 — Uncovered BRs | INFO | Business requirements with no traceable story |

---

### jira-publisher
**Agent file:** `.claude\agents\jira-publisher.md`  
**Input:** Jira ticket key/URL + story from `output\stories\`  
**MCP tools:** `jira_get_issue`, `jira_update_issue` only  
**Invoke when:** User wants to push a generated story to an existing Jira ticket.

**Rules:**
- Updates description and acceptance criteria fields only
- Never creates, deletes, or transitions tickets
- Shows a preview and asks for confirmation before writing
- Verifies the update by re-fetching the ticket after writing

---

### confluence-publisher
**Agent file:** `.claude\agents\confluence-publisher.md`  
**Input:** Confluence page URL + spec from `output\specs\`  
**MCP tools:** `confluence_get_page`, `confluence_update_page` only  
**Invoke when:** User wants to push a generated spec to an existing Confluence requirements page.

**Rules:**
- Always saves as `draft` — never publishes directly
- Never creates or deletes pages
- Checks for concurrent edit lock before writing
- Appends a new Document History row (Sarah Suda, today's date, sections updated)
- **Protected sections — never overwritten:** Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring and Alerting Guidelines
- Shows a preview and asks for confirmation before writing

---

## Skills (Slash Commands)

### /ba-workflow
**File:** `.claude\commands\ba-workflow.md`  
**Description:** Main orchestrator. Presents a menu and chains the correct agents in order.

| Option | Pipeline |
|---|---|
| 1 — Spec only | functional-spec-generator |
| 2 — Stories only | ba-story-generator |
| 3 — Full end-to-end | spec → stories → validate → amend → publish |
| 4 — Validate and publish | validate → amend → publish |

### /ba-amend
**File:** `.claude\commands\ba-amend.md`  
**Description:** Reads `output\validation\validation-report.md` and presents each flag one at a time. User chooses: Accept fix / Edit manually / Skip. Applies changes directly to the relevant file.

---

## MCP Server

**Location:** `C:\Users\[your_user]\MSC- Mule BA Agent\mcp\`  
**Start command:** `uv run msc-mcp-server` (run from the `mcp\` folder)  
**Endpoint:** `http://localhost:8080/mcp`  
**Credentials:** `mcp\.env` (see `docs\SETUP.md`)

The MCP server must be running for jira-publisher and confluence-publisher to function.

---

## Output Folder Structure

```
output/
├── specs/
│   └── functional_spec_[feature_name].html   ← generated functional specification
├── stories/
│   └── [feature_name].md                     ← Jira-ready CRs and User Stories
└── validation/
    └── validation-report.md                  ← flags, severities, and suggested fixes
```

---

## Templates

Stored in: `knowledge\templates\`

| Template | File | Use For |
|---|---|---|
| User Story | `user_story_template.html` | New interface stories |
| Mulesoft Requirements | `Mulesoft+Requirements+Template.doc` | Source template for functional spec structure |

---

## Input Documents

### Interface Agreement (IA)
The source of truth for field names, types, required markers, and error scenarios.  
**Rule:** Always use field names exactly as written in the IA — never use business/functional naming.

### Functional Specification
Adds business context — what the feature does, business rules, edge cases, user flows.  
Used for: scope and purpose sections, description texts, use case table.

### Solution Architecture
Contains orchestration logic (what calls what and in what order), downstream system mappings.  
Used for: system integrations section, high-level impacts per interface.

---

## Naming Conventions

### Interface IDs
Format: `INT{number}.{subversion}` — e.g. `INT004.4`, `INT006`, `INT007.2`  
ADF prefix (e.g. `ADF108`) → always owned by another team, exclude from stories.

### Story title format
- CR: concise Jira-style title, max 10 words
- US: concise Jira-style title, max 12 words

### Output file naming
- Functional spec: `functional_spec_[feature_name_snake_case].docx`
- BA stories: `[initiative-slug].md`

### Required field values (exact — never paraphrase)
`Required` / `Optional` / `Conditional`

---

## Project Background — DTTP

The **DTTP (Digital Transformation Program)** is MSC's initiative to replace legacy systems with a modern digital stack, covering the B2C website, booking funnel, web forms, and private customer area.

### Legacy Systems Being Replaced

| System | Purpose |
|---|---|
| Marketo | Marketing automation |
| Sitecore | B2C website |
| Siebel | Call centre CRM / customer master record |

### New Systems

| System | Purpose |
|---|---|
| Adobe AEM | Website content management |
| Adobe CDP | Customer data platform and profile building |
| Adobe Journey Optimizer (AJO) | Transactional emails and customer journeys |
| Salesforce (Service Cloud) | CRM — customer relationships and case management |

---

## Rollout Timeline

| Market | Go-Live | Notes |
|---|---|---|
| Ireland | 2024 | MVP — booking funnel and web forms |
| UK | March 2025 | Additional functionality beyond Ireland MVP |
| DACH | October 2025 | Further additional functionality |
| MED (France, Italy, Spain) + Latam | May 2026 | Currently being deployed |
| myMSC Private Area | June 2026 | Customer login, bookings, onboard services, Voyager Club |
| US | September 2026 | Including additional features |
| Additional markets | June–September 2026 | Booking funnel and myArea rollouts |

---

## Key Systems

| System | Role | Notes |
|---|---|---|
| Adobe AEM | Website content management | Content editors control website areas |
| DTS | Reservation system | Core system for cruise bookings, packages, prices, extras |
| Amadeus | Flight bookings | Used for flight components within cruise packages |
| Data Trans | Payment provider | Handles card details and payment transactions |
| Customer Hub (CHUB) | Customer master record | Ingests data from multiple systems for a full customer view. Not designed for real-time interactions — updates can be delayed. |
| Siebel (CRM as-is) | Legacy customer master / loyalty | Still in use for loyalty programme and other functionalities |
| Salesforce CRM | New CRM | Manages customer relationships and cases from web forms |
| Genesys | Call centre telephony | Handles inbound/outbound calls, integrated with Salesforce |
| CDP + AJO | Profiles and communications | Builds customer profiles and sends transactional emails |
| Algolia | Cruise search | Powers the website cruise search |
| MuleSoft | Integration layer | All website-to-backend API calls route through MuleSoft |
| Akamai | Web application firewall | All requests from website to MuleSoft pass through Akamai |
| Azure App | Transformation layer | Enriches DTS data for Algolia (itineraries, port stops) |

---

## Website Integration Architecture

- **Security:** All requests from the website to MuleSoft pass through **Akamai** (web application firewall)
- **Authentication:** MVP website is unauthenticated — APIs are public-facing
- **Private Area (myMSC):** Authenticated area launching June 2026 — customers view bookings, purchase onboard services, manage account and Voyager Club card

---

## Booking Process

1. User searches for cruises via **Algolia**
2. Booking initiated through **MuleSoft APIs**
3. User selects cabin type — mandatory and optional services included in the package
4. Data Trans generates a transaction ID including the total amount
5. Website sends card details directly to **Data Trans** — MuleSoft does not handle raw card data
6. Data Trans authorises payment with card issuer and returns a transaction reference
7. MuleSoft uses the reference to record the payment in **DTS**
8. Booking status changes from `OPT` (option) to `BKD` (booked)

---

## System Processes

### B2C Website — Adobe AEM

| Process | Description |
|---|---|
| Search | Uses Algolia for searching and filtering cruise options, with data enrichment from the transformation layer and DTS |
| Content Management | AEM allows content editors to manage and enrich website content, including overriding descriptions from DTS |
| Booking Funnel | Customers search, select packages and cabins, add optional services, and complete a booking |
| Web Forms | Customers contact MSC via web forms; submissions are processed into cases in Salesforce |
| Payment Processing | Facilitates secure payment transactions through Data Trans |
| Customer Data Submission | Sends customer data to CDP and AJO for profiling and marketing |

---

### MuleSoft — Integration & API Platform

| Process | Description |
|---|---|
| API Gateway | Acts as intermediary for all website-to-backend interactions |
| Data Integration | Retrieves and integrates data from DTS, Customer Hub, and Salesforce; enriches and validates before returning to website |
| Booking Management | Interacts with DTS to retrieve cruise details, prices, and execute bookings |
| Payment Processing | Coordinates with Data Trans to handle payment authorisations |
| Customer Data Handling | Searches for and creates customer records in Customer Hub |
| Case Creation | Integrates with Salesforce to create cases from web form submissions |

---

### Datatrans — Payment Gateway

| Process | Description |
|---|---|
| Payment Setup | Generates a transaction ID including the total amount when customer proceeds to payment |
| Card Details Submission | Website sends card details directly to Data Trans; MuleSoft does not interact with raw card data |
| Authorisation | Data Trans checks card details with the card issuer to authorise the payment |
| Transaction Reference | Returns a reference used by MuleSoft to confirm and record the payment |
| Booking Confirmation | MuleSoft records the payment in DTS and updates booking status from `OPT` to `BKD` |

---

### Customer Hub (CHUB) — Customer Master Data

| Process | Description |
|---|---|
| Data Ingestion | Ingests customer data from the website, call centres, travel agents, and onboard ship systems |
| Customer Record Search | Attempts to match submitted details to an exact existing customer record |
| New Record Creation | Creates a new customer record if no exact match is found (matched on first name, last name, date of birth, email) |
| Batch Processing | Many processes rely on batch processing — updates can take 15 minutes or more to reflect |

**Match and Merge (runs every ~15 minutes)**

| Rule | Detail |
|---|---|
| Exact match | First name + last name + date of birth → same customer |
| Combination match | Phone, email, and other fields used to catch near-duplicates |
| Merging | Duplicates merged into a single consolidated record taking the best details from each |

---

### Siebel — CRM (As-Is)

| Process | Description |
|---|---|
| Customer Record Management | Legacy customer master; still synchronises records to Customer Hub |
| Website Backend | Backend for the private area — manages web account records and links to bookings |
| Loyalty Card System | Master record for the MSC loyalty card programme |
| E-Coupons | Manages the e-coupon system |

---

### Salesforce — CRM (To-Be)

**Entities:**

| Entity | Description |
|---|---|
| Case | Created each time an agent needs to act, e.g. when a web form is submitted |
| Opportunity | Created when a customer expresses interest in buying a cruise; agent books in DTS |
| Quote | Created from booking update events from DTS; holds booking information for agent-created bookings |
| Asset | Extra data from CHUB about customers, including all booking history regardless of channel |

**Web form to case flow:**
1. Customer submits a web form
2. MuleSoft searches Customer Hub for a matching customer record
3. If exactly one match is found, the **Golden ID** (unique CHUB customer identifier) is retrieved
4. Golden ID is used to create the case in Salesforce
5. For callback requests, MuleSoft creates the case in Salesforce and schedules the call in Genesys

---

### Genesys — Computer Telephony Integration (CTI)

| Process | Description |
|---|---|
| Inbound & Outbound Calls | Manages all call centre calls |
| Call Scheduling | Web form callback requests → MuleSoft creates Salesforce case and schedules call in Genesys |
| Agent Notifications | At scheduled time, Genesys prompts agent with customer phone number and case details |

---

### Adobe CDP & AJO — Marketing Automation

| Process | Description |
|---|---|
| Data Submission | Website data (bookings, web forms) sent to CDP to build customer profiles |
| Customer Identification | Golden ID required to send data to CDP or AJO; CHUB searched and record created if needed |
| Profile Building | CDP builds detailed customer profiles from website and CHUB data |
| Transactional Emails | AJO sends booking confirmation emails after successful bookings |
| Marketing Campaigns | CDP data enables targeted campaigns based on browsing and booking activity |

---

### Algolia — Search as a Service

| Process | Description |
|---|---|
| Search Engine | Powers cruise search and filtering on the website |
| Data Enrichment | Transformation layer enriches DTS data (itineraries, port stops) before feeding into Algolia |
| Filtering | Supports filtering by departure port and other cruise attributes |

---

### Azure App — Transformation Layer

| Process | Description |
|---|---|
| Data Enrichment | Enriches raw DTS data with cruise itineraries and port stops |
| Algolia Integration | Feeds enriched data into Algolia to support accurate search results |

---

## Glossary

| Term | Acronym | Description |
|---|---|---|
| Marketing Automation | MA | Functional area / team. Previously Marketo, today replaced by Adobe CDP and AJO |
| Sales & Services | S&S | Functional area / team. Previously Siebel, today replaced in parts by Salesforce |
| Adobe Journey Optimiser | AJO | Orchestrates and delivers personalised customer engagement across all channels |
| Adobe Experience Manager | AEM | Manages website content; allows content editors to control parts of the website |
| Adobe Customer Data Platform | CDP | Collects, normalises, and unifies customer data into real-time profiles for personalised marketing |
| Akamai | — | Web application firewall. All requests from the website to MuleSoft pass through Akamai |
| Customer Hub | CHUB | System of record for the customer. Ingests data from various systems for a comprehensive customer view |
| DTS | DTS | The reservation system. Core system for booking cruises, managing packages, prices, and items |
| Booking Funnel | — | The part of the customer journey where the customer selects packages and cabin types after choosing a cruise |
| Data Trans | — | Payment gateway provider that processes payments and handles transactions |
| Private Area / myMSC Area | — | Authenticated section of the website where customers log in to manage bookings and onboard services |
| Golden ID | — | Unique customer identifier in Customer Hub, used to link records across Salesforce, CDP, and AJO |
| Digital Transformation Program | DTTP | MSC's program to replace Marketo, Sitecore, and Siebel with a modern Adobe + Salesforce stack |
| Interface Agreement | IA | Integration contract defining fields, types, auth, and error scenarios for a MuleSoft interface |
| OPT | OPT | Booking status: option — payment not yet confirmed |
| BKD | BKD | Booking status: booked — payment confirmed |
