# Booking Group Management

## Splitting Rationale

Two Change Requests are raised for this feature. Each CR maps to a distinct integration stream with a separate Jira ticket, a different source system, and a different downstream target.

- **CR-1** covers the synchronous webform-to-Salesforce interface (INT101): Stream 1 – Group ID on Webform Case. Separate CR because the source is MSC Book, the target is Salesforce, and the change is isolated to INT101 (Jira: MDTTPU-8133).
- **CR-2** consolidates the three DTS-to-CDP Booking Event interfaces (INT024.1, INT100, INT025): Stream 2 – Group booking type in Booking Events. The three interfaces carry exactly the same change — accepting and forwarding the new `GroupType` field from DTS Booking Events to CDP — share a common DTS source event, a common downstream target (CDP), and a single Jira ticket (MDTTPU-6140). Raising three separate CRs would produce near-identical stories with no additional clarity or traceability benefit.

No ADF interfaces are present in the spec.

| Story | Scope | Reason for separation (or consolidation) |
|---|---|---|
| CR-1: INT101 – Add Group ID to Webform Case Creation | INT101 – MSC Book webform to Salesforce Case creation. Accept and forward new optional `groupId` field. | Separate CR: different source system (MSC Book), different target (Salesforce), separate Jira ticket (MDTTPU-8133), synchronous request/response pattern. |
| CR-2: Booking Events – Add GroupType to BookingContext (INT024.1, INT100, INT025) | INT024.1, INT100, INT025 – DTS Booking Events to CDP. Accept and forward new `GroupType` field within BookingContext. | Consolidated CR: identical change across three interfaces (forward `GroupType` from DTS to CDP), same source event, same downstream target, single Jira ticket (MDTTPU-6140). Additive and uniform change across all three interfaces. |

---

## Change Requests

---

Type: CR
Summary: INT101 – Add Group ID field to MSC Book webform case creation
Jira Ticket: MDTTPU-8133
Description:
  Change Scope: Interface INT101 (MSC Book → MuleSoft → Salesforce). MuleSoft changes:
    - Accept the new optional `groupId` field (string, max 255 characters) in the inbound INT101 request payload from MSC Book Help Center, Need Help, and Group Request webforms.
    - Validate: if present, reject requests where `groupId` exceeds 255 characters and return an appropriate error response to MSC Book.
    - Map and forward `groupId` to Salesforce field `groupId__c` on the Case creation request. If absent from the inbound payload, the field is omitted (null) in the outbound Salesforce request.
    - Scope applies to DTP rolled-out markets only (Ireland, UK, DACH, MED+Latam, US). Non-DTP markets route via the existing path unchanged.
    - All existing INT101 behaviour (case creation, agency/customer lookup, caseId response, Genesys routing trigger) is unchanged.

  Rationale: When a Travel Agency submits a Help Center, Need Help, or Group Request form on MSC Book, the Group ID is not captured on the resulting Salesforce Case. Contact centre agents must manually look up the Group ID from DTS, adding handling effort and introducing risk of error. This change closes that gap by passing the `groupId` entered on the form through INT101 to Salesforce, giving agents immediate visibility of the group booking identifier on the Case record without a manual lookup.

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation: IA INT101 – MSC Book Help Center & Need Help Forms: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/3867836498/IA+INT101+-+MSC+Book+-+Help+Center+Need+Help+Forms
    - Confluence Page: TLI-XXX – Booking Group Management: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4800675945/TLI-XXX+-+Booking+Group+Management

Acceptance Criteria (BDD):
  Given a valid INT101 webform request is received from MSC Book for a DTP rolled-out market, and the payload contains a `groupId` value within the permitted 255-character limit
  When MuleSoft INT101 processes the request
  Then MuleSoft forwards the request to Salesforce with `groupId` mapped to `groupId__c` on the Case creation payload, and returns a success response to MSC Book

  Given a valid INT101 webform request is received from MSC Book for a DTP rolled-out market, and the payload does not contain a `groupId` field
  When MuleSoft INT101 processes the request
  Then MuleSoft forwards the request to Salesforce without `groupId__c` (field absent or null), and returns a success response to MSC Book — no error is raised due to the absence of the field

  Given an INT101 webform request is received from MSC Book for a DTP rolled-out market, and the `groupId` value in the payload exceeds 255 characters
  When MuleSoft INT101 attempts to process the request
  Then MuleSoft rejects the request before forwarding to Salesforce and returns an error response to MSC Book identifying `groupId` as invalid due to exceeding the maximum permitted length — no Case is created in Salesforce

  Given a valid INT101 webform request containing a valid `groupId` is received from MSC Book for a DTP rolled-out market, but Salesforce is unavailable
  When MuleSoft INT101 attempts to forward the request to Salesforce and exhausts all configured retries
  Then MuleSoft returns an error response to MSC Book indicating the downstream service is unavailable — no partial Case is created

  Given an INT101 webform request is received from MSC Book for a non-DTP market
  When MuleSoft INT101 processes the request
  Then MuleSoft routes the request via the existing non-DTP path unchanged — if `groupId` is present it is ignored and not forwarded, and existing behaviour is fully preserved

---

Type: CR
Summary: Booking Events – Add GroupType to BookingContext across INT024.1, INT100, INT025
Jira Ticket: MDTTPU-6140
Description:
  Change Scope: Interfaces INT024.1 (Booking Event Subset Legacy Orchestration), INT100 (Booking Profile Orchestration), and INT025 (Booking Event Orchestration) — all receiving DTS Booking Events and publishing to CDP. MuleSoft changes across all three interfaces:
    - Accept the extended DTS Booking Event payload that includes the new optional `GroupType` field within the booking context, once DTS delivers the event extension (delivered — see [MDTTPU-2419](https://smartship.atlassian.net/browse/MDTTPU-2419)).
    - Map and forward `GroupType` to the corresponding field in the CDP target schema for each interface: A007 (INT024.1), A086 (INT100), A087 (INT025).
    - For group bookings (booking type GRP): `GroupType` is present in the DTS event and must be included in the payload forwarded to CDP.
    - For individual bookings (booking type IND): `GroupType` is absent or null in the DTS event. MuleSoft must process the event normally without error and must forward `GroupType` as null in the CDP payload.
    - All existing orchestration logic for each interface is unchanged: event subset filtering and GoldenID enrichment in INT024.1; participant filtering and booking profile generation in INT100; item and participant filtering in INT025.
    - The change is additive and backward-compatible. Existing CDP consumers and other downstream consumers that do not process `GroupType` must not be affected.

  Rationale: DTS Booking Events published to downstream consumers do not currently carry information about whether a booking is a group or individual booking. Downstream systems such as CDP (Adobe Customer Data Platform) cannot distinguish between group and individual bookings for segmentation and marketing activation purposes. This change extends the booking event payload forwarded to CDP to include `GroupType`, enabling CDP and authorised consumers to correctly identify and segment group bookings. The change is additive and has no impact on existing consumers.

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation:
      - IA INT024.1 – Booking Event Subset Legacy Orchestration: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4288413802/IA+INT024.1+-+Booking+Event+Subset+Legacy+Orchestration
      - IA INT100 – Booking Profile Orchestration: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4321804290/IA+INT100+-+Booking+Profile+Orchestration
      - IA INT025 – Booking Event Orchestration: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4322230273/IA+INT025+-+Booking+Event+Orchestration
    - Confluence Page: TLI-XXX – Booking Group Management: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4800675945/TLI-XXX+-+Booking+Group+Management

Acceptance Criteria (BDD):
  Given DTS publishes a booking event for a group booking (type GRP) with `GroupType` populated, and INT024.1 receives the event
  When MuleSoft INT024.1 applies the event subset filter, performs GoldenID enrichment where required, and splits the event per participant
  Then MuleSoft INT024.1 forwards the event to CDP with `GroupType` included in schema A007

  Given DTS publishes a booking event for an individual booking (type IND) without `GroupType`, and INT024.1 receives the event
  When MuleSoft INT024.1 processes the event through the standard orchestration flow
  Then MuleSoft INT024.1 forwards the event to CDP without `GroupType` in the payload — no error is raised and existing orchestration behaviour is unchanged

  Given DTS publishes a booking event for a group booking (type GRP) with `GroupType` populated, and INT100 receives the event subset
  When MuleSoft INT100 applies participant filtering and generates the booking profile per participant
  Then MuleSoft INT100 forwards the booking profile to CDP with `GroupType` included in schema A086

  Given DTS publishes a booking event for an individual booking (type IND) without `GroupType`, and INT100 receives the event subset
  When MuleSoft INT100 processes the event through the standard booking profile orchestration flow
  Then MuleSoft INT100 forwards the booking profile to CDP without `GroupType` — no error is raised and existing orchestration behaviour is unchanged

  Given DTS publishes a booking event for a group booking (type GRP) with `GroupType` populated, and INT025 receives the event subset
  When MuleSoft INT025 applies item and participant filtering
  Then MuleSoft INT025 forwards the event to CDP with `GroupType` included in schema A087

  Given DTS publishes a booking event for an individual booking (type IND) without `GroupType`, and INT025 receives the event subset
  When MuleSoft INT025 processes the event through the standard orchestration flow
  Then MuleSoft INT025 forwards the event to CDP without `GroupType` — no error is raised and existing orchestration behaviour is unchanged

  Given a DTS booking event containing the new `GroupType` field is processed by INT024.1, INT100, or INT025 and forwarded to CDP
  When any existing downstream consumer registered on the same topic receives the event
  Then the existing consumer continues to receive and process the event without error — the change is backward-compatible and no existing consumer integration is broken
