# MSC Mule BA Agent — Knowledge Base

## Project Context

**Client:** MSC Cruises (Italy) — large cruise operator  
**Team:** EINT (Enterprise Integration) team at EPAM  
**Platform:** MuleSoft Anypoint + Confluence (msccruises.atlassian.net)  
**AI Platform:** Codemie (EPAM internal)  
**Program:** DTTP — Digital Transformation Program  

---

## What We're Building

AI agent that assists Business Analysts in producing BA documentation for the MSC MuleSoft integration program.

The agent helps generate and structure:
- **Functional Specifications** — full 9-section structured spec documents from raw inputs (IAs, Miro boards, JIRA tickets, pasted text)
- **User Stories** — Jira-ready US stories for new interfaces
- **Change Requests** — Jira-ready CR stories for changes to existing interfaces

---

## Available Agents

### functional-spec-generator
**Location:** `C:\Users\Sarah_Suda\functional-spec-generator`  
**Agent file:** `.claude\agents\functional-spec-generator.md`  
**Description:** Generates a structured Functional Specification document from raw input materials such as pasted text, interface agreements, Miro board URLs, JIRA tickets, or file paths.  
**Output:** `.docx` Word document saved to `C:\Users\Sarah_Suda\functional-spec-generator\output\`  
**Invoke when:** User wants to create a functional spec or process source documents into a spec.

**Accepts:**
- Pasted text (Confluence, Word, email, JIRA, chat)
- File paths (reads via Read tool)
- Miro board URLs (fetches via WebFetch)
- Interface Agreements (IAs)
- JIRA tickets or epics

**Output template — 9 sections:**

| Section | Title |
|---|---|
| 1 | Document Header |
| 2 | Document History |
| 3 | Feature Summary + Reference Documentation |
| 4 | Solution Scope (Overview, User Flow, Business Rules, Integrations, Post-Behaviour) |
| 5 | Functional Requirements / Use Cases |
| 6 | High-Level Impacts (one subsection per interface) |
| 7 | In Scope (JIRA tickets by system) |
| 8 | Test Scenarios |
| 9 | Non-Functional Requirements |

**Key rules:**
- Never invent content — gaps marked as `[TO BE CONFIRMED]`
- Preserve all IDs exactly (INT118, MDTTPU-877, etc.)
- Process steps → numbered lists; Business rules → bulleted lists
- Tables mandatory for: document history, reference docs, use case, test scenarios, NFRs
- Inferred content marked inline with `*(inferred)*`

---

### ba-story-generator
**Location:** `C:\Users\Sarah_Suda\ba-story-generator`  
**Agent file:** `.claude\agents\ba-story-generator.md`  
**Description:** Generates Jira-ready BA stories (Change Requests and User Stories) from a functional specification file (`.txt` or `.pdf`).  
**Output:** Markdown file saved to `C:\Users\Sarah_Suda\ba-story-generator\output\`  
**Invoke when:** User wants to generate BA stories or process a spec file into CRs and/or User Stories.

**Story types:**
- `CR` / Change Request → changes to existing interfaces
- `US` / User Story → new interfaces
- Auto-detect → reads spec and determines type automatically

**Splitting logic:**
- **ADF interfaces** (e.g. ADF108) → always excluded, owned by another team
- **New interfaces** → one individual User Story each, never grouped
- **Existing interface changes** → group CRs by same change detail or same logical feature

**CR template fields:** Summary, Change Scope, Rationale, Resources (links), Acceptance Criteria (BDD Given/When/Then)

**US template fields:** Summary, User Story Statement, Interface Name, Purpose, Users, Use Cases, Functionality (Auth / Happy Path / Alternative Paths / Error Scenarios), Documentation, Acceptance Criteria (BDD)

---

## Templates

Stored in: `knowledge\templates\`

| Template | File | Use For |
|---|---|---|
| Functional Specification | `functional_specification_template.html` | Full 9-section spec document |
| User Story | `user_story_template.html` | New interface stories |
| Change Request | `change_request_template.html` | Changes to existing interfaces |

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
