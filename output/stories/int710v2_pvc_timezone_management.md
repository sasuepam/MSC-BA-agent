# INT710V2 – PVC Timezone Management

---

Type: CR
Summary: INT710 Campaign Contact Creation – Time Zone Enforcement and PVC Callback Routing
Jira Ticket: [TO BE CONFIRMED]
Description:
  Change Scope: Interface INT710 (create contact for campaign).

  - A new synchronous call to AZF003 is inserted after the existing duplicate case check (S008.2V2) and before Salesforce case creation (S008V3).
  - INT710 passes the customer's phone number and market code to AZF003. AZF003 resolves the customer's time zone (IANA format) and earliest contactable date and time (UTC with offset). Time zone is derived from the area code (US/Canada) or country code (all other countries); if the phone number has no country code prefix, the customer's country of residence is used as a fallback.
  - Any error from AZF003 terminates the flow immediately; INT710 returns an error to AJO and no Salesforce case or Genesys contact/callback is created.
  - Salesforce case creation is updated to use S008V3, whose response includes a flag indicating whether the customer has a PVC assigned.
  - If no PVC assigned: INT710 calls GEN070 to add the customer to the campaign contact list, with the resolved time zone included in the contact entry.
  - If PVC assigned: INT710 calls GEN001 to schedule a direct CTI callback in the PVC's personal callback queue at the earliest contactable date and time returned by AZF003.
  - In both paths, after a successful Genesys call, INT710 calls S202 asynchronously to update the Salesforce case with the Genesys interaction identifier; S202 errors are logged but not returned to AJO.

  Rationale: US regulations prohibit call centre agents from contacting customers outside permitted hours (9:00 AM to 9:00 PM) in the customer's own time zone. This restriction was previously applied to campaign queue customers but was not enforced for customers routed directly to an assigned PVC. As PVC assignment has gone live in the US market, PVC-routed customers must now have their callback scheduled at or after the earliest legally permissible contact time. The time zone resolution step also provides Genesys with the customer's time zone for campaign queue customers, enabling Genesys to enforce contactable hours when assigning leads to agents.

  Resources:
    - Timezone Requirements When Contacting Customers: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4685987948/Timezone+requirements+when+contacting+Customers
    - ADR0041 – Outbound Calls Time Zone Contactable Hours: https://msccruises.atlassian.net/wiki/spaces/EA/pages/4701585409/ADR0041+-+Outbound+calls+time+zone+contactable+hours
    - AZF003 – Get Contactable Slot IA: [TO BE CONFIRMED]
    - INT710V2 IA: [TO BE CONFIRMED]
    - Jira Ticket: [TO BE CONFIRMED]

Acceptance Criteria (BDD):
  Scenario: No PVC assigned – customer added to campaign contact list with resolved time zone
  Given AJO sends a campaign contact creation request to INT710 with a valid phone number and market code, no existing case is found in Salesforce, AZF003 successfully returns the customer's time zone and earliest contactable date and time, and the Salesforce case creation response indicates the customer has no PVC assigned
  When INT710 processes the request
  Then INT710 adds the customer to the Genesys campaign contact list via GEN070 with the resolved time zone included in the contact entry, returns a successful response to AJO, and asynchronously updates the Salesforce case with the Genesys contact identifier via S202

  Scenario: PVC assigned – direct CTI callback scheduled in PVC queue at contactable time
  Given AJO sends a campaign contact creation request to INT710 with a valid phone number and market code, no existing case is found in Salesforce, AZF003 successfully returns the customer's time zone and earliest contactable date and time, and the Salesforce case creation response indicates the customer has a PVC assigned
  When INT710 processes the request
  Then INT710 schedules a direct CTI callback in the PVC's personal callback queue via GEN001 at the earliest contactable date and time returned by AZF003, returns a successful response to AJO, and asynchronously updates the Salesforce case with the Genesys callback identifier via S202

  Scenario: Phone number without country code prefix – customer country used as fallback for time zone resolution
  Given AJO sends a campaign contact creation request to INT710 with a phone number that does not include a country code prefix and the customer country is provided, and no existing case is found in Salesforce
  When INT710 calls AZF003
  Then AZF003 derives the country code from the customer country, resolves the area code and time zone, and returns a valid contactable slot; INT710 continues processing normally as in the no-country-code-prefix path

  Scenario: AZF003 returns invalid phone number error – flow terminated, no case created
  Given AJO sends a campaign contact creation request to INT710 with a phone number that cannot be parsed by AZF003, and no existing case is found in Salesforce
  When INT710 calls AZF003
  Then AZF003 returns an invalid phone number error, INT710 terminates the flow and returns an error to AJO, and no Salesforce case, Genesys contact, or Genesys callback is created

  Scenario: AZF003 market code not recognised – flow terminated, no case created
  Given AJO sends a campaign contact creation request to INT710 with a market code that is not recognised by AZF003, and no existing case is found in Salesforce
  When INT710 calls AZF003
  Then AZF003 returns a market code not recognised error, INT710 terminates the flow and returns an error to AJO, and no Salesforce case, Genesys contact, or Genesys callback is created

  Scenario: AZF003 market code cannot be resolved to a country – flow terminated, no case created
  Given AJO sends a campaign contact creation request to INT710 with a market code that is recognised by AZF003 but cannot be mapped to a country, and no existing case is found in Salesforce
  When INT710 calls AZF003
  Then AZF003 returns an error indicating the market code cannot be resolved to a country, INT710 terminates the flow and returns an error to AJO, and no Salesforce case, Genesys contact, or Genesys callback is created

  Scenario: AZF003 no contactable hours configured for resolved country – flow terminated, no case created
  Given AJO sends a campaign contact creation request to INT710 with a phone number that resolves to a country for which no contactable hours are configured in AZF003, and no existing case is found in Salesforce
  When INT710 calls AZF003
  Then AZF003 returns a no contactable hours error for the resolved country, INT710 terminates the flow and returns an error to AJO, and no Salesforce case, Genesys contact, or Genesys callback is created

  Scenario: AZF003 configuration table has no default row for resolved country – flow terminated, no case created
  Given AJO sends a campaign contact creation request to INT710 with a phone number that resolves to a country that exists in the AZF003 configuration but has no default row defined for that country, and no existing case is found in Salesforce
  When INT710 calls AZF003
  Then AZF003 returns an error indicating no default row is present for the country, INT710 terminates the flow and returns an error to AJO, and no Salesforce case, Genesys contact, or Genesys callback is created
