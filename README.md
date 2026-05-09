# MxSploit — Mendix Penetration Testing Skill

A Claude Code skill for autonomous security assessment of Mendix applications against [The S-Unit Top 10](https://the-s-unit.nl/en/the-s-unit-top-10/) (TSU) vulnerability categories.

## How it works

Claude orchestrates 13 standalone Python scripts that probe a target Mendix application, then applies LLM reasoning to classify findings by sensitivity and impact. The skill produces a structured pentest report with TSU references and severity ratings.

**Key idea:** Deterministic checks (default creds, missing headers) run first. Then Claude reasons about gray-area findings — like whether an exposed entity named `Administration.Account` is more concerning than `Catalog.ProductCategory` — and selectively exploits only what looks sensitive.

## Setup

### Prerequisites

- Python 3.10+
- Claude Code with skill support

### Install

```bash
# Clone the repo
git clone <repo-url> ~/dev/skills/mxsploit

# Install dependencies
pip install -r ~/dev/skills/mxsploit/requirements.txt

# Symlink into Claude Code's personal skills directory
ln -sfn ~/dev/skills/mxsploit ~/.claude/skills/mxsploit
```

The skill auto-resolves its script paths, so it works from any project directory.

## Usage

```
/mendix-pentest https://your-target.mendixcloud.com
```

Claude will run through five phases automatically:

1. **Enumerate** — collect session data, published services, security headers, runtime version
2. **Deterministic checks** — default credentials, demo users, dev mode
3. **LLM reasoning** — classify exposed entities, constants, and microflows by sensitivity
4. **Targeted exploitation** — probe only the findings flagged as sensitive
5. **Report** — structured markdown with severity ratings and TSU references

## Scripts

Each script is standalone, accepts a URL as its first argument, and outputs JSON to stdout.

### Enumeration

| Script | Purpose | TSU |
|---|---|---|
| `get_sessiondata.py <url>` | Retrieve session data (constants, microflows, entities, demo users, dev mode) | 07, 09, 10 |
| `check_webservices.py <url>` | Enumerate `/api-doc/`, `/rest-doc/`, `/ws-doc/`, `/odata/` | 04, 10 |
| `check_headers.py <url>` | Inspect security headers (CSP, HSTS, X-Frame-Options, etc.) | 10 |
| `check_mendix_version.py <url>` | Detect runtime version from response headers and HTML | 06 |

### Deterministic Checks

| Script | Purpose | TSU |
|---|---|---|
| `check_defaultcreds.py <url>` | Test MxAdmin:1 login | 07 |
| `check_demousers.py <url>` | Detect demo users and attempt login | 07 |
| `check_devmode.py <url>` | Check if developer mode is enabled | 10 |

### Exploitation

| Script | Purpose | TSU |
|---|---|---|
| `fetch_entity_data.py <url> <xpath>` | Unauthenticated XPath read (e.g. `//Administration.Account`) | 02 |
| `write_entity_data.py <url> <entity>` | Unauthenticated object creation attempt | 02 |
| `check_microflow_access.py <url> <name>` | Invoke a microflow without authentication | 03 |
| `check_published_api_auth.py <url> <path>` | Test if a REST/OData/SOAP endpoint requires auth | 04 |
| `check_xpath_injection.py <url> <entity>` | Safe read-only XPath injection probes | 08 |
| `check_page_access.py <url> <page>` | Test if a `/p/<page>` is accessible without auth | 01, 03 |

### Running scripts individually

```bash
python scripts/get_sessiondata.py https://target.mendixcloud.com
python scripts/fetch_entity_data.py https://target.mendixcloud.com //Administration.Account
```

## TSU Coverage

| TSU | Category | Coverage |
|---|---|---|
| TSU-01 | Insecure User Roles | Partial — page access enumeration |
| TSU-02 | Insecure Entity Access | Full — read and write testing |
| TSU-03 | Insecure Microflows | Good — enumerate and invoke |
| TSU-04 | Insecure Published Integrations | Good — enumerate and test auth |
| TSU-05 | Insecure Consumption | Manual review required |
| TSU-06 | Outdated Components | Partial — version detection |
| TSU-07 | Insecure Custom Auth | Good — default creds, demo users |
| TSU-08 | Insecure Custom Java | Partial — XPath injection |
| TSU-09 | Insecure UI Components | Good — constants analysis via LLM |
| TSU-10 | Insecure Cloud Deployments | Full — headers, docs, dev mode |

## Safety

- No brute-force or credential stuffing — zero risk of DoS or account lockout
- All scripts use a 5-second timeout with no retries
- XPath injection probes are read-only
- Write tests create at most one object and do not persist or commit it

## References

- [The S-Unit Top 10](https://the-s-unit.nl/en/the-s-unit-top-10/)
- [Mendix Penetration Testing Guide](https://0xbruno.dev/posts/research/mendix/testingguide/)
