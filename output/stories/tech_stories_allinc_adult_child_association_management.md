# Tech Stories – ALLINC Adult–Minor Association Management

Feature: MS: MyMSC All inclusive item relationship in DTS  
Spec: functional_spec_allinc_adult_child_association_management.html  
Confluence: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/5381554199

---

## STORY 1 — INT130: Migrate ALLINC adult–minor relationship fields from CMS to DTS

**Summary:** INT130 – Migrate ALLINC adult–minor relationship source from AEM CMS to DTS /obs/prices

**Story:**  
As a MuleSoft developer I want to replace the CMS-sourced ALLINC adult–minor relationship data in INT130 with DTS `/obs/prices` data so that the relationship source is consistent and authoritative, reducing the risk of CMS/DTS divergence.

---

### Context

INT130 currently enriches ALLINC items with adult–minor relationship data obtained via the AEM CMS `getOnBoardServices` GraphQL query. DTS `/obs/prices` now returns a `linked-item-code` field on adult ALLINC items, providing an authoritative source for the same relationship. The CMS relationship fields are to be deprecated; both old and new fields must be returned during the migration window.

---

### Implementation Requirements

#### Step 1 – Build `itemsThatHaveRelationship` from DTS `/obs/prices`

In the SAPI layer, after receiving the DTS `/obs/prices` response (`DtsJsonOnboardServicesResponse{}.Result{}.ObsType[].Obs[]`):

1. Filter to items where `obs-type = ALLINC`
2. Filter further to items where `linked-item-code` is present (non-null/non-empty)
3. For each such item, add **both** the item's own code **and** the value of `linked-item-code` to the array `itemsThatHaveRelationship`
4. Items **not** in this array are standalone ALLINC items — return them without relationship arrays

> **Example:** Adult items 131N9 (linked-item-code = 135N9), 133N9 (linked-item-code = 135N9), 144N9 (linked-item-code = 145N9)  
> → `itemsThatHaveRelationship = { 131N9, 133N9, 134N9, 135N9, 144N9, 145N9 }`  
> (134N9 would be added if it also returns linked-item-code = 135N9)

---

#### Step 2 – Enrich items with new DTS-sourced relationship fields

For each item **in** `itemsThatHaveRelationship`:

**Adult items** (`is-for-adult = true` OR `is-for-senior = true`):

| Response field | Value | DTS source |
|---|---|---|
| `onboardServices[N].linkedItems.minors[N]` | `[linked-item-code]` — size-1 array | `DtsJsonOnboardServicesResponse{}.Result{}.ObsType[].Obs[].linked-item-code` |

**Minor items** (`is-for-child = true` OR `is-for-junior = true` OR `is-for-infant = true`):

| Response field | Value | DTS source |
|---|---|---|
| `onboardServices[N].linkedItems.adults[N]` | All adult item codes whose `linked-item-code` equals this item's code — reverse lookup across OBS response | `DtsJsonOnboardServicesResponse{}.Result{}.ObsType[].Obs[].linked-item-code` |

> Note: `linkedItems.minors` always has length 1 (one adult links to one minor). `linkedItems.adults` may have multiple entries (many adults can share the same minor, e.g. 131N9, 133N9, 134N9 all linking to 135N9).

---

#### Step 3 – Retain deprecated CMS-sourced fields (earmarked for removal)

Continue calling AEM CMS `getOnBoardServices` for non-relationship content enrichment. The following fields must continue to be populated from CMS — they are **deprecated** but retained until consumer migration is confirmed:

| Response field | Status | CMS source |
|---|---|---|
| `onboardServices[n].prepaidItems[n].serviceCodes.adults[]` | **DEPRECATED** – to be removed in future iteration | `data.prepaidData.prepaidItems[N].adultRelatedServiceCodes[]` |
| `onboardServices[n].prepaidItems[n].serviceCodes.minors[]` | **DEPRECATED** – to be removed in future iteration | `data.prepaidData.prepaidItems[N].minorsRelatedServiceCodes[]` |

---

### Acceptance Criteria

- Adult ALLINC items in `itemsThatHaveRelationship`: response contains `linkedItems.minors = [<linked-item-code value>]` (size-1 array)
- Minor ALLINC items in `itemsThatHaveRelationship`: response contains `linkedItems.adults = [<codes of all adult items pointing to this minor>]` (1 or more entries, via reverse lookup)
- Both deprecated fields `serviceCodes.adults[]` and `serviceCodes.minors[]` remain populated from CMS
- ALLINC items **not** in `itemsThatHaveRelationship` are returned without `linkedItems` arrays — no null-pointer exception
- No breaking change: both new and deprecated fields returned simultaneously

### Dependencies
None (uses existing DTS `/obs/prices` call already in INT130 SAPI)

---
---

## STORY 2 — INT139/INT140: Replace CMS-based ALLINC combination validation with DTS-derived logic

**Summary:** INT139/INT140 – Replace CMS ALLINC adult–minor combination check with DTS /obs/prices validation

**Story:**  
As a MuleSoft developer I want to replace the CMS-sourced ALLINC combination validation in INT139 and INT140 with DTS `/obs/prices`-derived logic so that the permitted adult–minor combinations are always consistent with DTS data.

---

### Context

INT139 (PriceToBook) and INT140 (Book) currently validate that minor ALLINC items are permitted associates of adult ALLINC items in the request using CMS relationship data. This story replaces that validation with DTS-derived `allowedMinorItems`, built from `linked-item-code` on `/obs/prices` adult items. The same validation logic applies to both INT139 and INT140.

---

### Implementation Requirements

#### ALLINC combination validation (apply to both INT139 and INT140)

Before calling DTS for price/booking, run the following validation:

1. **Build `itemsThatHaveRelationship`** — same algorithm as INT130 (re-use from SAPI layer)

2. **Build `allowedMinorItems`** — for each ALLINC adult item in the request, add its `linked-item-code` to `allowedMinorItems`

3. **Validate adult passenger coverage** — for each ALLINC adult item in the request:
   - Verify the item is present for all applicable adult/senior passengers (`is-for-adult = true` OR `is-for-senior = true`)
   - Verify the item is not present for non-applicable passengers

4. **Validate minor passenger coverage** — for each ALLINC adult item in the request:
   - If the related minor item is returned by `/obs/prices` (i.e., applicable minor passengers exist on the booking): verify the minor item is present for all applicable minor passengers (`is-for-child`, `is-for-junior`, or `is-for-infant = true`)
   - If the related minor item is **not** returned by `/obs/prices` (no applicable minor passengers on booking): the adult item has no relationship constraint — treat as standalone ALLINC

5. **Validate no unauthorised minor items** — after iterating all adult items: verify that no ALLINC minor item in the request has a code that is **not** in `allowedMinorItems`
   > This catches the case where a consumer includes a minor package without its corresponding adult package.

6. **On validation failure**: reject with HTTP 422 and a specific error before calling DTS. No DTS price/booking call is made.

7. **On validation pass**: proceed with existing price/booking flow.

> **Example rejection:** Request contains `[131N9, 135N9, 145N9]`. `allowedMinorItems = [135N9]` (derived from 131N9's `linked-item-code`). `145N9` is a minor not in `allowedMinorItems` → **reject**.

---

#### Passenger count validation (per-passenger ALLINC items, priceBasis = "P")

For ALLINC items priced per passenger:

1. Determine eligible passengers using DTS applicability flags (`is-for-adult`, `is-for-senior`, `is-for-child`, `is-for-junior`, `is-for-infant`)
2. Passengers not matching any flag: skipped (not eligible)
3. All eligible passengers must be included in the request — partial passenger requests are not permitted
4. If no applicable passengers exist for the item: request is valid without that item
5. On missing eligible passenger: reject with HTTP 422

---

### Acceptance Criteria

- Valid adult + permitted minor in request: HTTP 200, price/booking proceeds
- Adult only (no applicable minor passengers on booking): HTTP 200, no error raised
- Minor item code not in `allowedMinorItems`: HTTP 422 before DTS call; DTS is NOT called
- Minor item linked to a different adult than the one in the request: HTTP 422
- All eligible passengers present for per-pax ALLINC item: HTTP 200
- Missing eligible passenger for per-pax ALLINC item: HTTP 422

### Dependencies
None (uses existing DTS `/obs/prices` response already available in INT139/INT140 SAPI)

---
---

## STORY 3 — INT137V2: Replace CMS-based ALLINC refund validation with DTS getBookings data

**Summary:** INT137V2 – Replace CMS ALLINC refund validation with DTS getBookings LinkedItemCode logic

**Story:**  
As a MuleSoft developer I want to replace the CMS-sourced ALLINC refund combination validation in INT137V2 with DTS `getBookings` relationship data so that refund validation is consistent with the DTS-authoritative source.

---

### Context

INT137V2 currently validates that ALLINC minor items in a refund request are linked to the adult item in the same request using CMS relationship data. This story migrates that validation to use `LinkedItemCode` from DTS `getBookings` (R113). It also enforces that a single refund request cannot span unrelated ALLINC pairs, and that all passengers holding an item are included in the refund.

---

### Implementation Requirements

#### ALLINC combination validation for refund

1. **Identify relationships from `getBookings`** — filter to `ServiceType = ALLINC` AND `LinkedItemCode` present in the booking items

2. **Build `expectedMinorItems`** — for each ALLINC adult item in the refund request, add its `LinkedItemCode` to `expectedMinorItems`

3. **Enforce single-pair constraint** — verify `expectedMinorItems` contains **at most 1 value**. If adult items in the request point to different minor items: reject with HTTP 422.  
   > Note: this scenario is not expected given the DTS constraint that no booking contains two unrelated ALLINC pairs, but must be guarded.

4. **Validate minor items in request** — verify any ALLINC minor item present in the refund request is in `expectedMinorItems`. This catches refund of a minor without its corresponding adult.

5. **Validate minor item coverage** — for each minor in `expectedMinorItems`:
   - If at least one passenger in the booking holds this minor item (in BKD status): the refund request **must** include this minor item
   - If no passenger holds this minor item: the request should **not** include it and must proceed without it
   - If the minor item is absent from `getBookings` `LinkedItemCode` entirely: treat adult as standalone ALLINC with no relationship constraint

6. **On validation failure**: reject with HTTP 422 and a specific error before calling DTS.

---

#### All-passenger completeness validation (applies to all ALLINC items being refunded)

1. For the ALLINC ItemCode being refunded, identify **all passengers in the booking** holding that ItemCode (across all prebookings, not only those in the current refund request)
2. All such passengers must be included in the refund request — partial-passenger ALLINC refunds are not permitted
3. On missing passenger: reject with HTTP 422

---

### Acceptance Criteria

- Valid adult + minor pair, all relevant passengers in request: HTTP 200, refund processed
- Minor item not in `expectedMinorItems`: HTTP 422, refund not processed
- `expectedMinorItems` contains more than 1 value: HTTP 422 (at-most-one constraint)
- Missing passenger who holds the ALLINC ItemCode: HTTP 422; check spans all prebookings
- Adult item with no applicable minor passengers (no `LinkedItemCode` returned): treated as standalone ALLINC, refund proceeds for all passengers holding that item

### Dependencies

- **RES2-29207** — DTS must return `LinkedItemCode` on minor package items in `getBookings`. Until delivered, minor items will lack `LinkedItemCode` and adult items will be treated as standalone ALLINC.
- **RES2-29208** — DTS `ItemPaxApplicability` field (used for passenger classification in validation)

---
---

## STORY 4 — INT142: Add ALLINC relationship fields to booking details response

**Summary:** INT142 – Add linkedItem and itemApplicability fields to purchased ALLINC items in booking details

**Story:**  
As a MuleSoft developer I want to add three new fields to the INT142 response for purchased ALLINC items so that consumers can identify adult–minor item relationships and passenger applicability for items they have already booked.

---

### Context

INT142 currently returns purchased prepaid items without any adult–minor relationship data. This story adds three new fields sourced from DTS `getBookings` (R113) after DTS delivers RES2-29207 and RES2-29208.

Reference: https://msccruises.atlassian.net/wiki/spaces/DTP/pages/3867181732

---

### New Response Fields

All three fields are added at the path: `prepaid.bookings[N].onboardServices[N]`

| Field | Type | Description | DTS source |
|---|---|---|---|
| `linkedItem.minor` | string | Code of the related minor ALLINC item. Populated for **adult items** only. | `DtsRetrieveBookingResponseMessage.PreBookings{}.PreBooking{[N]}.ItemInfo{[N]}.LinkedItemCode` |
| `linkedItem.adult` | string | Code of the related adult ALLINC item. Populated for **minor items** only. | `DtsRetrieveBookingResponseMessage.PreBookings{}.PreBooking{[N]}.ItemInfo{[N]}.LinkedItemCode` |
| `itemApplicability[]` | array of string | Passenger types to which this item applies. | `DtsRetrieveBookingResponseMessage{}.PreBookings{}.PreBooking[N].ItemInfo[].ItemPaxApplicability` |

#### `itemApplicability[]` enum mapping

Map `ItemPaxApplicability` character values to the following strings:

| DTS value | Response string |
|---|---|
| A | `adult` |
| S | `senior` |
| J | `junior` |
| C | `child` |
| I | `infant` |

---

### Item classification (to determine which `linkedItem` field to populate)

Use `ItemPaxApplicability` (RES2-29208) to classify items:

| Classification | Condition |
|---|---|
| Adult item | `ItemPaxApplicability` contains "A" or "S" |
| Minor item | `ItemPaxApplicability` contains "C", "J", or "I" |

Mapping logic:
- **Adult item**: populate `linkedItem.minor` from `LinkedItemCode`; leave `linkedItem.adult` null/absent
- **Minor item**: populate `linkedItem.adult` from `LinkedItemCode`; leave `linkedItem.minor` null/absent

> **Example** (booking with 131N9 adult and 135N9 minor):  
> `131N9: linkedItem.minor = "135N9", linkedItem.adult = null, itemApplicability = ["adult"]`  
> `135N9: linkedItem.minor = null, linkedItem.adult = "131N9", itemApplicability = ["child"]`

---

### Graceful handling before DTS dependencies are delivered

If `ItemPaxApplicability` is absent (RES2-29207/RES2-29208 not yet delivered):
- `linkedItem.adult`, `linkedItem.minor`, and `itemApplicability[]` must be **omitted or null** in the response
- All other item fields must continue to be returned correctly
- No null-pointer exception or 5xx error

---

### Acceptance Criteria

- Adult ALLINC item with `LinkedItemCode` returned: `linkedItem.minor = <LinkedItemCode value>`, `linkedItem.adult = null`
- Minor ALLINC item with `LinkedItemCode` returned: `linkedItem.adult = <LinkedItemCode value>`, `linkedItem.minor = null`
- `itemApplicability[]` populated with mapped string values (e.g. `["adult"]`, `["child", "junior"]`)
- If DTS `ItemPaxApplicability` absent: all three new fields absent/null; no 5xx error; all other fields correct
- DTS `getBookings` error: HTTP 502/503; error message returned; no unhandled exception

### Dependencies

- **RES2-29207** — DTS must return `LinkedItemCode` on minor items in `getBookings`
- **RES2-29208** — DTS must return `ItemPaxApplicability` on all prepaid items in `getBookings`
- Chiara/Filippo to retest applicability field and raise a DTS bug if still missing after RES2-29208 delivery
