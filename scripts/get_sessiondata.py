#!/usr/bin/env python3
"""
Retrieve Mendix session data from /xas/ and extract surface area.
TSU-07, TSU-09, TSU-10

Usage: python get_sessiondata.py <url>
Output: JSON to stdout
"""
import json
import sys
import requests


def get_sessiondata(url: str) -> dict:
    xas = url.rstrip("/") + "/xas/"
    payload = {"action": "get_session_data", "params": {}}
    try:
        resp = requests.post(xas, json=payload, timeout=5)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        return {"xas_status": None, "error": str(e)}

    result = {
        "xas_status": resp.status_code,
        "constants": None,
        "microflows": None,
        "accessible_entities": None,
        "demo_users": None,
        "is_devmode_enabled": None,
        "error": None,
    }

    if resp.status_code != 200:
        return result

    try:
        data = resp.json()
    except ValueError as e:
        result["error"] = f"invalid JSON: {e}"
        return result

    result["constants"] = data.get("constants")
    result["demo_users"] = data.get("demoUsers")
    result["is_devmode_enabled"] = data.get("isDevModeEnabled")

    raw_mf = data.get("microflows")
    result["microflows"] = raw_mf

    metadata = data.get("metadata")
    if metadata:
        result["accessible_entities"] = [e.get("objectType") for e in metadata if e.get("objectType")]

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: get_sessiondata.py <url>"}))
        sys.exit(1)
    print(json.dumps(get_sessiondata(sys.argv[1]), indent=2))
