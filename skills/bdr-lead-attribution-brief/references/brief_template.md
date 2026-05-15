# Brief template

Use this EXACT structure when rendering the final brief.

---

# [Week {YYYY-MM-DD}] Lead Attribution Report

## 📊 1. État des pipelines

| {sales_rep_role} | Stock actuel | Cible | À attribuer |
|---|---|---|---|
| {name} | {current_stock} | {target} | **{to_assign}** |
| ... | ... | ... | ... |
| **Total** | | | **{total_to_assign}** |

---

## 🎯 2. Base de leads à attribuer (deals recently won lookalikes)

| Groupe | Deals gagnés | Volume estimé |
|---|---|---|
| **{N} — {bucket_name}** | {wins_count} | ~{volume} |
| ... | ... | ... |
| **Taille réelle de la liste** | | **{list_size}** |

👉 **[Ouvrir la liste dans HubSpot]({hubspot_list_url})**

---

## Style rules

- Use `**` (bold) only on the bucket name and on `Taille réelle`, never elsewhere in the table.
- Volume numbers prefixed with `~` for estimates.
- Geographic scope in the bucket name uses simple region terms (e.g. "PACA + Occitanie + IDF", "national", "Auvergne-Rhône-Alpes").
- The libellé NAF in the filters column is wrapped in backticks and reproduces the value EXACTLY as it appears in HubSpot (including double spaces if any, e.g. "Commerce de gros  de bois...").
- Department codes are 2-character strings, comma-separated, e.g. `06, 13, 83, 34`.
- Don't include 4941A or 4941B in any bucket unless the user explicitly asks (Piana wants to deprioritize Transport routier fret).
- `{wins_count}` = number of won deals in the 30-day (or 90-day) window for that NAF libellé, from Step 5 data.

## Filling rules

- `{sales_rep_role}` = "BDR" if all reps are BDRs, "Sales rep" if mixed (BDRs + AEs)
- `{N}` = number of buckets kept
- `{list_size}` = actual list size from HubSpot GET after creation (Step 10d) — this is the real number, not an estimate
- `{wins_count}` = number of distinct won deals associated with companies matching that NAF libellé
