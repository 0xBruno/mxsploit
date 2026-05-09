#!/usr/bin/env python3
"""
Test whether the default MxAdmin:1 credentials are active.
TSU-07

Usage: python check_defaultcreds.py <url>
Output: JSON to stdout
"""
import json
import sys
import requests


def check_defaultcreds(url: str) -> dict:
    xas = url.rstrip("/") + "/xas/"
    payload = {
        "action": "login",
        "params": {"username": "MxAdmin", "password": "1"},
        "profiledata": {},
    }
    try:
        resp = requests.post(xas, json=payload, timeout=5)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        return {"vulnerable": None, "detail": None, "error": str(e)}

    vulnerable = resp.ok
    return {
        "vulnerable": vulnerable,
        "detail": "MxAdmin:1 authenticated successfully" if vulnerable else f"login rejected (HTTP {resp.status_code})",
        "error": None,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: check_defaultcreds.py <url>"}))
        sys.exit(1)
    print(json.dumps(check_defaultcreds(sys.argv[1]), indent=2))
