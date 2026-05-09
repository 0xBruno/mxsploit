#!/usr/bin/env python3
"""
Inspect HTTP security headers on the Mendix application root.
TSU-10

Usage: python check_headers.py <url>
Output: JSON to stdout
"""
import json
import sys
import requests


SECURITY_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Frame-Options",
    "X-Content-Type-Options",
    "Permissions-Policy",
    "Referrer-Policy",
    "Cross-Origin-Opener-Policy",
]


def check_headers(url: str) -> dict:
    base = url.rstrip("/") + "/"
    try:
        resp = requests.get(base, timeout=5, allow_redirects=True)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        return {"headers": {}, "missing": [], "error": str(e)}

    headers = {h: resp.headers.get(h) for h in SECURITY_HEADERS}
    missing = [h for h, v in headers.items() if v is None]

    csp = headers.get("Content-Security-Policy")
    csp_issues = []
    if csp:
        if "unsafe-inline" in csp:
            csp_issues.append("contains 'unsafe-inline'")
        if "unsafe-eval" in csp:
            csp_issues.append("contains 'unsafe-eval'")
        if "*" in csp:
            csp_issues.append("contains wildcard '*'")

    return {
        "status_code": resp.status_code,
        "headers": headers,
        "missing": missing,
        "csp_issues": csp_issues,
        "error": None,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: check_headers.py <url>"}))
        sys.exit(1)
    print(json.dumps(check_headers(sys.argv[1]), indent=2))
