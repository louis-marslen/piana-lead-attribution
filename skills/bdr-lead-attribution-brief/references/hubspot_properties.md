# HubSpot properties — Piana account

Property names and quirks specific to Piana's HubSpot setup. Always use these exact names when calling `HubSpot:search_crm_objects`.

## Companies — key properties

| Property name (internal) | Label (UI) | Type / Format | Notes |
|---|---|---|---|
| `proprietaire_prospection` | Propriétaire Prospection | Owner ID (string) | The BDR/AE who owns the prospecting pool. Currently mostly empty on the account. |
| `hubspot_owner_id` | Company owner | Owner ID | Different from `proprietaire_prospection` — represents general ownership. |
| `ready_tbc` | Ready to be called ? | String enum `"1"` or unknown | **Important: filter value is `"1"` not `true`.** |
| `lead_count` | Compteur lead | Number | Filter `= "0"` for companies never converted. |
| `num_associated_deals` | Nombre de transactions associées | Number | **Always unknown for 0 deals** — use `NOT_HAS_PROPERTY` to filter "no deal". |
| `data___calc__nb_vehicles` | [Data - Calc] Nb Vehicles | Number (string) | Filter `>= "10"` for the typical addressable target. Note the triple underscore. |
| `siret_2` | SIRET | String | Use `HAS_PROPERTY` to filter SIRET present. |
| `address` | Street Address | String | Use `HAS_PROPERTY` to filter address present. |
| `zip` | Postal Code | String | Sometimes contains trailing whitespace — `.strip()` before slicing department. |
| `departement_code` | Département_Code | String (2 chars) | Format `"XX"`. Use this for filtering by department, never derive from zip in the HubSpot query. |
| `code_naf` | [INSEE] Code NAF | String | Format `"4941B"` — no dot, uppercase letter suffix. **NOT `naf_code`** which exists but is empty.|
| `libelle_code_naf` | [INSEE] Libellé code NAF | String | The human-readable libellé. Match exactly (case + accents). |
| `categorie_naf` | Catégorie NAF | String enum | Custom Piana classification — too coarse for lookalike, use `libelle_code_naf` instead. |

## Deals — key properties

| Property name (internal) | Label (UI) | Notes |
|---|---|---|
| `hs_v2_date_entered_2600062176` | Date entered (Piana's canonical Won stage) | The stage entry date for Piana's Closed Won stage. **This is the user's reference for "won deals".** Do NOT use `hs_v2_date_entered_2824474818` (a different Close Won stage in another pipeline that over-counts) or `hs_is_closed_won` (covers all pipelines and over-counts). |
| `hs_is_closed_won` | Is Closed Won | Use `EQ "true"` for general closed-won status (covers all pipelines). |
| `dealstage` | Deal Stage | Stage ID. Piana's canonical Won stage = `2600062176`. (Note: stage `2824474818` exists in another pipeline as "Close Won 🎉 Hunting" but is NOT the one to use for win analysis.) |
| `pipeline` | Pipeline | Pipeline ID. Hunting = `2060022992`. |

## Filter syntax pitfalls

- **6 filters max per filterGroup**. To AND more, you cannot — restructure or accept the limitation.
- **5 filterGroups max per query** (OR'd together).
- **`associatedWith` filter**: max ~29 IDs per `objectIdValues` array in practice. To pull companies linked to many deals, batch IDs into multiple filterGroups (OR'd together — equivalent to a single IN since each company appears once in results).
- **`HAS_PROPERTY` / `NOT_HAS_PROPERTY`** don't take a `value` field. Check property presence.
- **`IN` operator** uses `values` (array), not `value` (single).

## Owner IDs (current Piana BDRs at time of skill creation)

- Adam Gruat: `33334662`
- Nathan dellasantina: `33371638`
- Rayane Sellal: `32501903`

Always re-fetch via `HubSpot:search_owners` — these can change if a BDR is replaced.
