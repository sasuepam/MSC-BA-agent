# Post-Cruise Complaint Form

---

Type: CR
Summary: INT010.4 – Add attachment support and Post-Cruise Complaint campaignCode mapping
Jira Ticket: EA-1286
Description:
  Change Scope:
    Extend INT010.4 (Contact Request EAPI) to support the new Post-Cruise Complaint webform.
    Two related changes are bundled in this CR:

    1. Optional attachment fields added to the INT010.4 EAPI contract:
       - attachment.name  (Type: String) — filename of the uploaded file
       - attachment.data  (Type: String, base64-encoded) — file content
       Both fields are optional. Their absence must leave all existing INT010.4 use cases
       completely unaffected (full backwards compatibility).
       Maximum permitted file size: 4 MB.

    2. New campaignCode → eventType mapping entry added for the Post-Cruise Complaint Form.
       The confirmation email must reuse the existing "Contact Us" eventType;
       no new email type is to be created.

    When attachment fields are present, the CRM SAPI composite call to S008 is extended
    with three additional sub-requests (executed within the existing Salesforce composite call):
       a. POST ContentVersion   — uploads the file as a ContentVersion record in Salesforce
       b. GET ContentDocumentId — retrieves the ContentDocumentId of the uploaded file
       c. POST ContentDocumentLink — links the ContentDocument to the newly created case

    No changes to the CRM SAPI layer are required; all attachment handling is within
    the existing composite call orchestration at the CRM SAPI level.

  Rationale:
    Post-cruise complaints are currently received via unstructured channels (phone, email),
    causing missing information and longer resolution times for Customer Service agents.
    A structured webform on the B2C website with file attachment support improves data
    completeness and operational efficiency. The existing INT010.4 contact request integration
    is the correct channel to route these submissions into Salesforce.
    File attachments are not supported by the current INT010.4 contract; this CR adds
    that capability while preserving full backwards compatibility with all existing callers.

  Resources:
    - Functional Spec (MS: Post-Cruise Complaint Form):
        https://msccruises.atlassian.net/wiki/spaces/DTP/pages/5365366920/MS+Post-Cruise+Complaint+Form
    - IA INT010.4: [TO BE CONFIRMED]

Acceptance Criteria (BDD):

  Scenario: Post-Cruise Complaint submission with attachment – full happy path
  Given a valid POST request is received on INT010.4 with the Post-Cruise Complaint campaignCode
  And the request body includes attachment.name (a valid filename) and attachment.data (a valid base64-encoded file not exceeding 4 MB)
  When INT010.4 processes the request
  Then a Salesforce case is created via the CRM SAPI S008 composite call
  And a ContentVersion record is created in Salesforce with the file content
  And the ContentDocumentId is retrieved for the uploaded file
  And a ContentDocumentLink is created linking the document to the new case
  And INT010.4 returns 200 OK to the caller

  Scenario: Post-Cruise Complaint submission without attachment
  Given a valid POST request is received on INT010.4 with the Post-Cruise Complaint campaignCode
  And the request body does not include attachment.name or attachment.data
  When INT010.4 processes the request
  Then a Salesforce case is created via the CRM SAPI S008 composite call
  And no ContentVersion, ContentDocumentId, or ContentDocumentLink operations are performed
  And INT010.4 returns 200 OK to the caller

  Scenario: Existing INT010.4 callers – backwards compatibility preserved
  Given a valid POST request is received on INT010.4 with any pre-existing campaignCode
  And the request body does not include attachment fields
  When INT010.4 processes the request
  Then the existing campaignCode-to-eventType mapping and orchestration logic apply unchanged
  And INT010.4 returns 200 OK to the caller
  And no downstream behaviour is altered

  Scenario: campaignCode mapping – Post-Cruise Complaint uses Contact Us email type
  Given a POST request is received on INT010.4 with the Post-Cruise Complaint campaignCode
  When INT010.4 resolves the campaignCode-to-eventType mapping
  Then the eventType is mapped to the existing "Contact Us" type
  And no new email type is created or invoked

  Scenario: Attachment exceeds 4 MB – request rejected
  Given a POST request is received on INT010.4 with an attachment.data value whose decoded size exceeds 4 MB
  When INT010.4 validates the request
  Then the request is rejected with an appropriate error response
  And no Salesforce case is created
  And no ContentVersion record is created

  Scenario: attachment.name present but attachment.data absent (or vice versa) – request rejected
  Given a POST request is received on INT010.4 with only one of attachment.name or attachment.data present
  When INT010.4 validates the request
  Then the request is rejected with an appropriate error response indicating both fields are required when an attachment is included
  And no Salesforce case is created
