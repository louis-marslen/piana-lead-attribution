"""Construit un filterBranch HubSpot Lists v3 en DNF (OR de AND).

HubSpot impose que le filterBranch racine soit un OR contenant
uniquement des branches AND (Disjunctive Normal Form).

Pattern: master ET (bucket_1 OU bucket_2 OU ... bucket_N)
       = (master ET bucket_1) OU (master ET bucket_2) OU ... (master ET bucket_N)

On distribue donc le AND sur le OR.

Format buckets (entrée) :
    [
      {"naf_libelle": "Transports routiers de fret interurbains",
       "departements": ["31", "32", "81"]},
      {"naf_libelle": "Manutention non portuaire",
       "departements": None},   # bucket national
    ]
"""

import copy
from typing import Any

NAF_PROPERTY = "libelle_code_naf"
DEPT_PROPERTY = "departement_code"
VEHICLES_PROPERTY = "data___calc__nb_vehicles"
VEHICLES_MIN = 10
VEHICLES_MAX = 250


def _bucket_filters(
    naf_libelle: str, departements: list[str] | None
) -> list[dict[str, Any]]:
    """Renvoie la liste de filtres atomiques d'un bucket (NAF [+ dept])."""
    filters: list[dict[str, Any]] = [
        {
            "filterType": "PROPERTY",
            "property": NAF_PROPERTY,
            "operation": {
                "operator": "IS_EQUAL_TO",
                "operationType": "MULTISTRING",
                "values": [naf_libelle],
                "includeObjectsWithNoValueSet": False,
            },
        }
    ]
    if departements:
        # HubSpot stocke les codes département sans zéro en tête (ex: "6" et non "06")
        normalized = [d.lstrip("0") or d for d in departements]
        filters.append(
            {
                "filterType": "PROPERTY",
                "property": DEPT_PROPERTY,
                "operation": {
                    "operator": "IS_ANY_OF",
                    "operationType": "ENUMERATION",
                    "values": normalized,
                    "includeObjectsWithNoValueSet": False,
                },
            }
        )
    return filters


def _vehicles_filters() -> list[dict[str, Any]]:
    """Filtre nb véhicules entre VEHICLES_MIN et VEHICLES_MAX (inclus)."""
    return [
        {
            "filterType": "PROPERTY",
            "property": VEHICLES_PROPERTY,
            "operation": {
                "operator": "IS_GREATER_THAN_OR_EQUAL_TO",
                "operationType": "NUMBER",
                "value": VEHICLES_MIN,
                "includeObjectsWithNoValueSet": False,
            },
        },
        {
            "filterType": "PROPERTY",
            "property": VEHICLES_PROPERTY,
            "operation": {
                "operator": "IS_LESS_THAN_OR_EQUAL_TO",
                "operationType": "NUMBER",
                "value": VEHICLES_MAX,
                "includeObjectsWithNoValueSet": False,
            },
        },
    ]


def _empty_and_branch() -> dict[str, Any]:
    return {
        "filterBranchType": "AND",
        "filterBranchOperator": "AND",
        "filterBranches": [],
        "filters": [],
    }


def _master_and_branches(master_branch: dict[str, Any]) -> list[dict[str, Any]]:
    """Extrait les branches AND du master.

    - master = OR de AND (DNF) : on renvoie ses filterBranches.
    - master = AND seul       : on l'enveloppe dans une liste.
    - master vide ou autre    : on renvoie une AND vide (pas de contrainte).
    """
    op = master_branch.get("filterBranchOperator") or master_branch.get(
        "filterBranchType"
    )

    if op == "OR":
        and_branches = master_branch.get("filterBranches", [])
        return and_branches if and_branches else [_empty_and_branch()]

    if op == "AND":
        return [master_branch]

    return [_empty_and_branch()]


def build_dnf_with_buckets(
    master_branch: dict[str, Any], buckets: list[dict[str, Any]]
) -> dict[str, Any]:
    """Distribue master AND (OR buckets) en DNF acceptée par HubSpot.

    Pour chaque combinaison (master_AND_branch, bucket) on crée une nouvelle
    branche AND qui fusionne les filtres des deux.
    """
    if not buckets:
        raise ValueError("Aucun bucket fourni")

    master_ands = _master_and_branches(master_branch)
    distributed: list[dict[str, Any]] = []

    for master_and in master_ands:
        master_filters = list(master_and.get("filters", []))
        master_subbranches = list(master_and.get("filterBranches", []))

        for bucket in buckets:
            merged_filters = (
                copy.deepcopy(master_filters)
                + _bucket_filters(bucket["naf_libelle"], bucket.get("departements"))
                + _vehicles_filters()
            )
            distributed.append(
                {
                    "filterBranchType": "AND",
                    "filterBranchOperator": "AND",
                    "filterBranches": copy.deepcopy(master_subbranches),
                    "filters": merged_filters,
                }
            )

    return {
        "filterBranchType": "OR",
        "filterBranchOperator": "OR",
        "filterBranches": distributed,
        "filters": [],
    }
