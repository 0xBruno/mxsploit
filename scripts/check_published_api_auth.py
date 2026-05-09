#!/usr/bin/env python3
"""
Test whether a published REST/OData/SOAP endpoint requires authentication.
TSU-04

Usage: python check_published_api_auth.py <url> <endpoint_path>
  endpoint_path example: /rest/myservice/v1/
Output: JSON to stdout
"""
import json
import sys
import requests


def check_published_api_auth(url: str, endpoint_path: str) -> dict:
    full_url = url.rstrip("/") + "/" + endpoint_path.lstrip("/")
    # Deliberately send no Authorization header
    try:
        resp = requests.get(full_url, timeout=5, allow_redirects=False)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        return {"endpoint": full_url, "auth_required": None, "status_code": None, "error": str(e)}

    # 401 or 403 = auth required; 200/2xx = unauthenticated access
    auth_required = resp.status_code in (401, 403)
    unauthenticated_access = resp.ok

    result = {
        "endpoint": full_url,
        "status_code": resp.status_code,
        "auth_required": auth_required,
        "unauthenticated_access": unauthenticated_access,
        "error": None,
    }

    if unauthenticated_access:
        try:
            result["response_sample"] = resp.json()
        except ValueError:
            result["response_sample"] = resp.text[:300]

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage: check_published_api_auth.py <url> <endpoint_path>"}))
        sys.exit(1)
    print(json.dumps(check_published_api_auth(sys.argv[1], sys.argv[2]), indent=2))
