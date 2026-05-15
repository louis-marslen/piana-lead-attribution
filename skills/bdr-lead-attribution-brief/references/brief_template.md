# Brief template

Use this EXACT structure when rendering the final brief.

---

## 📊 1. Leads à attribuer par {sales_rep_role_plural}

| {sales_rep_role} | Stock actuel | Cible | À attribuer |
|---|---|---|---|
| {name} | {current_stock} | {target} | **{to_assign}** |
| ... | ... | ... | ... |
| **Total** | | | **{total_to_assign}** |

---

## 🎯 2. Liste HubSpot créée

J'ai sélectionné {N} groupes NAF × géo — **{list_size} leads** dans la liste.

👉 **[Ouvrir la liste dans HubSpot]({hubspot_list_url})**

| Groupe | Volume estimé |
|---|---|
| **{N} — {bucket_name}** | ~{volume} |
| ... | ... |
| **Taille réelle de la liste** | **{list_size}** |

---

## Style rules

- Use `**` (bold) only on the bucket name and on `Total`, never elsewhere in the table.
- Volume numbers prefixed with `~` for estimates.
- Geographic scope in the bucket name uses simple region terms (e.g. "PACA + Occitanie + IDF", "national", "Auvergne-Rhône-Alpes").
- The libellé NAF in the filters column is wrapped in backticks and reproduces the value EXACTLY as it appears in HubSpot (including double spaces if any, e.g. "Commerce de gros  de bois...").
- Department codes are 2-character strings, comma-separated, e.g. `06, 13, 83, 34`.
- Don't include 4941A or 4941B in any bucket unless the user explicitly asks (Piana wants to deprioritize Transport routier fret).

## Filling rules

- `{sales_rep_role}` = "BDR" if all reps are BDRs, "Sales rep" if mixed (BDRs + AEs)
- `{1.5x_total}` = round(total_to_assign * 1.5)
- `{N}` = number of buckets kept
- `{list_size}` = actual list size from HubSpot GET after creation (Step 10d) — this is the real number, not an estimate
