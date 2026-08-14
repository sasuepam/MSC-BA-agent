# One-Way Flight Management

## Splitting Rationale

Three Change Requests are raised for this feature. Each CR maps to a distinct interface grouping with a separate scope of change and Jira ticket.

- **CR-1** consolidates INT002.1, INT002.2, INT002.3, and INT002.4: all four interfaces make the same additive change (expose `airType` derived from the DTS `<Occurrence>` tag), share a single Jira ticket (DTTP25-31684), and have a common DTS source. Raising four separate CRs would produce near-identical stories with no additional clarity benefit.
- **CR-2** covers INT005.2 in isolation: the nature of change is distinct (consume `airType` in the request, fix one-way DTS response mapping, make flight collections optional), it has its own Jira ticket (DTTP25-37438), and the backward-compatibility impact (NFR-001) is scoped to this interface only.
- **CR-3** consolidates INT004.3, INT004.4, INT006, and INT007: all four interfaces make the same change (accept and validate `airType`, set `<OneWay>` in the DTS request, handle legacy `isOneWay` fallback), covered across two Jira tickets (DTTP25-29614, DTTP25-29615).

No ADF interfaces are present in the spec.

| Story | Scope | Reason for separation (or consolidation) |
|---|---|---|
| CR-1: INT002.x – Expose airType in Category Search Responses | INT002.1, INT002.2, INT002.3, INT002.4 — derive and return `airType` from DTS `<Occurrence>` tag | Consolidated CR: identical change across all four variants, single Jira ticket (DTTP25-31684), common DTS source. |
| CR-2: INT005.2 – Support One-Way Air Packages in Flight Availability | INT005.2 — accept `airType` in request, fix one-way DTS response mapping, make flight collections optional | Separate CR: distinct change with unique backward-compatibility scope, separate Jira ticket (DTTP25-37438). |
| CR-3: INT004.3 / INT004.4 / INT006 / INT007 – Forward airType to DTS | INT004.3, INT004.4, INT006, INT007 — validate `airType` consistency, set `<OneWay>` in DTS request, support legacy fallback | Consolidated CR: identical change across all four interfaces, two Jira tickets (DTTP25-29614, DTTP25-29615). |

---

## Change Requests

---

Type: CR
Summary: INT002.x – Expose airType in Category Search Responses
Jira Ticket: DTTP25-31684
Description:
  Change Scope:
    - INT002.1 (Get Price Lists), INT002.2 (Get Cabin Types), INT002.3 (Get Cabin Preferences), and INT002.4 (Get Categories) must each be updated to derive and expose the `airType` field for every packaged AIR item in their category search responses.
    - DTS returns an `<Occurrence>` tag per AIR item; each INT002.x interface must map this to the `airType` enumeration: `*` → `ROUND_TRIP`, `O` → `OUTBOUND_ONLY`, `R` → `RETURN_ONLY`.
    - The derived `airType` value must be included in the response returned to B2CW alongside the corresponding packaged air item.
    - B2CW uses `airType` to display the correct UI — one-way banner and single-leg flight selection for one-way packages, or standard round-trip UI for round-trip packages.
    - B2CW must carry `airType` forward into all subsequent booking funnel calls for the selected package.
    - The change applies identically across all four INT002.x variants.

  Rationale: The MSC website cannot currently display or sell one-way packaged flight options for repositioning cruises. B2CW has no signal from MuleSoft to indicate whether a packaged air item is outbound-only, return-only, or round-trip. Exposing `airType` in the INT002.x responses gives B2CW the information it needs to display the correct UI and carry the flight type through the full booking funnel.

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation:
      - IA INT002.1 – Get Price Lists: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4248076289/IA+INT002.1v1.1+-+Get+price+lists
      - IA INT002.2 – Get Cabin Types: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4249387009/IA+INT002.2v1.1+-+Get+cabin+types
      - IA INT002.3 – Get Cabin Preferences: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4249419777
      - IA INT002.4 – Get Categories: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4249387137
    - Confluence Page: MS One Way Flights: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/5176262885/MS+One+Way+Flights

Acceptance Criteria (BDD):
  Given a customer searches for a repositioning cruise that includes an outbound-only packaged flight (cruise ID: [TO BE CONFIRMED], DTS air occurrence = O)
  When the category search response is returned from DTS via INT002.x
  Then the website receives `airType` = `OUTBOUND_ONLY` against the packaged air item, enabling the one-way outbound banner and single-leg flight selection to be displayed

  Given a customer searches for a repositioning cruise that includes a return-only packaged flight (cruise ID: OX20261031GOALRM, DTS air occurrence = R)
  When the category search response is returned from DTS via INT002.x
  Then the website receives `airType` = `RETURN_ONLY` against the packaged air item, enabling the one-way return banner and single-leg flight selection to be displayed

  Given a customer searches for a standard cruise with a round-trip packaged flight
  When the request flows through INT002.x
  Then all INT002.x interfaces derive `airType` = `ROUND_TRIP` from DTS `<Occurrence>` = `*` and return it to B2CW — the website displays the standard round-trip flight selection UI with no one-way banners displayed

---

Type: CR
Summary: INT005.2 – Support One-Way Air Packages in Flight Availability
Jira Ticket: DTTP25-37438
Description:
  Change Scope:
    - INT005.2 (Get Flights) must be updated to accept `airType` from B2CW in the flight availability request.
    - The DTS `DtsAirWrapResponse` must be filtered based on `airType` before returning to B2CW:
      - `OUTBOUND_ONLY`: return `OutboundFlightChoices` and a single `<Selector>` only; `ReturnFlightChoices` must be absent from the response.
      - `RETURN_ONLY`: return `ReturnFlightChoices` and a single `<Selector>` only; `OutboundFlightChoices` must be absent from the response.
      - `ROUND_TRIP`: return both `OutboundFlightChoices` and `ReturnFlightChoices` as before.
    - If DTS unexpectedly returns both flight collections for a declared one-way package, INT005.2 must discard the irrelevant collection and return only the applicable leg — no unhandled error must be raised.
    - The `outbound` and `return` collections in the response become optional fields.
    - All downstream consumers that currently expect both collections to always be present must be assessed for backward compatibility impact before deployment (NFR-001).

  Rationale: INT005.2 currently assumes both outbound and return flight legs are always present in the DTS response. Categories with one-way flights fail to return a result because the mapping looks for a leg that is absent. This change fixes the mapping to handle single-leg DTS responses and exposes only the relevant flight collection to B2CW.

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation:
      - IA INT005.2 – Get Flights: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/3463905380
    - Confluence Page: MS One Way Flights: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/5176262885/MS+One+Way+Flights

Acceptance Criteria (BDD):
  Given a customer has selected a repositioning cruise with an outbound-only packaged flight (cruise ID: [TO BE CONFIRMED]) and the website requests flight availability with `airType` = `OUTBOUND_ONLY`
  When INT005.2 retrieves the available flights from DTS
  Then only outbound flight options are returned to the website; no return flight options are included, and the customer can proceed to select their outbound flight

  Given a customer has selected a repositioning cruise with a return-only packaged flight (cruise ID: OX20261031GOALRM) and the website requests flight availability with `airType` = `RETURN_ONLY`
  When INT005.2 retrieves the available flights from DTS
  Then only return flight options are returned to the website; no outbound flight options are included, and the customer can proceed to select their return flight

  Given a customer has selected a one-way packaged flight and flight availability is requested with `airType` = `OUTBOUND_ONLY` or `RETURN_ONLY`
  When DTS unexpectedly returns both outbound and return flight collections in the response
  Then INT005.2 returns only the flight collection applicable to the declared `airType` without an unhandled error, and the irrelevant collection is discarded

  Given a customer searches for and books a standard cruise with a round-trip packaged flight
  When the request flows through INT005.2
  Then both `OutboundFlightChoices` and `ReturnFlightChoices` are returned as before — no regression in round-trip behaviour

---

Type: CR
Summary: INT004.3 / INT004.4 / INT006 / INT007 – Forward airType to DTS in Insurance, Price, Booking, and Amendment Requests
Jira Ticket: DTTP25-29614, DTTP25-29615
Description:
  Change Scope:
    - INT004.3 (Insurance), INT004.4 (Price to Book), INT006 (Hold Option), and INT007 (Booking Request) must each be updated to accept `airType` from B2CW and validate consistency with the supplied flight collections before making any DTS call.
    - Validation rules for `airType` vs. flight collections:
      - `ROUND_TRIP`: both outbound and return flight collections must be present.
      - `OUTBOUND_ONLY`: outbound collection required; return collection must be absent.
      - `RETURN_ONLY`: return collection required; outbound collection must be absent.
    - If validation fails, the request must be rejected before reaching DTS and an error response returned to B2CW indicating the inconsistency.
    - If validation passes, MuleSoft must forward the request to DTS with `<OneWay>` set to `yes` (one-way) or `no` (round-trip), and both `<OutboundDepartureDate>` and `<ReturnDepartureDate>` populated.
    - When `airType` is present in the request, it takes precedence over any legacy `isOneWay` boolean field (NFR-002).
    - When `airType` is absent, the integration must fall back to the legacy `isOneWay` field to maintain backward compatibility with existing callers that have not yet adopted `airType` (NFR-002).
    - DTTP25-29614 covers INT004.3 and INT004.4; DTTP25-29615 covers INT006 and INT007.

  Rationale: Insurance, price, booking, and amendment interfaces currently pass the one-way indicator to DTS based on a legacy boolean value assumed to be false in all requests. This change introduces `airType` across all four interfaces to correctly set the DTS `<OneWay>` flag, ensuring DTS applies the right pricing and processing logic for one-way packages and that the full booking funnel is aligned.

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation:
      - IA INT004.3 – Insurance: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4452319314
      - IA INT004.4 – Price to Book: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4537876824
      - IA INT006 – Hold Option: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4800413697
      - IA INT007 – Booking Request: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/4537876481
    - Confluence Page: MS One Way Flights: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/5176262885/MS+One+Way+Flights

Acceptance Criteria (BDD):
  Given a customer has selected an outbound-only flight for a repositioning cruise (cruise ID: [TO BE CONFIRMED]) and proceeds to the insurance and pricing step
  When INT004.3 (insurance) and INT004.4 (price) send the request to DTS
  Then DTS receives `<OneWay>` = `yes` alongside the outbound flight details only, and returns insurance and price results that reflect the one-way package

  Given a customer has selected a return-only flight for a repositioning cruise (cruise ID: OX20261031GOALRM) and proceeds to hold the option
  When INT006 (hold option) sends the request to DTS
  Then DTS receives `<OneWay>` = `yes` alongside the return flight details only, and the hold option is confirmed successfully

  Given a customer has selected an outbound-only flight for a repositioning cruise (cruise ID: [TO BE CONFIRMED]) and proceeds to confirm the booking
  When INT007 (booking) sends the request to DTS
  Then DTS receives `<OneWay>` = `yes` alongside the outbound flight details only, and the booking is confirmed successfully

  Given a request is sent to INT004.3, INT004.4, INT006, or INT007 with an inconsistent combination of `airType` and flight collections — `airType` = `OUTBOUND_ONLY` but a return flight collection is included, or `airType` = `RETURN_ONLY` but an outbound flight collection is included, or `airType` = `ROUND_TRIP` but one or both flight collections are missing
  When MuleSoft validates the request
  Then the request is rejected before reaching DTS and an error response is returned to the website indicating the inconsistency

  Given a customer searches for and books a standard cruise with a round-trip packaged flight
  When the request flows through INT004.3, INT004.4, INT006, and INT007
  Then all interfaces behave exactly as before — both outbound and return flight collections are present throughout, DTS receives `<OneWay>` = `no`, and the booking completes successfully

  Given a request is sent to INT004.3, INT004.4, INT006, or INT007 without the new `airType` field but with the legacy one-way indicator populated (pre-condition: confirm legacy `isOneWay` field exists on each interface — [TO BE CONFIRMED] for INT004.3, INT004.4, INT006, INT007)
  When MuleSoft processes the request
  Then the legacy field is used to determine the one-way indicator sent to DTS, and the request is processed successfully without error — existing integrations that have not yet adopted `airType` are unaffected
