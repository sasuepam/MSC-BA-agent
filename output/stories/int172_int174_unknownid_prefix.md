# INT172 & INT174 – Add "U_" Prefix to unknownId in A092 and A094 CDP Payloads

---

Type: CR
Summary: INT172 & INT174 – Add "U_" prefix to unknownId fields in A092 and A094
Jira Ticket: MDTTPU-14943
Description:
  Change Scope:
    In both the INT172 (Attentive Webhook Subscription) and INT174 (Attentive Webhook Unsubscription)
    flows, update the transformation logic for the following two CDP payload fields:

    A092 – Unknown Profile to CDP:
      Field:  messages[].body{}.xdmEntity{}._msccruisessa{}.identities{}.unknownId
      Before: CHUB › uid  (direct mapping, Type: String)
      After:  CHUB › uid  (Transformation: "U_" + uid, Type: String)

    A094 – Unknown Tracking to CDP:
      Field:  messages[].body{}.xdmEntity{}.identityMap.UNKNOWNID[0].id
      Before: CHUB › uid  (direct mapping, Type: String)
      After:  CHUB › uid  (Transformation: "U_" + uid, Type: String)

    The change applies equally to both INT172 and INT174 because both flows share the
    same A092 and A094 downstream calls.  No other fields in A092 or A094 are affected.

  Rationale:
    CDP requires the UNKNOWNID identity namespace to be prefixed with "U_" so that
    unknown customer profiles are correctly resolved in Adobe Experience Platform.
    Without this prefix the uid value cannot be matched to the UNKNOWNID namespace
    and the profile identity is not established correctly in CDP.

  Resources:
    - IA INT172 – Attentive Webhook Subscription:
        https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4827185319/IA+INT172+-+Attentive+Webhook+Subscription
    - IA INT174 – Attentive Webhook Unsubscribe:
        https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4828856325/IA+INT174+-+Attentive+WebHook+Unsubscribe
    - Source Spike (MDTTPU-14943):
        https://smartship.atlassian.net/browse/MDTTPU-14943

Acceptance Criteria (BDD):

  Scenario: A092 – unknownId prefixed correctly when uid is present
  Given INT172 or INT174 has successfully upserted an unknown customer in CHUB via CH042
  And CHUB returns a non-empty uid value in the response
  When MuleSoft constructs the A092 CDP payload
  Then messages[].body{}.xdmEntity{}._msccruisessa{}.identities{}.unknownId
       is set to the string concatenation "U_" + uid
  And all other A092 fields remain unchanged

  Scenario: A094 – UNKNOWNID[0].id prefixed correctly when uid is present
  Given INT172 or INT174 has successfully upserted an unknown customer in CHUB via CH042
  And CHUB returns a non-empty uid value in the response
  When MuleSoft constructs the A094 CDP payload
  Then messages[].body{}.xdmEntity{}.identityMap.UNKNOWNID[0].id
       is set to the string concatenation "U_" + uid
  And all other A094 fields remain unchanged

  Scenario: INT172 end-to-end – both A092 and A094 carry prefixed uid
  Given Attentive sends a valid subscription event (email.subscribed or sms.subscribed) to INT172
  And CHUB returns a non-empty uid value after the CH042 unknownUpsert call
  When MuleSoft calls A092 and A094
  Then A092 sends messages[].body{}.xdmEntity{}._msccruisessa{}.identities{}.unknownId = "U_" + uid to CDP
  And A094 sends messages[].body{}.xdmEntity{}.identityMap.UNKNOWNID[0].id = "U_" + uid to CDP
  And both calls return 200 OK
  And MuleSoft returns 200 OK to Attentive

  Scenario: INT174 end-to-end – both A092 and A094 carry prefixed uid
  Given Attentive sends a valid unsubscription event (email.unsubscribed or sms.unsubscribed) to INT174
  And CHUB returns a non-empty uid value after the CH042 unknownUpsert call
  When MuleSoft calls A092 and A094
  Then A092 sends messages[].body{}.xdmEntity{}._msccruisessa{}.identities{}.unknownId = "U_" + uid to CDP
  And A094 sends messages[].body{}.xdmEntity{}.identityMap.UNKNOWNID[0].id = "U_" + uid to CDP
  And both calls return 200 OK
  And MuleSoft returns 200 OK to Attentive

  Scenario: uid is null or empty – field is not sent
  Given INT172 or INT174 has called CH042 and CHUB returns a null or empty uid value
  When MuleSoft constructs the A092 and A094 CDP payloads
  Then messages[].body{}.xdmEntity{}._msccruisessa{}.identities{}.unknownId is omitted from the A092 payload
  And messages[].body{}.xdmEntity{}.identityMap.UNKNOWNID[0].id is omitted from the A094 payload
