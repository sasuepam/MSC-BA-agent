# INT142 Prepaid Bookings: Excursions and Onboard Services Fields Added

## Change Requests

---

Type: CR
Summary: INT142 – Add new fields to prepaid bookings response (excursions and onboard services)
Description:
  Change Scope: INT142 (MyMSC Booking Details) — enrich the API response for prepaid items with additional fields currently missing from the response. This change covers both excursions and onboard services where applicable.

  **Fields added to all prepaid items (excursions and onboard services):**
  - `longDescription`: sourced from the item info object returned by the relevant upstream provider API. Direct string mapping, no conversion required. Source path within onboard services item info object is [TO BE CONFIRMED].

  **Fields added to prepaid excursion items only:**
  - `duration`: sourced from the upstream excursions API. Data type, unit, and format (e.g. integer minutes, ISO 8601 duration string) are [TO BE CONFIRMED].
  - `MinPaxRequired`: mapped from `minimumPassengersRequired` in the upstream excursions API. Source and target data types are [TO BE CONFIRMED].
  - `ActivityMoreInfo` object: structured object containing the following flags sourced from the upstream excursions API:

  | Source Field (Excursions API)   | Target Field (ActivityMoreInfo) | Type             |
  |---------------------------------|---------------------------------|------------------|
  | isBestSeller                    | BestSeller                      | Boolean          |
  | isBusTransportAvailable         | Bus                             | Boolean          |
  | isInvolvesWalking               | ByFoot                          | Boolean          |
  | isCulturalActivity              | Cultural                        | Boolean          |
  | isDrinkIncluded                 | Drink                           | Boolean          |
  | isFamilyFriendlyActivity        | ForFamily                       | Boolean          |
  | isMealIncluded                  | Lunch                           | Boolean          |
  | isFilmingAllowed                | NoFilm                          | Boolean          |
  | isGuideAvailable                | NoGuide                         | Boolean          |
  | guideLanguageCodes              | GuideLang                       | Array of strings |
  | isShoppingIncluded              | Shopping                        | Boolean          |
  | isSnackIncluded                 | Snack                           | Boolean          |
  | isSwimmingIncluded              | Swim                            | Boolean          |
  | isTastingIncluded               | Tasting                         | Boolean          |
  | isTourActivity                  | Tour                            | Boolean          |
  | isWalkingDifficulty             | WalkingDifficulty               | Boolean          |
  | isWheelchairFriendly            | Wheelchair                      | Boolean          |
  | isLimitedSeats                  | NbrMaxWaitList                  | Boolean          |
  | isBestRated                     | BestRated                       | Boolean          |

  The `ActivityMoreInfo` object is not applicable to prepaid onboard service items.

  Items requiring SA confirmation before implementation:
    - `NoFilm`: source field `isFilmingAllowed = true` means filming IS allowed; target field name implies the inverse. Boolean inversion semantics are [TO BE CONFIRMED].
    - `NoGuide`: source field `isGuideAvailable = true` means a guide IS available; target field name implies the inverse. Boolean inversion semantics are [TO BE CONFIRMED].
    - `NbrMaxWaitList`: source field `isLimitedSeats` is boolean, but the target field name implies a numeric count. Whether the target type is boolean or numeric is [TO BE CONFIRMED].
    - `GuideLang`: format of language codes returned by the excursions API (e.g. ISO 639-1) is [TO BE CONFIRMED].

  Rationale: Customers viewing the "Already Purchased" section of the MyMSC private area are missing key details on their purchased excursions and onboard services. This change aligns the INT142 response with the data available from upstream providers, enabling the frontend to display complete and accurate information on the "Already Purchased" card.

  Resources:
    - Mule Specification Document: [TO BE CONFIRMED]
    - High Level Architecture Document: [TO BE CONFIRMED]
    - API Documentation: [TO BE CONFIRMED]
    - Confluence Page: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/3911614639 (access restricted — contents [TO BE CONFIRMED])

Acceptance Criteria (BDD):
  Given an authenticated customer has a booking containing a prepaid excursion
  When the customer requests their booking details via INT142
  Then the response returns HTTP 200
  And the prepaid excursion item includes `longDescription`, `duration`, `MinPaxRequired`, and an `ActivityMoreInfo` object
  And all boolean fields within `ActivityMoreInfo` are returned as boolean type
  And `ActivityMoreInfo.GuideLang` is returned as an array of strings

  Given an authenticated customer has a booking containing a prepaid onboard service
  When the customer requests their booking details via INT142
  Then the response returns HTTP 200
  And the prepaid onboard service item includes a `longDescription` field
  And `duration`, `MinPaxRequired`, and `ActivityMoreInfo` are absent from the onboard service item

  Given a prepaid excursion where the upstream excursions API returns `isFilmingAllowed = true`
  When the customer requests their booking details via INT142
  Then `ActivityMoreInfo.NoFilm` reflects the agreed inversion logic confirmed by the SA
  And the value is [TO BE CONFIRMED] pending SA confirmation

  Given a prepaid excursion where the upstream excursions API returns `isGuideAvailable = true`
  When the customer requests their booking details via INT142
  Then `ActivityMoreInfo.NoGuide` reflects the agreed inversion logic confirmed by the SA
  And the value is [TO BE CONFIRMED] pending SA confirmation

  Given an unauthenticated request is made to INT142
  When the request is processed
  Then the response returns HTTP 401 Unauthorised
  And no booking data is returned
