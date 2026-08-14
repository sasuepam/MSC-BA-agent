| VERSION | AUTHOR(S) | DATE | REMARKS | STATUS | TICKETS |
| --- | --- | --- | --- | --- | --- |
| 1 | link Co-authored by MSC Integration Architect Agent |  | SA sections populated: Solution Overview, Involved Interfaces, Sequence Diagrams, Monitoring and Alerting Guidelines | **[DRAFT]** |  |
| 2 | link Co-authored by MSC BA Agent |  | Updated BA sections: Reference Documentation, Feature Summary, Business Requirements, Use Cases, Non-Functional Requirements, Test Scenarios & Acceptance Criteria | **[DRAFT]** |  |
| 3 | link |  | Updates based on review | **[LATEST]** |  |

## **Reference documentation:**

| ** Document ** | ** Link ** |
| --- | --- |
| DTTP25-25492 – One-Way Flight Management (parent / epic) | DTTP25-25492 |
| DTTP25-21764 – INT002.1 / INT002.2 / INT002.3 / INT002.4 – Expose airType in category search responses | DTTP25-21764 |
| DTTP25-26726 – INT005.2 – Support one-way air packages in flight availability | DTTP25-26726 |
| DTTP25-29614 – INT004.3 / INT004.4 – Forward airType to DTS in insurance and price requests | DTTP25-29614 |
| DTTP25-29615 – INT006 / INT007 – Forward airType to DTS in booking and amendment requests | DTTP25-29615 |
| DTTP25-31684 – MuleSoft Tech Story | DTTP25-31684 |
| DTTP25-37438 – MuleSoft Tech Story | DTTP25-37438 |
| DTTP25-37439 – MuleSoft Tech Story | DTTP25-37439 |
| IA INT002.1 – Get Price Lists | [IA INT002.1 – Get Price Lists](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=IA+INT002.1v1.1+-+Get+price+lists) |
| outIA INT002.2 – Get Cabin Types | [IA INT002.2 – Get Cabin Types](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=IA+INT002.2v1.1+-+Get+cabin+types) |

# Feature Summary
**Business Context**
MSC Cruises offers repositioning voyages — cruises where the ship departs from one port and arrives at a completely different destination, without returning to where it started. Because customers on these itineraries only need to travel in one direction, the cruise package may include either an outbound flight to the embarkation port, a return flight home from the disembarkation port, or both legs for guests travelling to and from the same city.
Today, the MSC website cannot display or sell these one-way packaged flight options. When a customer browses a repositioning cruise that includes a one-way flight, the booking platform fails to return flight availability results, meaning the guest either sees no options or hits a dead end before they can complete their booking. This results in lost sales and a poor guest experience for an important part of the MSC cruise portfolio.
**What this feature delivers**
This feature unlocks the ability for customers to search, select, and book repositioning cruises with one-way packaged flights — outbound only, return only, or both legs — end-to-end through the MSC booking website. Key improvements include:
- **Flight availability is no longer blocked** for categories that include a single flight leg. Customers can view and select the available flight without encountering missing data or errors.
- **The booking website adapts its display** based on the flight type available —
showing clear one-way banners, direction-specific labels (“Outbound Only” / “Return Only”), and
relevant flight cards. Unavailable legs are hidden throughout the booking journey.
- **Pricing, insurance, and booking confirmations** correctly reflect the one-way
nature of the flight package, ensuring DTS applies the right pricing logic and that all
downstream systems are aligned.
- **A consistent flight type indicator** is carried through every step of the booking funnel — from category search through to booking confirmation — replacing fragmented or hardcoded values that previously caused failures.

## Business Requirements

| ** ID ** | ** Requirements ** |
| --- | --- |
| BR-001 | As a B2CW website user, I want the category search results to indicate whether an air package includes a round trip, outbound-only, or return-only flight so that the correct one-way UI (banner and single-leg flight selection) is displayed on the website. [Image] |
| BR-002 | As a B2CW website user, I want flight availability results to correctly reflect one-way packages so that I can select the available flight leg without encountering missing data errors. [Image] |
| BR-003 | As the DTS system, I want the insurance, price, booking, and amendment interfaces to pass the correct one-way indicator so that DTS can apply the appropriate pricing and processing logic for the selected air type. |

## Use Cases

- 
- 

- 
- 
- 
- 
- 

- 
- 

- 
- 
  - 
  - 
- 
- 

- 
- 

- 
- 
  - 
  - 
  - 
- 
- 

- 

- 
- 
- 
- 

| ** UC# ** | ** PreCondition ** | ** Actor/s ** | ** Use Case ** | ** Functionality Expected ** | ** Open Questions ** |
| --- | --- | --- | --- | --- | --- |
| UC-001 | Customer is searching for a cruise package on B2CW. The selected cruise is a repositioning cruise with a packaged air item that is outbound-only, return-only, or round-trip. | Customer on B2C Website | Category search results indicate the air trip type for each packaged air item (BR-001) | B2CW calls the relevant INT002.x variant with a category search request. MuleSoft INT002.x calls DTS and receives category data containing AIR packaged items, each with an ` <Occurrence> ` tag ( ` * ` , ` O ` , or ` R ` ). MuleSoft derives ` airType ` for each AIR packaged item — ` ROUND_TRIP ` , ` OUTBOUND_ONLY ` , or ` RETURN_ONLY ` — and includes it in the category search response to B2CW. B2CW reads ` airType ` and adapts the UI accordingly: displaying a one-way banner and single-leg flight selection for one-way packages, or standard UI for round-trip. B2CW carries the ` airType ` value forward into all subsequent booking funnel calls. |  |
| UC-002 | Customer has selected a repositioning cruise with a one-way packaged air item. B2CW holds ` airType ` (OUTBOUND_ONLY or RETURN_ONLY) from the INT002.x response. | Customer on B2C Website | Flight availability returns only the relevant flight collection for one-way packages (BR-002) | B2CW calls INT005.2 with a flight availability request including the ` airType ` value from the category search response. INT005.2 calls DTS and receives a ` DtsAirWrapResponse ` containing only the flight collection(s) applicable to the declared air type: ` OUTBOUND_ONLY ` : only ` OutboundFlightChoices ` and one ` <Selector> ` are returned. ` RETURN_ONLY ` : only ` ReturnFlightChoices ` and one ` <Selector> ` are returned. MuleSoft maps the response based on ` airType ` , returning only the relevant flight collection to B2CW; the other collection is absent. B2CW displays only the available flight direction to the customer; the unavailable leg is suppressed throughout the booking funnel. |  |
| UC-003 | Customer has selected a flight and is proceeding through insurance, pricing, booking, or amendment for a repositioning cruise with a one-way packaged air item. B2CW holds ` airType ` from INT002.x and the applicable flight selection(s) from INT005.2. | Customer on B2C Website | Insurance, price, booking, and amendment interfaces validate and forward airType to DTS (BR-003) | B2CW calls INT004.3 (insurance), INT004.4 (price), INT006 (hold option), or INT007 (booking) with ` airType ` and the appropriate flight collection(s) for the declared air type. MuleSoft validates consistency between ` airType ` and the supplied flight collections before making any DTS call: ` ROUND_TRIP ` : both outbound and return collections must be present. ` OUTBOUND_ONLY ` : outbound collection required; return must be absent. ` RETURN_ONLY ` : return collection required; outbound must be absent. If validation passes, MuleSoft forwards the request to DTS with ` <OneWay> ` set to ` yes ` (one-way) or ` no ` (round-trip), and both ` <OutboundDepartureDate> ` and ` <ReturnDepartureDate> ` populated. DTS returns the insurance, price, hold option, or booking response. MuleSoft returns it to B2CW. |  |
| UC-004 | Customer is browsing a standard cruise with a round-trip packaged air item. | Customer on B2C Website | Existing round-trip air packages continue to work unchanged after the airType change | INT002.x derives ` airType ` = ` ROUND_TRIP ` from DTS ` <Occurrence> ` = ` * ` and returns it to B2CW. INT005.2 receives ` airType ` = ` ROUND_TRIP ` and returns both ` OutboundFlightChoices ` and ` ReturnFlightChoices ` as before. INT004.3, INT004.4, INT006, and INT007 receive ` airType ` = ` ROUND_TRIP ` with both collections present, pass validation, and forward ` <OneWay> ` = ` no ` to DTS. B2CW displays the standard round-trip flight selection UI; no one-way banners or labels are shown. |  |

# Solution Overview
Some repositioning cruises depart from one port and arrive at a different port, meaning the ship does not return to its origin. For these cruises, DTS supports packaged items for a category where only one flight leg is included – either an outbound flight(s) to the embarkation port, or a return flight(s) from the disembarkation port. Three air item types exist:

| Packaged Item field ` <Occurrence> ` | Meaning |
| --- | --- |
| ` * ` | Round Trip – outbound and return flights included |
| ` O ` | Outbound Only – flight to the embarkation port only |
| ` R ` | Return Only – flight from the disembarkation port only |
The current implementation does not support one-way flight packaged items, as it was assumed that flights would always be round trip.
INT002.1, INT002.2, INT002.3, INT002.4 integrations do not expose the type of air trip to B2CW and INT005.2 assumes both flight legs are always present in the DTS response. This means categories with one-way flights fail to return a result in INT005.2 as the mapping is looking for missing information.
Insurance (INT004.3), price (INT004.4) and booking (INT006, INT007) interfaces pass if the flight is one way or not to DTS based on the value provided by B2CW, but it’s assumed to be false in all requests.
To address this, a new `airType` field is introduced across all interfaces which include air packaged items in either requests and responses, replacing the legacy boolean `isOneWay` field where it already exists. This gives a single, consistent representation of the air type across integrations.

| Field | Type | Values | Description |
| --- | --- | --- | --- |
| ` airType ` (naming to be confirmed in API design) | String (enumeration) | ` ROUND_TRIP ` , ` OUTBOUND_ONLY ` , ` RETURN_ONLY ` | Identifies whether the packaged air item includes both flight legs, outbound only, or return only |
The mapping between `airType` and DTS fields is as follows:

| ` airType ` | DTS ` <Occurrence> ` (searchCruisesB2C response) | DTS ` <OneWay> ` (multiple requests) |
| --- | --- | --- |
| ` ROUND_TRIP ` | ` * ` | ` no ` |
| ` OUTBOUND_ONLY ` | ` O ` | ` yes ` |
| ` RETURN_ONLY ` | ` R ` | ` yes ` |
Where a legacy `isOneWay` boolean field exists, the integrations will give preference to `airType` when present and fall back to the legacy field otherwise.
It was confirmed that both `<OutboundDepartureDate>` and `<ReturnDepartureDate>` should always be populated in the DTS requests, regardless of the air type.

## **INT002.1, INT002.2, INT002.3, INT002.4**
INT002.1, INT002.2, INT002.3 and INT002.4 will each return the new `airType` field within each AIR packaged item in the categories in the response, derived from the DTS `<Occurrence>` tag. The website uses this value to drive the one-way banner and single-leg flight selection UI, and carries it forward into all subsequent booking funnel calls.

## **INT005.2**
A new `airType` field is added to the request; the website populates it from the relevant INT002.1, INT002.2, INT002.3 and INT002.4 response.
For one-way packages, DTS returns a `DtsAirWrapResponse` containing only one of `OutboundFlightChoices` or `ReturnFlightChoices`, and `FlightRef` carries a single `<Selector>` rather than two. The mapping must be updated to map the response based on the `airType`, checking which leg is present and return only the relevant flight collection. The `outbound` and `return` collections in the response become optional fields.

| Scenario | ` OutboundFlightChoices ` | ` ReturnFlightChoices ` | ` <Selector> ` count |
| --- | --- | --- | --- |
| Round Trip | Present | Present | 2 |
| Outbound Only | Present | Absent | 1 |
| Return Only | Absent | Present | 1 |

## **INT004.3, INT004.4, INT006, INT007**
These interfaces need only forward `airType` to DTS as the `<OneWay>` tag. The `outbound` and `return` flight collections with air items in the request become optional. The integrations should validate consistency between `airType` and the populated flight collections:

| ` airType ` | Required | Must not be present |
| --- | --- | --- |
| ` ROUND_TRIP ` | ` outbound ` + ` return ` | – |
| ` OUTBOUND_ONLY ` | ` outbound ` | ` return ` |
| ` RETURN_ONLY ` | ` return ` | ` outbound ` |

## Involved Interfaces

| ** Interface ** | ** High Level Impacts ** | ** Low Level Impacts ** | ** Integration High Level Architecture ** |
| --- | --- | --- | --- |
| [INT002.1 – Get Price Lists](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=IA+INT002.1v1.1+-+Get+price+lists) | None | Add ` airType ` to AIR item in response | [INT002v2 - Flexible Booking Funnel](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=INT002v2+Flexible+Booking+Funnel) |
| [INT002.2 – Get Cabin Types](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=IA+INT002.2v1.1+-+Get+cabin+types) | None | Add ` airType ` to AIR item in response | [INT002v2 - Flexible Booking Funnel](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=INT002v2+Flexible+Booking+Funnel) |
| [INT002.3 – Get Cabin Preferences](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=IA+INT002.3v1.1+-+Get+cabin+preferences) | None | Add ` airType ` to AIR item in response | [INT002v2 - Flexible Booking Funnel](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=INT002v2+Flexible+Booking+Funnel) |
| [INT002.4 – Get Categories](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=IA+INT002.4v1.1+-+Get+categories) | None | Add ` airType ` to AIR item in response | [INT002v2 - Flexible Booking Funnel](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=INT002v2+Flexible+Booking+Funnel) |
| [INT005.2 – Get Flights](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=W005-2+-+Get+Flights) | None | Add ` airType ` to request Fix one-way DTS response mapping to handle single-leg ` DtsAirWrapResponse ` Make ` outbound ` / ` return ` optional in response | [INT005.2 - Search Flight Fares](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=INT005.W005-2+-+Search+Flight+Fares) |
| [INT004.3 – Insurance](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=INT004.3V2+-+Insurance) | None | Add ` airType ` to request; pass ` <OneWay> ` to DTS Make ` outbound ` / ` return ` optional in request; add server-side consistency validation | [INT004.3 - Insurance](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=INT004.W004.3+-+Insurance) |
| [INT004.4 – Price to Book](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=INT004.4V3+-+Price+to+book) | None | Add ` airType ` to request; pass ` <OneWay> ` to DTS Make ` outbound ` / ` return ` optional in request; add server-side consistency validation | [INT004.4 - Update Cart](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=INT004.4+-+Price+to+Book) |
| [INT006 – Hold Option](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=IA+INT006V3+-+Hold+Option) | None | Add ` airType ` to request; pass ` <OneWay> ` to DTS Make ` outbound ` / ` return ` optional in request; add server-side consistency validation | [INT006 - Freeze Price/Hold Option](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=INT006.W006+-+Freeze+Price/Hold+Option) |
| [INT007 – Booking Request](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=IA+INT007V3+-+Booking+Request) | None | Add ` airType ` to request; pass ` <OneWay> ` to DTS Make ` outbound ` / ` return ` optional in request; add server-side consistency validation | [INT007 - Booking Request](https://msccruises.atlassian.net/wiki/spaces/DTP/search?text=INT007.W007+-+Create+Booking) |

## Sequence Diagrams
[Image]**[Source]**

```
@startuml

actor "Customer" as User
participant "B2C Website" as B2C
participant "APIs" as API
participant "DTS" as DTS

activate User
User -> B2C++: Select cruise

B2C -> API++: Get price types (INT002.1)
API -> DTS++: searchCruisesB2C
DTS -> API--: Return categories, including AIR item details with Occurrence (*, O, R)
API -> B2C--: Price types including airType for lowest priced category
...
B2C -> API++: Get cabin types (INT002.2)
API -> DTS++: searchCruisesB2C
DTS -> API--: Return categories, including AIR item details with Occurrence (*, O, R)
API -> B2C--: Cabin types including airType for lowest priced category
...
B2C -> API++: Get cabin preferences (INT002.3)
API -> DTS++: searchCruisesB2C
DTS -> API--: Return categories, including AIR item details with Occurrence (*, O, R)
API -> B2C--: Cabin preferences including airType for lowest priced category
...
B2C -> API++: Get categories (INT002.4)
API -> DTS++: searchCruisesB2C
DTS -> API--: Return categories, including AIR item details with Occurrence (*, O, R)
API -> B2C--: Categories including airType
...
B2C -> API++: Get departure airports (INT005.1)
API -> DTS++: originairports
DTS -> API--:
API -> B2C--: Return departure airports
...
B2C -> API++: Get air fares (INT005.2) with airType
API -> DTS++: dtsairwrapgenrequest with OneWay + both departure dates
DTS -> API--: Return airfares (one leg only for one-way; single Selector)
API -> B2C--: Return airfares with for relevant leg(s) (outbound/return flights optional)

B2C -> User: Display available flights
...
User -> B2C: Select flight(s)
...
B2C -> API++: Get insurance (INT004.3) with airType
API -> DTS++: shopRequest with OneWay
DTS -> API--:
API -> B2C--: Return insurance options
...
B2C -> API++: Get price to book (INT004.4) with airType
API -> DTS++: priceToBook with OneWay
DTS -> API--:
API -> B2C--: Return final price
...
B2C -> User: Display final price and booking summary
...
User -> B2C: Confirm booking
...
alt Hold option
    B2C -> API++: Hold booking (INT006) with airType
    API -> DTS++: bookRequestB2C with OneWay
    DTS -> API--:
    API -> B2C--: Return booking
else Book with payment
    B2C -> API++: Create booking (INT007) with airType
    API -> DTS++: bookRequestB2C with OneWay
    DTS -> API--:
    API -> B2C--: Return booking
end

B2C -> User--: Display confirmation
deactivate User
@enduml
```
When the customer selects a cruise, the website calls INT002.1, INT002.2, INT002.3, INT002.4 for the price types, cabin types, cabin preferences, and cabin categories respectively so the user selects a specific cabin category. Each of these responses includes the `airType` field on every AIR packaged item, derived from the `<Occurrence>` tag in the `searchCruisesB2C` response. The website uses this to determine whether the packaged air item is round trip, outbound only, or return only, and adapts the UI accordingly.
Once the customer selects a cabin category and optionally a specific cabin, the website summary screen calls INT005.1 to retrieve the available departure airports, followed by INT005.2 to retrieve airfares for the selected airport and cabin class. The `airType` value from the earlier INT002.1/INT002.2/INT002.3/INT002.4 response is sent in the INT005.2 request. DTS returns only the outbound or return flight choices for one-way packages, with a single `<Selector>` in the `FlightRef`, and the integration maps this to the response.
After the customer selects their flight(s), the website calls INT004.3 for insurance options and INT004.4 to retrieve the price to book, both with `airType` and only the relevant flights included. On booking confirmation, the website calls either INT006 to create a hold option booking or INT007 to create a booking with payment, again passing `airType` and the relevant flights. In all cases DTS receives the `<OneWay>` flag with the appropriate value.

# Non-Functional Requirements

| Requirement ID | Interface | Requirement Description | Category | Priority |
| --- | --- | --- | --- | --- |
| NFR-001 | INT005.2 | The outbound and return flight collections in the INT005.2 response are optional. Consumers that currently expect both collections to always be present must be assessed for backward compatibility impact before deployment. The change must not cause existing round-trip consumers to fail when both collections are present. | Backward Compatibility | High |

# Monitoring and alerting guidelines
No specific monitoring or alerting scenarios have been identified for this feature.

# Test Scenarios & Acceptance Criteria

| ** Use Case ** | ** Test Cases ** | ** Acceptance Criteria ** | ** Test Data ** |
| --- | --- | --- | --- |
| UC-001 | TC-001: Happy Path – Category search correctly identifies an outbound-only flight package and returns the air type to the website | ** Given ** a customer searches for a repositioning cruise that includes an outbound-only packaged flight ** When ** the category search response is returned from DTS via INT002.x ** Then ** the website receives ` airType ` = ` OUTBOUND_ONLY ` against the packaged air item, enabling the one-way outbound banner and single-leg flight selection to be displayed | Identify a repositioning cruise in DTS with an outbound-only packaged air category (DTS air occurrence = O). Applicable to INT002.1, INT002.2, INT002.3, INT002.4 — test data required for each variant. |
| UC-001 | TC-002: Happy Path – Category search correctly identifies a return-only flight package and returns the air type to the website | ** Given ** a customer searches for a repositioning cruise that includes a return-only packaged flight ** When ** the category search response is returned from DTS via INT002.x ** Then ** the website receives ` airType ` = ` RETURN_ONLY ` against the packaged air item, enabling the one-way return banner and single-leg flight selection to be displayed | Cruise ID: OX20261031GOALRM — repositioning cruise with a return-only packaged air category (DTS air occurrence = R). Applicable to INT002.1, INT002.2, INT002.3, INT002.4 — test data required for each variant. |
| UC-002 | TC-003: Happy Path – Flight availability returns only outbound flight options when the package is outbound-only | ** Given ** a customer has selected a repositioning cruise with an outbound-only packaged flight and the website requests flight availability with ` airType ` = ` OUTBOUND_ONLY ` ** When ** INT005.2 retrieves the available flights from DTS ** Then ** only outbound flight options are returned to the website; no return flight options are included, and the customer can proceed to select their outbound flight | Identify a repositioning cruise with an outbound-only packaged flight where DTS returns flight availability for the outbound leg only. Confirm the DTS response contains a single flight selector for the outbound direction. |
| UC-002 | TC-004: Happy Path – Flight availability returns only return flight options when the package is return-only | ** Given ** a customer has selected a repositioning cruise with a return-only packaged flight and the website requests flight availability with ` airType ` = ` RETURN_ONLY ` ** When ** INT005.2 retrieves the available flights from DTS ** Then ** only return flight options are returned to the website; no outbound flight options are included, and the customer can proceed to select their return flight | Cruise ID: OX20261031GOALRM — repositioning cruise with a return-only packaged flight where DTS returns flight availability for the return leg only. Confirm the DTS response contains a single flight selector for the return direction. |
| UC-002 | TC-005: Error Scenario – Flight availability handles a DTS response that unexpectedly returns both legs for a one-way package | ** Given ** a customer has selected an outbound-only packaged flight and flight availability is requested with ` airType ` = ` OUTBOUND_ONLY ` ** When ** DTS unexpectedly returns both outbound and return flight collections in the response ** Then ** TBC | Simulate a DTS flight availability response for an outbound-only request that incorrectly includes both outbound and return flight collections. Use a stubbed or mocked DTS response to create this defensive scenario. |
| UC-003 | TC-006: Happy Path – Insurance and price calculations correctly reflect an outbound-only package when passed to DTS | ** Given ** a customer has selected an outbound-only flight for a repositioning cruise and proceeds to the insurance and pricing step ** When ** INT004.3 (insurance) and INT004.4 (price) send the request to DTS ** Then ** DTS receives the correct one-way indicator alongside the outbound flight details only, and returns insurance and price results that reflect the one-way package | Identify a repositioning cruise with an outbound-only packaged flight that is available for insurance and price calculation in DTS. Request should include only the outbound flight collection. |
| UC-003 | TC-007: Happy Path – Hold option correctly reflects a return-only package when passed to DTS | ** Given ** a customer has selected a return-only flight for a repositioning cruise and proceeds to hold the option ** When ** INT006 (hold option) sends the request to DTS ** Then ** DTS receives the correct one-way indicator alongside the return flight details only, and the hold option is confirmed successfully | Cruise ID: OX20261031GOALRM — repositioning cruise with a return-only packaged flight that is available for hold option in DTS. Request should include only the return flight collection. |
| UC-003 | TC-008: Happy Path – Booking correctly reflects an outbound-only package when passed to DTS | ** Given ** a customer has selected an outbound-only flight for a repositioning cruise and proceeds to confirm the booking ** When ** INT007 (booking) sends the request to DTS ** Then ** DTS receives the correct one-way indicator alongside the outbound flight details only, and the booking is confirmed successfully | Identify a repositioning cruise with an outbound-only packaged flight that is bookable in DTS. Request should include only the outbound flight collection. |
| UC-003 | TC-009: Error Scenario – Request is rejected when the flight collections supplied do not match the declared air type | ** Given ** a request is sent to INT004.3, INT004.4, INT006, or INT007 declaring ` airType ` = ` OUTBOUND_ONLY ` but includes a return flight collection ** When ** MuleSoft validates the request ** Then ** the request is rejected before reaching DTS and an error response is returned to the website indicating the inconsistency | Construct a request for a repositioning cruise with ` airType ` = ` OUTBOUND_ONLY ` that incorrectly includes a return flight collection. Test against INT004.3, INT004.4, INT006, and INT007 separately. |
| UC-004 | TC-010: Happy Path – A standard round-trip cruise package continues to search, price, and book without any change in behaviour | ** Given ** a customer searches for and books a standard cruise with a round-trip packaged flight ** When ** the request flows through INT002.x, INT005.2, INT004.3, INT004.4, INT006, and INT007 ** Then ** all interfaces behave exactly as before — both outbound and return flight collections are present throughout, DTS receives the round-trip indicator, and the booking completes successfully with no one-way banners displayed | Identify a standard (non-repositioning) cruise with a round-trip packaged air category. Use an existing test booking that covers the full funnel end-to-end to confirm no regression. |
| UC-004 | TC-011: Alternative Path – Existing callers that send the legacy one-way flag instead of airType continue to be handled correctly | ** Given ** a request is sent to INT004.3, INT004.4, INT006, or INT007 without the new ` airType ` field but with the legacy one-way indicator populated ** When ** MuleSoft processes the request ** Then ** the legacy field is used to determine the one-way indicator sent to DTS, and the request is processed successfully without error — existing integrations that have not yet adopted ` airType ` are unaffected | Construct a request for a round-trip cruise that omits ` airType ` and includes only the legacy one-way field set to false. Test against INT004.3, INT004.4, INT006, and INT007 — confirm the legacy field exists on each interface before running this scenario. |