# Piana — Lead Attribution → HubSpot List

Ce projet pousse les buckets NAF × département produits par le skill
`bdr-lead-attribution-brief` directement dans HubSpot, sous forme d'une
**nouvelle liste dynamique fille** de la master de prospection.

## Workflow standard

1. L'utilisateur déclenche le skill `bdr-lead-attribution-brief` dans une conv Claude.
2. Le skill produit le brief habituel (Section 1 + Section 2).
3. À la fin, l'utilisateur dit "push dans HubSpot" / "crée la liste".
4. Claude (ou l'utilisateur) écrit le JSON des buckets sélectionnés dans
   `input/buckets.json` puis lance :

   ```bash
   python scripts/push_list.py \
     --buckets input/buckets.json \
     --name "Master — Attribution $(date +%Y-%m-%d)"
   ```

5. Le script :
   - GET `/crm/v3/lists/{MASTER_LIST_ID}` → récupère le filterBranch master
   - Construit un OR des buckets (NAF × départements)
   - Wrappe en AND : `master_filterBranch AND (OR des buckets)`
   - POST `/crm/v3/lists` → crée la liste fille
   - Retourne l'URL HubSpot de la liste

## Format de `input/buckets.json`

```json
{
  "buckets": [
    {
      "naf_libelle": "Transports routiers de fret interurbains",
      "departements": ["31", "32", "81", "82"]
    },
    {
      "naf_libelle": "Manutention non portuaire",
      "departements": null
    }
  ]
}
```

- `departements: null` ou absent → bucket national (pas de filtre géo).
- `naf_libelle` doit être le libellé EXACT INSEE (le skill le sort déjà comme ça).

## Variables d'environnement requises

Voir `.env.example`. Token Private App HubSpot avec scopes :
- `crm.lists.read`
- `crm.lists.write`

## Tests

```bash
python scripts/push_list.py --buckets input/buckets.example.json \
  --name "TEST — à supprimer" --dry-run
```

Le mode `--dry-run` n'envoie PAS le POST, il affiche juste le payload.
