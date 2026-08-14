# Attentive Webhook – Subscription and Unsubscription

---

Type: US
Summary: INT172 Attentive Webhook – Record Subscription Event in MSC Systems
Jira Ticket: [TO BE CONFIRMED]
Description:
  User Story: As a marketing operations team, I want subscription events captured in Attentive to be recorded in CHUB and CDP in real time so that customer opt-in preferences are consistent across MSC systems.

  Integration Description:
  - INT172 receives real-time subscription webhook events from Attentive (event types: email.subscribed, sms.subscribed). The Attentive webhook payload format is fixed and cannot be customised; the request must match the default Attentive subscription event schema.
  - The email address is always present in the event and serves as the key identifier for the customer. For email.subscribed events, the phone number is not present in the payload.
  - INT172 validates the HMAC-SHA256 signature sent by Attentive in the x-attentive-hmac-sha256 header by calculating the digest from the raw request data and comparing it against the header value using the environment-specific signing key. Requests with an invalid or missing signature are rejected.
  - On successful validation, INT172 calls CH042 (CHUB Unknown Customer Upsert) using the email address as identifier.
  - After a successful CHUB upsert, INT172 calls A092 (CDP Import Profile) followed by A094 (CDP Send Tracking History for signup), using the subscription status returned by CHUB.
  - MuleSoft returns 200 OK to Attentive only after all downstream calls complete successfully. Any error in a downstream call causes INT172 to return an error response to Attentive.
  - Attentive applies an exponential backoff retry strategy for non-2xx responses for up to 3 days. All downstream integrations (CH042, A092, A094) must support idempotency to prevent duplicate records on retry.

  Security:
  - Signature validation: HMAC-SHA256 digest calculated from raw request body; compared against x-attentive-hmac-sha256 header using the environment- and application-specific signing key. INT172 uses a different signing key from INT174.
  - Client credentials: static clientId and clientSecret passed as query parameters; validated via the client enforcement policy on INT172.
  - IP whitelisting: Attentive source IP addresses whitelisted on Akamai under the verified-legacy category.

  Resources:
    - MS Arch: Attentive | Webhook security measures: [TO BE CONFIRMED]
    - API Connections (Attentive webhook app overview per environment): [TO BE CONFIRMED]
    - Attentive IP whitelisting for webhooks: [TO BE CONFIRMED]
    - Webhook Authentication: [TO BE CONFIRMED]
    - IA INT172: [TO BE CONFIRMED]
    - Jira Ticket: [TO BE CONFIRMED]

Acceptance Criteria (BDD):
  Scenario: Valid email.subscribed event – full processing chain completed
  Given Attentive sends a valid email.subscribed webhook to INT172 with a correct HMAC-SHA256 signature, a valid email address, and no phone number in the payload
  When INT172 processes the event
  Then INT172 upserts the customer in CHUB via CH042 using the email address as identifier, imports the profile to CDP via A092, sends tracking history for signup to CDP via A094, and returns 200 OK to Attentive

  Scenario: Valid sms.subscribed event – full processing chain completed
  Given Attentive sends a valid sms.subscribed webhook to INT172 with a correct HMAC-SHA256 signature and a valid email address
  When INT172 processes the event
  Then INT172 upserts the customer in CHUB via CH042 using the email address as identifier, imports the profile to CDP via A092, sends tracking history for signup to CDP via A094, and returns 200 OK to Attentive

  Scenario: Invalid signature – request rejected
  Given Attentive sends a subscription webhook to INT172 with an invalid or missing HMAC-SHA256 signature
  When INT172 validates the signature
  Then INT172 rejects the request and returns an error response to Attentive without calling any downstream system

  Scenario: CHUB upsert failure – error returned to Attentive
  Given Attentive sends a valid subscription webhook to INT172 with a correct signature, and CH042 returns an error response
  When INT172 calls CH042
  Then INT172 returns an error response to Attentive; no calls to A092 or A094 are made

  Scenario: CDP profile import failure – error returned to Attentive
  Given Attentive sends a valid subscription webhook to INT172 with a correct signature, CH042 completes successfully, and A092 returns an error response
  When INT172 calls A092
  Then INT172 returns an error response to Attentive; no call to A094 is made

  Scenario: CDP tracking history failure – error returned to Attentive
  Given Attentive sends a valid subscription webhook to INT172 with a correct signature, CH042 and A092 complete successfully, and A094 returns an error response
  When INT172 calls A094
  Then INT172 returns an error response to Attentive

  Scenario: Retry of a previously processed event – idempotent, no duplicates created
  Given Attentive retries a subscription webhook that INT172 has already processed successfully
  When INT172 processes the duplicate event
  Then the downstream calls to CH042, A092, and A094 are handled idempotently and no duplicate records are created in CHUB or CDP; INT172 returns 200 OK to Attentive

---

Type: US
Summary: INT174 Attentive Webhook – Record Unsubscription Event in MSC Systems
Jira Ticket: [TO BE CONFIRMED]
Description:
  User Story: As a marketing operations team, I want unsubscription events captured in Attentive to be recorded in CHUB and CDP in real time so that customer opt-out preferences are reflected across MSC systems without delay.

  Integration Description:
  - INT174 receives real-time unsubscription webhook events from Attentive (event types: email.unsubscribed, sms.unsubscribed). INT174 mirrors the orchestration of INT172 for unsubscription events.
  - The email address is always present in the event and serves as the key identifier for the customer.
  - INT174 validates the HMAC-SHA256 signature sent by Attentive in the x-attentive-hmac-sha256 header by calculating the digest from the raw request data and comparing it against the header value using the environment-specific signing key. Requests with an invalid or missing signature are rejected.
  - On successful validation, INT174 calls CH042 (CHUB Unknown Customer Upsert) using the email address as identifier.
  - After a successful CHUB upsert, INT174 calls A092 (CDP Import Profile) followed by A094 (CDP Send Tracking History for signup), using the subscription status returned by CHUB.
  - MuleSoft returns 200 OK to Attentive only after all downstream calls complete successfully. Any error in a downstream call causes INT174 to return an error response to Attentive.
  - Attentive applies an exponential backoff retry strategy for non-2xx responses for up to 3 days. All downstream integrations (CH042, A092, A094) must support idempotency to prevent duplicate records on retry.

  Security:
  - Signature validation: HMAC-SHA256 digest calculated from raw request body; compared against x-attentive-hmac-sha256 header using the environment- and application-specific signing key. INT174 uses a different signing key from INT172 (separate webhook application per environment).
  - Client credentials: static clientId and clientSecret passed as query parameters; validated via the client enforcement policy on INT174.
  - IP whitelisting: Attentive source IP addresses whitelisted on Akamai under the verified-legacy category.

  Resources:
    - MS Arch: Attentive | Webhook security measures: [TO BE CONFIRMED]
    - API Connections (Attentive webhook app overview per environment): [TO BE CONFIRMED]
    - Attentive IP whitelisting for webhooks: [TO BE CONFIRMED]
    - Webhook Authentication: [TO BE CONFIRMED]
    - IA INT174: [TO BE CONFIRMED]
    - Jira Ticket: [TO BE CONFIRMED]

Acceptance Criteria (BDD):
  Scenario: Valid email.unsubscribed event – full processing chain completed
  Given Attentive sends a valid email.unsubscribed webhook to INT174 with a correct HMAC-SHA256 signature and a valid email address
  When INT174 processes the event
  Then INT174 upserts the customer in CHUB via CH042 using the email address as identifier, imports the updated profile to CDP via A092, sends tracking history for the unsubscription to CDP via A094, and returns 200 OK to Attentive

  Scenario: Valid sms.unsubscribed event – full processing chain completed
  Given Attentive sends a valid sms.unsubscribed webhook to INT174 with a correct HMAC-SHA256 signature and a valid email address
  When INT174 processes the event
  Then INT174 upserts the customer in CHUB via CH042 using the email address as identifier, imports the updated profile to CDP via A092, sends tracking history for the unsubscription to CDP via A094, and returns 200 OK to Attentive

  Scenario: Invalid signature – request rejected
  Given Attentive sends an unsubscription webhook to INT174 with an invalid or missing HMAC-SHA256 signature
  When INT174 validates the signature
  Then INT174 rejects the request and returns an error response to Attentive without calling any downstream system

  Scenario: CHUB upsert failure – error returned to Attentive
  Given Attentive sends a valid unsubscription webhook to INT174 with a correct signature, and CH042 returns an error response
  When INT174 calls CH042
  Then INT174 returns an error response to Attentive; no calls to A092 or A094 are made

  Scenario: CDP profile import failure – error returned to Attentive
  Given Attentive sends a valid unsubscription webhook to INT174 with a correct signature, CH042 completes successfully, and A092 returns an error response
  When INT174 calls A092
  Then INT174 returns an error response to Attentive; no call to A094 is made

  Scenario: CDP tracking history failure – error returned to Attentive
  Given Attentive sends a valid unsubscription webhook to INT174 with a correct signature, CH042 and A092 complete successfully, and A094 returns an error response
  When INT174 calls A094
  Then INT174 returns an error response to Attentive

  Scenario: Retry of a previously processed event – idempotent, no duplicates created
  Given Attentive retries an unsubscription webhook that INT174 has already processed successfully
  When INT174 processes the duplicate event
  Then the downstream calls to CH042, A092, and A094 are handled idempotently and no duplicate records are created in CHUB or CDP; INT174 returns 200 OK to Attentive
