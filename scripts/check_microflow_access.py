#!/usr/bin/env python3
"""
Attempt to invoke a named microflow via unauthenticated runtimeOperation on /xas/.
TSU-03

Usage: python check_microflow_access.py <url> <microflow_name>
  microflow_name example: MyModule.MyMicroflow
Output: JSON to stdout
"""
import json
import sys
import requests


def check_microflow_access(url: str, microflow_name: str) -> dict:
    xas = url.rstrip("/") + "/xas/"
    payload = {
        "action": "runtimeOperation",
        "params": {
            "actionName": microflow_name,
            "applyto": "none",
            "guids": [],
            "val": [],
        },
    }
    try:
        resp = requests.post(xas, json=payload, timeout=5)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        return {"microflow": microflow_name, "invocable": None, "status_code": None, "error": str(e)}

    invocable = resp.ok
    result = {
        "microflow": microflow_name,
        "invocable": invocable,
        "status_code": resp.status_code,
        "error": None,
    }

    if invocable:
        try:
            result["response_sample"] = resp.json()
        except ValueError:
            result["response_sample"] = resp.text[:200]

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage: check_microflow_access.py <url> <microflow_name>"}))
        sys.exit(1)
    print(json.dumps(check_microflow_access(sys.argv[1], sys.argv[2]), indent=2))
