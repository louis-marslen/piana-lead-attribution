---
name: bdr-lead-attribution-brief
description: Generates a HubSpot lead attribution brief for sales reps (BDRs, AEs, etc.) who own a "Propriétaire Prospection" pool of companies. The brief tells the user how many leads to assign per rep to reach their target pool size, and proposes NAF × department filter groups (lookalike of recent wins) to add to their HubSpot master list. Use this skill whenever the user asks for a lead attribution brief, asks how many leads to add to their BDRs/AEs/sales reps, asks for lookalike NAF filters based on recent wins, or wants to refresh the prospecting pool of their sales team. Trigger even if the user just says "fais le brief d'attribution" or "refais le brief des leads" — they're almost certainly asking for this.
---

# BDR Lead Attribution Brief

This skill generates a structured brief telling the user (a RevOps operator at Piana) how to attribute new leads to their sales reps in HubSpot, using NAF × geographic lookalike of recent won deals.

## When to use this skill

Trigger this skill when the user asks for:
- "Le brief d'attribution des leads"
- "Combien de leads je dois rajouter à mes BDR/AE"
- "Refais-moi le brief pour les BDR"
- "Les filtres NAF/géo à ajouter à ma liste master"
- Any variant where the user wants to refresh their sales reps' prospecting pool with lookalike companies of recent wins.

## Output format (mandatory)

The final brief MUST contain exactly two sections, in this order, and nothing else (no extra commentary unless the user asks):

### Section 1 — Leads à attribuer par sales rep

A markdown table with columns: `Sales rep | Stock actuel | Cible | À attribuer`. Add a `Total` row.

### Section 2 — Liste HubSpot créée

A direct link to the HubSpot list that was automatically created via the HubSpot API, plus a summary table of the NAF × geo buckets included (columns: `Groupe | Volume`). The list is ready to use — the user just clicks the link to view and assign leads.

## Workflow

Follow this sequence. Never skip a step.

### Step 1 — Capture parameters

Ask the user (or infer from conversation) for:
- **List of sales reps** (default: Adam Gruat, Nathan dellasantina, Rayane Sellal — the 3 current BDRs at Piana).
- **Target pool size per rep** (default: 250). Each rep may have a different target — BDRs typically 250, AEs may have a higher target.

If new reps are mentioned without targets, ask for their target. Don't assume.

### Step 2 — Identify the sales reps' HubSpot owner IDs

Call `HubSpot:search_owners` with each rep's first name (or full name). Capture the `ownerId` for each.

If a name returns 0 results, try variations (last name, first name only, full name without accents). If still nothing, flag it to the user.

### Step 3 — Count current "Propriétaire Prospection" stock per rep

For each rep, call `HubSpot:search_crm_objects` on `companies` with:
```
filterGroups: [{ filters: [{ propertyName: "proprietaire_prospection", operator: "EQ", value: "<ownerId>" }] }]
```

Read the `total` field. This is the current stock.

Compute `À attribuer = max(0, Target - Stock actuel)` for each rep. Sum to get total leads needed.

### Step 4 — Pull recent won deals (30-day window first, fallback to 90-day)

The "won" stage at Piana is identified by stage entry property `hs_v2_date_entered_2600062176`. Use this property to count won deals — not `hs_is_closed_won` (which over-counts) and not other stage-entry properties.

Compute the cutoff date 30 days ago in ISO format (`YYYY-MM-DD`).

Call `HubSpot:search_crm_objects` on `deals` with:
```
filterGroups: [{ filters: [{ propertyName: "hs_v2_date_entered_2600062176", operator: "GTE", value: "<30d-ago>" }] }]
limit: 200
properties: ["dealname"]
```

Collect all deal IDs.

### Step 5 — Pull associated companies with their NAF and postal code

Call `HubSpot:search_crm_objects` on `companies` with `associatedWith` filter listing the deal IDs from Step 4. Up to 29 IDs per filterGroup, max 5 filterGroups per call (i.e. 145 deals per call — chain calls if needed).

Properties to fetch: `["name", "libelle_code_naf", "code_naf", "zip", "departement_code"]`.

Deduplicate companies (some deals share the same company).

### Step 6 — Assess if 30-day signal is strong enough

The 30-day signal is "strong" if at least 3 distinct libellés NAF have ≥ 2 wins each. Otherwise it's too sparse — fall back to 90 days.

If too sparse, repeat Steps 4-5 with a 90-day cutoff.

### Step 7 — Cross NAF × department to build buckets

For each libellé NAF present in the wins (excluding any explicitly excluded by the user — by default, exclude `4941A` and `4941B` "Transports routiers de fret de proximité/interurbains" because Piana wants to deprioritize this segment):

1. Collect the postal codes of the wins for that libellé.
2. Extract the department code (`zip[:2]`, with the special case of Corsica `2A/2B` mapped to `20`).
3. If the libellé has wins in at least 2 distinct departments → build a "NAF × geo" bucket. Departments to include: the ones with wins + adjacent ones in the same INSEE region (see `skills/bdr-lead-attribution-brief/references/french_regions.md`).
4. If the libellé has wins in only 1 department (or 0 wins but is in the user's target NAF list) → either skip it OR include as a "national" bucket if its standalone volume is significant.

### Step 8 — Estimate the volume of each bucket

For each candidate bucket, call `HubSpot:search_crm_objects` on `companies` with the filters below.

**HubSpot caps at 6 filters per filterGroup**, so pick the 6 most impactful from the master list + bucket filters.

For **national buckets** (no dept filter) — 6 filters:
```
filterGroups: [{ filters: [
  { propertyName: "libelle_code_naf", operator: "EQ", value: "<naf>" },
  { propertyName: "ready_tbc", operator: "EQ", value: "1" },
  { propertyName: "proprietaire_prospection", operator: "NOT_HAS_PROPERTY" },
  { propertyName: "statut_de_prospection", operator: "NOT_HAS_PROPERTY" },
  { propertyName: "siret_2", operator: "HAS_PROPERTY" },
  { propertyName: "num_associated_deals", operator: "NOT_HAS_PROPERTY" }
] }]
limit: 1
```

For **geo buckets** (with dept filter) — 6 filters:
```
filterGroups: [{ filters: [
  { propertyName: "libelle_code_naf", operator: "EQ", value: "<naf>" },
  { propertyName: "departement_code", operator: "IN", values: [<depts>] },
  { propertyName: "ready_tbc", operator: "EQ", value: "1" },
  { propertyName: "proprietaire_prospection", operator: "NOT_HAS_PROPERTY" },
  { propertyName: "statut_de_prospection", operator: "NOT_HAS_PROPERTY" },
  { propertyName: "siret_2", operator: "HAS_PROPERTY" }
] }]
limit: 1
```

Read the `total`. This is the bucket's estimated volume.

**Note:** The pre-check still omits some master filters (address/city/zip IS_KNOWN, company_nb_open_leads < 1) due to the 6-filter limit, so volumes will be slightly overestimated (~10-20%). This is expected.

### Step 9 — Select the minimal set of buckets reaching ~1.5× the target

Sort candidate buckets by relevance (number of wins for that libellé) and by volume.

Greedy selection: pick buckets until the cumulative volume reaches ~1.5× the total leads needed (no more — the user explicitly wants a compact brief).

If no individual bucket reaches enough volume, broaden the geographic scope (department → region → national) for the highest-conviction libellés.

### Step 10 — Create the HubSpot list via API

Create the list by calling the HubSpot Lists API directly via `WebFetch`. No local script needed.

#### 10a — Build the filterBranch payload

The list uses a DNF (OR of ANDs) structure: `master_filters AND bucket_filters` for each bucket, OR'd together.

The master filters (AND'd) — use these EXACT JSON objects, do NOT change the operationType values:

```json
[
  {"filterType":"PROPERTY","property":"proprietaire_prospection","operation":{"operator":"IS_UNKNOWN","operationType":"ALL_PROPERTY","includeObjectsWithNoValueSet":false}},
  {"filterType":"PROPERTY","property":"statut_de_prospection","operation":{"operator":"IS_UNKNOWN","operationType":"ALL_PROPERTY","includeObjectsWithNoValueSet":false}},
  {"filterType":"PROPERTY","property":"siret_2","operation":{"operator":"IS_KNOWN","operationType":"ALL_PROPERTY","includeObjectsWithNoValueSet":false}},
  {"filterType":"PROPERTY","property":"address","operation":{"operator":"IS_KNOWN","operationType":"ALL_PROPERTY","includeObjectsWithNoValueSet":false}},
  {"filterType":"PROPERTY","property":"city","operation":{"operator":"IS_KNOWN","operationType":"ALL_PROPERTY","includeObjectsWithNoValueSet":false}},
  {"filterType":"PROPERTY","property":"zip","operation":{"operator":"IS_KNOWN","operationType":"ALL_PROPERTY","includeObjectsWithNoValueSet":false}},
  {"filterType":"PROPERTY","property":"data___calc__nb_vehicles","operation":{"operator":"IS_KNOWN","operationType":"ALL_PROPERTY","includeObjectsWithNoValueSet":false}},
  {"filterType":"PROPERTY","property":"ready_tbc","operation":{"operator":"IS_EQUAL_TO","operationType":"NUMBER","value":1.0,"includeObjectsWithNoValueSet":false}},
  {"filterType":"PROPERTY","property":"company_nb_open_leads","operation":{"operator":"IS_LESS_THAN","operationType":"NUMBER","value":1.0,"includeObjectsWithNoValueSet":true}},
  {"filterType":"PROPERTY","property":"num_associated_deals","operation":{"operator":"IS_LESS_THAN","operationType":"NUMBER","value":1.0,"includeObjectsWithNoValueSet":true}}
]
```

For each bucket, append these filters to the master array:
- NAF filter: `{"filterType":"PROPERTY","property":"libelle_code_naf","operation":{"operator":"IS_EQUAL_TO","operationType":"MULTISTRING","values":["<exact libellé>"],"includeObjectsWithNoValueSet":false}}`
- Dept filter (if not national): `{"filterType":"PROPERTY","property":"departement_code","operation":{"operator":"IS_ANY_OF","operationType":"ENUMERATION","values":["<dept codes>"],"includeObjectsWithNoValueSet":false}}`

**Important:** Department codes have NO leading zeros (`"6"` not `"06"`). Use `ALL_PROPERTY` for IS_KNOWN/IS_UNKNOWN — never OWNER or STRING.

Each AND branch = master filters + bucket filters. The root filterBranch:
```json
{
  "filterBranchType": "OR",
  "filterBranchOperator": "OR",
  "filterBranches": [
    {
      "filterBranchType": "AND",
      "filterBranchOperator": "AND",
      "filterBranches": [],
      "filters": [ ...master_filters, ...bucket_filters ]
    }
  ],
  "filters": []
}
```

#### 10b — POST to create the list

Call via WebFetch:
```
POST https://api.hubapi.com/crm/v3/lists
Authorization: Bearer <HUBSPOT_TOKEN>
Content-Type: application/json

{
  "name": "[YYYY-MM-DD] BDR Leads List",
  "objectTypeId": "0-2",
  "processingType": "DYNAMIC",
  "filterBranch": <the DNF filterBranch from 10a>
}
```

Use the HubSpot token from environment variable `$HUBSPOT_TOKEN`.

Capture `listId` from the response.

#### 10c — Move to folder

```
PUT https://api.hubapi.com/crm/v3/lists/folders/move-list
Authorization: Bearer <HUBSPOT_TOKEN>
Content-Type: application/json

{"listId": "<listId>", "newFolderId": "1062490299"}
```

#### 10d — Get the actual list size

Wait a few seconds for HubSpot to process, then fetch the list:
```
GET https://api.hubapi.com/crm/v3/lists/<listId>
Authorization: Bearer <HUBSPOT_TOKEN>
```

Read the `listSize` (or `size`) field from the response. This is the **real** total volume to display in the brief — not the pre-check estimates from Step 8.

#### 10e — Build the list URL

`https://app-eu1.hubspot.com/contacts/26080063/objectLists/<listId>`

### Step 11 — Render the brief

Use the template in `skills/bdr-lead-attribution-brief/references/brief_template.md`. Section 2 now contains:
- A summary of the buckets selected (count, total volume, ratio vs need)
- The direct link to the HubSpot list just created

### Step 12 — Send to Slack

Post the rendered brief to the Slack channel `#bdr-lead-attribution-brief` (channel ID: `C0B4W2YF9EU`). Use `Slack:slack_send_message` to post the brief as a single message.

Then stop. Don't add commentary, analysis, or caveats unless the user explicitly asks. The brief is the deliverable.

## What NOT to include in the brief

- Do NOT list the master criteria (ready_tbc, lead_count, etc.) — the user already has them in their master list.
- Do NOT include charts or visualizations unless the user explicitly asks.
- Do NOT pad the brief with intermediate analysis — just the two sections.

## Reference files

- `skills/bdr-lead-attribution-brief/references/hubspot_properties.md` — HubSpot property names, owner IDs format, common pitfalls (e.g., `ready_tbc` is `"1"` not `true`, `code_naf` not `naf_code`).
- `skills/bdr-lead-attribution-brief/references/french_regions.md` — Mapping of French INSEE regions to their constituent department codes (used to expand geographic scope).
- `skills/bdr-lead-attribution-brief/references/brief_template.md` — The exact markdown template for the final brief output.

## External dependencies

- **HubSpot API** — Used via WebFetch to create the dynamic list (the HubSpot MCP doesn't support list creation). Token: Private App with scopes `crm.lists.read`, `crm.lists.write`.
- **HubSpot MCP** — Used for CRM searches (owners, companies, deals).
- **Slack MCP** — Used to post the brief to `#bdr-lead-attribution-brief` via `Slack:slack_send_message`.
