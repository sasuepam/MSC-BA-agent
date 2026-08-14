# MyMSC Item Applicability – Related All-Inclusive Item Unavailable from DTS

---

Type: CR
Summary: Item Applicability Validation – Allow purchase when related all-inclusive item is not returned by DTS
Jira Ticket: DTTP25-37538
Description:
  Change Scope: Interfaces INT139 (prepaid price) and INT140 (prepaid booking). The validation logic applied to all-inclusive onboard service items with an adult/minor CMS relationship is updated to handle the scenario where a related item is absent from the DTS onboard services list because no passenger in the booking is eligible to purchase it.

  Currently, when an all-inclusive adult item is included in a website request and CMS defines a related minor item for that adult item, the validation requires the minor item to be present in the DTS onboard services list. If the minor item is absent from DTS — even when the website has not attempted to include it in the request — the entire request is rejected. The same applies symmetrically: a missing adult item related to a present minor item also causes rejection.

  Under the new logic, if a related adult or minor all-inclusive item is absent from the DTS onboard services list and the website has also not included that item in the request, the validation must allow the request to proceed without enforcing the related item. The related item is not enforced because it cannot be purchased by any eligible passenger and therefore cannot be required.

  This change does not alter the existing rejection behaviour when the website explicitly includes a related item in the request but that item is absent from the DTS onboard services list. In that case the request must still be rejected, as the item cannot be purchased.

  All other all-inclusive validation logic — including applicability per passenger type using item-specific age rules and the is-for-adult / is-for-child / is-for-junior / is-for-infant flags — remains unchanged.

  The change applies to both INT139 and INT140 as both interfaces share the same all-inclusive validation logic.

  Rationale: DTS only returns onboard service items for which at least one passenger in the booking is eligible. For some all-inclusive package configurations, a related minor item will not appear in the DTS onboard services list when no minor passenger in the booking meets the item's eligibility criteria (for example, an infant below the minimum purchasable age for that package). The existing validation treats absence of the related item as a blocking condition, rejecting the request even when the website has correctly not included the uneligible item. This prevents eligible adult passengers from purchasing their all-inclusive package in bookings that include an ineligible minor, breaking the MyMSC prepaid items purchase journey for those bookings.

  Resources:
    - Architecture Document: MS Arch: MyMSC Item Applicability – https://msccruises.atlassian.net/wiki/spaces/DTP/pages/5057413209/MS+Arch+MyMSC+Item+Applicability
    - Open Point: DTTP25-37538 – https://smartship.atlassian.net/browse/DTTP25-37538
    - Mule Specification Document: [TO BE CONFIRMED]

Acceptance Criteria (BDD):
  Scenario: Related minor item absent from DTS and not included in request – request allowed
  Given a booking contains adult passengers and a minor passenger for whom a related all-inclusive minor item is not purchasable, and the website requests an all-inclusive adult item for all applicable adult passengers, and CMS defines the adult item as related to a minor item, and the related minor item is absent from the DTS onboard services list for the cruise, and the website request does not include the related minor item for any passenger
  When the all-inclusive validation is applied in INT139 and INT140
  Then the request is accepted and the related minor item is not enforced, because it cannot be purchased by any passenger in the booking and was not included in the request

  Scenario: Related minor item absent from DTS but explicitly included in request – request rejected
  Given a booking contains adult passengers and a minor passenger, and the website requests an all-inclusive adult item for all applicable adult passengers and also includes the related minor item for the minor passenger, and CMS defines the adult item as related to that minor item, and the related minor item is absent from the DTS onboard services list for the cruise
  When the all-inclusive validation is applied in INT139 and INT140
  Then the request is rejected because the website explicitly included an item that cannot be purchased, regardless of whether the minor passenger would otherwise be eligible

  Scenario: Related minor item present in DTS but applicable minor passenger not covered – request rejected
  Given a booking contains adult passengers and a minor passenger, and the website requests an all-inclusive adult item for all applicable adult passengers, and CMS defines the adult item as related to a minor item, and the related minor item IS present in the DTS onboard services list for the cruise, and the minor passenger is applicable for the minor item but has not been included in the request for that item
  When the all-inclusive validation is applied in INT139 and INT140
  Then the request is rejected because all applicable minor passengers must purchase the related minor item when it is available and purchasable

  Scenario: Both adult and minor items present in DTS and all applicable passengers covered – request allowed (regression)
  Given a booking contains adult passengers and a minor passenger, and the website requests an all-inclusive adult item for all applicable adult passengers and the related minor item for all applicable minor passengers, and both items are present in the DTS onboard services list for the cruise
  When the all-inclusive validation is applied in INT139 and INT140
  Then the request is accepted and proceeds to pricing and booking — existing behaviour is unchanged
