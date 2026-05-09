#!/usr/bin/env python3
"""
Attempt to detect the Mendix runtime version from HTTP response headers and client bundles.
TSU-06

Usage: python check_mendix_version.py <url>
Output: JSON to stdout
"""
import json
import re
import sys
import requests


def check_mendix_version(url: str) -> dict:
    base = url.rstrip("/")
    result = {"version": None, "detected_from": None, "raw_hints": [], "error": None}

    # Check response headers on the root and /xas/
    for path in ["/", "/xas/"]:
        try:
            resp = requests.get(base + path, timeout=5, allow_redirects=True)
            for header in ["X-Powered-By", "Server", "X-Mendix-Version"]:
                val = resp.headers.get(header, "")
                if val:
                    result["raw_hints"].append(f"{header}: {val}")
                    m = re.search(r"(\d+\.\d+[\.\d]*)", val)
                    if m and result["version"] is None:
                        result["version"] = m.group(1)
                        result["detected_from"] = header
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            pass

    # Try to find version in /js/ bundle filenames (Mendix embeds version in paths)
    try:
        resp = requests.get(base + "/", timeout=5, allow_redirects=True)
        html = resp.text
        # Mendix bundles: mxclientsystem/mxui/mxui.js or versioned paths
        patterns = [
            r'src="[^"]*?(\d+\.\d+\.\d+[^"]*?)\.js"',
            r'/(\d+\.\d+\.\d+)/mxui\.js',
            r'mendix[/ ](\d+\.\d+[\.\d]*)',
            r'"mendixVersion"\s*:\s*"(\d+[\.\d]+)"',
        ]
        for pat in patterns:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                hint = m.group(0)
                result["raw_hints"].append(f"html_pattern: {hint}")
                if result["version"] is None:
                    ver_m = re.search(r"(\d+\.\d+[\.\d]*)", m.group(1))
                    if ver_m:
                        result["version"] = ver_m.group(1)
                        result["detected_from"] = "html_bundle_path"
                break
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        result["error"] = str(e)

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: check_mendix_version.py <url>"}))
        sys.exit(1)
    print(json.dumps(check_mendix_version(sys.argv[1]), indent=2))
