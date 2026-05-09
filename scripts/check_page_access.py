#!/usr/bin/env python3
"""
Test whether a named Mendix page is accessible without authentication via /p/.
TSU-01, TSU-03

Usage: python check_page_access.py <url> <page_name>
  page_name example: Administration or UserManagement_Overview
Output: JSON to stdout
"""
import json
import sys
import requests


def check_page_access(url: str, page_name: str) -> dict:
    page_url = url.rstrip("/") + "/p/" + page_name
    try:
        resp = requests.get(page_url, timeout=5, allow_redirects=False)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        return {"page": page_name, "url": page_url, "accessible": None, "status_code": None, "error": str(e)}

    # 200 = accessible; 3xx = redirect (likely to login); 401/403/404 = blocked
    redirects_to_login = resp.status_code in (301, 302, 303, 307, 308)
    accessible = resp.ok

    return {
        "page": page_name,
        "url": page_url,
        "accessible": accessible,
        "status_code": resp.status_code,
        "redirects_to_login": redirects_to_login,
        "location": resp.headers.get("Location"),
        "error": None,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage: check_page_access.py <url> <page_name>"}))
        sys.exit(1)
    print(json.dumps(check_page_access(sys.argv[1], sys.argv[2]), indent=2))
