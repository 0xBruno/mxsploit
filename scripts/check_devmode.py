#!/usr/bin/env python3
"""
Check whether Mendix developer mode is enabled in the application.
TSU-10

Usage: python check_devmode.py <url>
Output: JSON to stdout
"""
import json
import sys
import requests


def check_devmode(url: str) -> dict:
    xas = url.rstrip("/") + "/xas/"
    try:
        resp = requests.post(xas, json={"action": "get_session_data", "params": {}}, timeout=5)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        return {"devmode_enabled": None, "error": str(e)}

    if not resp.ok:
        return {"devmode_enabled": None, "error": f"HTTP {resp.status_code}"}

    try:
        data = resp.json()
    except ValueError as e:
        return {"devmode_enabled": None, "error": f"invalid JSON: {e}"}

    return {"devmode_enabled": data.get("isDevModeEnabled", False), "error": None}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: check_devmode.py <url>"}))
        sys.exit(1)
    print(json.dumps(check_devmode(sys.argv[1]), indent=2))
