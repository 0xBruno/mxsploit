#!/usr/bin/env python3
"""
Enumerate exposed Mendix integration documentation endpoints.
TSU-04, TSU-10

Usage: python check_webservices.py <url>
Output: JSON to stdout
"""
import json
import sys
import requests


ENDPOINTS = [
    ("/api-doc/", "api_doc"),
    ("/rest-doc/", "rest_doc"),
    ("/ws-doc/", "ws_doc"),
    ("/ws/", "ws"),
    ("/odata/", "odata"),
]


def check_webservices(url: str) -> dict:
    base = url.rstrip("/")
    result = {"endpoints": {}, "any_exposed": False, "error": None}

    for path, key in ENDPOINTS:
        try:
            resp = requests.get(base + path, timeout=5, allow_redirects=True)
            accessible = resp.ok
            result["endpoints"][key] = {
                "url": base + path,
                "accessible": accessible,
                "status_code": resp.status_code,
            }
            if accessible:
                result["any_exposed"] = True
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            result["endpoints"][key] = {"url": base + path, "accessible": False, "error": str(e)}

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: check_webservices.py <url>"}))
        sys.exit(1)
    print(json.dumps(check_webservices(sys.argv[1]), indent=2))
