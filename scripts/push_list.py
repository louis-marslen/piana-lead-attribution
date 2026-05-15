#!/usr/bin/env python3
"""Crée une liste dynamique HubSpot fille de la master, avec filtres NAF×dept.

Usage:
    python scripts/push_list.py \\
        --buckets input/buckets.json \\
        --name "Master — Attribution 2026-05-15"

    # Pour tester sans pousser :
    python scripts/push_list.py --buckets input/buckets.json \\
        --name "TEST" --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Permet d'exécuter le script depuis n'importe où
sys.path.insert(0, str(Path(__file__).parent))

from lib.filter_builder import build_dnf_with_buckets
from lib.hubspot_lists import (
    HubSpotListsClient,
    extract_filter_branch,
    extract_object_type_id,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--buckets",
        required=True,
        help="Chemin du JSON contenant les buckets NAF×dept",
    )
    parser.add_argument(
        "--name", required=True, help="Nom de la nouvelle liste HubSpot"
    )
    parser.add_argument(
        "--master-id",
        default=None,
        help="ID de la liste master (sinon: MASTER_LIST_ID dans .env)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="N'envoie pas le POST, affiche juste le payload",
    )
    parser.add_argument(
        "--folder-id",
        default=None,
        help="ID du dossier HubSpot où ranger la liste (sinon: HUBSPOT_FOLDER_ID dans .env)",
    )
    parser.add_argument(
        "--save-payload",
        default=None,
        help="Sauve le payload final dans ce fichier (utile pour debug)",
    )
    args = parser.parse_args()

    load_dotenv()
    token = os.environ.get("HUBSPOT_TOKEN")
    region = os.environ.get("HUBSPOT_REGION", "na1")
    master_id = args.master_id or os.environ.get("MASTER_LIST_ID")

    if not token:
        print("❌ HUBSPOT_TOKEN manquant dans .env", file=sys.stderr)
        return 1
    if not master_id:
        print("❌ MASTER_LIST_ID manquant (--master-id ou .env)", file=sys.stderr)
        return 1

    # Charger les buckets
    buckets_path = Path(args.buckets)
    if not buckets_path.exists():
        print(f"❌ Fichier buckets introuvable : {buckets_path}", file=sys.stderr)
        return 1

    data = json.loads(buckets_path.read_text(encoding="utf-8"))
    buckets = data["buckets"] if "buckets" in data else data
    print(f"📦 {len(buckets)} bucket(s) chargé(s) depuis {buckets_path}")

    portal_id = os.environ.get("HUBSPOT_PORTAL_ID")
    client = HubSpotListsClient(token=token, region=region, portal_id=portal_id)

    # 1. GET master
    print(f"⬇️  GET master list {master_id}...")
    master_payload = client.get_list(master_id)
    master_branch = extract_filter_branch(master_payload)
    object_type_id = extract_object_type_id(master_payload)
    print(f"   ✓ objectTypeId = {object_type_id}")

    # 2. Construire le filterBranch combiné en DNF (OR de AND)
    combined = build_dnf_with_buckets(master_branch, buckets)
    print(f"   ✓ DNF construite : {len(combined['filterBranches'])} branche(s) AND")

    payload_preview = {
        "name": args.name,
        "objectTypeId": object_type_id,
        "processingType": "DYNAMIC",
        "filterBranch": combined,
    }

    if args.save_payload:
        Path(args.save_payload).write_text(
            json.dumps(payload_preview, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"💾 Payload sauvé dans {args.save_payload}")

    if args.dry_run:
        print("\n🧪 DRY RUN — payload qui aurait été envoyé :\n")
        print(json.dumps(payload_preview, indent=2, ensure_ascii=False))
        return 0

    # 3. POST nouvelle liste
    print(f"⬆️  POST nouvelle liste « {args.name} »...")
    result = client.create_list(
        name=args.name,
        object_type_id=object_type_id,
        filter_branch=combined,
    )

    new_id = result.get("listId") or result.get("list", {}).get("listId")
    print(f"\n✅ Liste créée — listId = {new_id}")

    # 4. Déplacer dans un dossier si spécifié
    folder_id = args.folder_id or os.environ.get("HUBSPOT_FOLDER_ID")
    if new_id and folder_id:
        print(f"📁 Déplacement dans le dossier {folder_id}...")
        client.move_list_to_folder(new_id, folder_id)
        print("   ✓ OK")

    if new_id:
        print(f"🔗 {client.list_ui_url(new_id)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
