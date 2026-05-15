"""Client minimal pour l'API HubSpot Lists v3."""

import os
from typing import Any

import requests


class HubSpotListsClient:
    def __init__(self, token: str, region: str = "na1", portal_id: str | None = None):
        self.token = token
        # L'API HubSpot est globale (api.hubapi.com), la "region" du token
        # est gérée côté serveur. On garde le param pour construire les URLs UI.
        self.region = region
        self.portal_id = portal_id
        self.base = "https://api.hubapi.com"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    def get_list(self, list_id: int | str) -> dict[str, Any]:
        """GET /crm/v3/lists/{listId} — inclut le filterBranch."""
        url = f"{self.base}/crm/v3/lists/{list_id}"
        # includeFilters=true pour récupérer le filterBranch
        r = self.session.get(url, params={"includeFilters": "true"})
        r.raise_for_status()
        return r.json()

    def create_list(
        self,
        name: str,
        object_type_id: str,
        filter_branch: dict[str, Any],
        processing_type: str = "DYNAMIC",
    ) -> dict[str, Any]:
        """POST /crm/v3/lists — crée une liste dynamique."""
        url = f"{self.base}/crm/v3/lists"
        payload = {
            "name": name,
            "objectTypeId": object_type_id,
            "processingType": processing_type,
            "filterBranch": filter_branch,
        }
        r = self.session.post(url, json=payload)
        if not r.ok:
            # Remonter le corps d'erreur HubSpot, souvent verbeux et utile
            raise RuntimeError(
                f"HubSpot {r.status_code} — {r.text}"
            )
        return r.json()

    def move_list_to_folder(self, list_id: int | str, folder_id: int | str) -> dict[str, Any]:
        """Déplace une liste dans un dossier HubSpot."""
        url = f"{self.base}/crm/v3/lists/folders/move-list"
        payload = {"listId": str(list_id), "newFolderId": str(folder_id)}
        r = self.session.put(url, json=payload)
        if not r.ok:
            raise RuntimeError(f"HubSpot {r.status_code} — {r.text}")
        return r.json() if r.text else {}

    def list_ui_url(self, list_id: int | str) -> str:
        """Construit l'URL UI HubSpot d'une liste."""
        host = f"https://app{'-eu1' if self.region == 'eu1' else ''}.hubspot.com"
        portal = self.portal_id or "_"
        return f"{host}/contacts/{portal}/objectLists/{list_id}"


def extract_filter_branch(list_payload: dict[str, Any]) -> dict[str, Any]:
    """Extrait le filterBranch du payload GET list.

    La structure exacte dépend de la version d'API ; on cherche `filterBranch`
    en racine puis sous `list.filterBranch`.
    """
    if "filterBranch" in list_payload:
        return list_payload["filterBranch"]
    if "list" in list_payload and "filterBranch" in list_payload["list"]:
        return list_payload["list"]["filterBranch"]
    raise KeyError(
        f"Pas de filterBranch dans la réponse. Clés disponibles : {list(list_payload.keys())}"
    )


def extract_object_type_id(list_payload: dict[str, Any]) -> str:
    """Extrait l'objectTypeId du payload (companies = 0-2)."""
    if "objectTypeId" in list_payload:
        return list_payload["objectTypeId"]
    if "list" in list_payload and "objectTypeId" in list_payload["list"]:
        return list_payload["list"]["objectTypeId"]
    raise KeyError("Pas d'objectTypeId dans la réponse master")
