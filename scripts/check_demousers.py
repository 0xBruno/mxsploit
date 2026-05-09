#!/usr/bin/env python3
"""
Detect demo users from session data and attempt login with their credentials.
TSU-07

Usage: python check_demousers.py <url>
Output: JSON to stdout
"""
import json
import sys
import requests


def check_demousers(url: str) -> dict:
    base = url.rstrip("/")
    xas = base + "/xas/"
    result = {"demo_users": [], "loginable": [], "error": None}

    # Fetch session data to find demoUsers
    try:
        resp = requests.post(xas, json={"action": "get_session_data", "params": {}}, timeout=5)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        result["error"] = str(e)
        return result

    if not resp.ok:
        return result

    try:
        data = resp.json()
    except ValueError as e:
        result["error"] = f"invalid JSON: {e}"
        return result

    demo_users = data.get("demoUsers", [])
    result["demo_users"] = demo_users

    for user in demo_users:
        username = user.get("username") or user.get("login") or user.get("user")
        password = user.get("password") or user.get("pass") or user.get("pw")
        if not username or not password:
            continue

        login_payload = {
            "action": "login",
            "params": {"username": username, "password": password},
            "profiledata": {},
        }
        try:
            login_resp = requests.post(xas, json=login_payload, timeout=5)
            if login_resp.ok:
                result["loginable"].append({"username": username, "password": password})
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            pass

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: check_demousers.py <url>"}))
        sys.exit(1)
    print(json.dumps(check_demousers(sys.argv[1]), indent=2))
