# Webform US – INT103 & INT101: Agency Email Address and Representative Code

## Splitting Rationale

Both requirements are delivered as a single CR because:
- They are part of the same Webform US initiative scoped to the US market
- Both changes are additive-only (new optional fields, no transformation, no impact on existing behaviour)
- A single Jira ticket (MDTTPU-6137) covers the full scope
- Neither change is dependent on the other being released separately

| Item | Decision |
|------|----------|
| Number of CRs | 1 |
| Interfaces covered | INT103 (MSC Book Status Match, B2B Status Match), INT101 (MSC Book Help Center & Need Help Forms, B2B Contact Requests) |
| User Stories | None — no new interfaces; all changes are to existing interfaces |

---

Type: CR
Summary: Webform US – Add Agency Email Address and Representative Code to INT103 and INT101
Jira Ticket: MDTTPU-6137
Description:
  Change Scope:
    - Add optional field `agencyEmail__c` (Agency Email Address) to the Salesforce Case payload for INT103 – MSC Book Status Match and INT103 – B2B Status Match
    - Add optional field `agencyRepresentativeId__c` (Representative Code) to the Salesforce Case payload for INT103 – MSC Book Status Match and INT103 – B2B Status Match
    - Add optional field `agencyRepresentativeId__c` (Representative Code) to the Salesforce Case payload for INT101 – MSC Book Help Center & Need Help Forms and INT101 – B2B Contact Requests
    - Both fields are optional; if absent, existing interface behaviour is unchanged
    - `agencyRepresentativeId__c` is a pass-through field — no transformation required
    - `agencyEmail__c` is used by Salesforce to send a completion notification email to the Travel Agency; the email send itself is handled entirely within Salesforce
    - All changes are scoped to the US market only

  Rationale:
    - Travel Agencies submitting Status Match requests via MSCBook currently receive no confirmation when the status match is completed for their client. Capturing the agency email address on the form and passing it via INT103 enables Salesforce to send a near-real-time notification email directly to the agency representative.
    - The Representative Code field is being added to both the Status Match form (INT103) and the Help Center / Need Help forms (INT101) as an optional pass-through for future use; no immediate business process depends on it.

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation:
      - IA INT103 – MSC Book Status Match & B2B Status Match: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/3585703967
      - IA INT101 – MSC Book Help Center & Need Help Forms / B2B Contact Requests: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/3867836498
    - Confluence Page: MS: Webform for US: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/5233475594/MS+Webform+for+US
    - TLI Document: TLI-XXX – Webform US: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4741922817/TLI-XXX+-+Webform+US

Acceptance Criteria (BDD):
  Given a Travel Agency submits a Status Match form with an Agency Email Address and a Representative Code
  When INT103 processes the payload
  Then `agencyEmail__c` and `agencyRepresentativeId__c` are present in the Salesforce Case with the submitted values
  And no transformation is applied to either field

  Given a Travel Agency submits a Status Match form without an Agency Email Address
  When INT103 processes the payload
  Then the request is processed successfully without error
  And no agency notification email is sent by Salesforce

  Given a Travel Agency submits a Help Center or Need Help form with a Representative Code
  When INT101 processes the payload
  Then `agencyRepresentativeId__c` is present in the Salesforce Case with the submitted value
  And no transformation is applied to the field
