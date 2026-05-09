# Mendix Penetration Testing Skill

## Trigger

Use this skill when the user runs `/mendix-pentest <url>` or asks to perform a security assessment of a Mendix application.

## Overview

This skill performs an autonomous security assessment of a Mendix application against The S-Unit Top 10 (TSU) vulnerability categories. It works in five phases: enumerate, deterministic checks, LLM reasoning, targeted exploitation, and report.

All scripts live in the `scripts/` subdirectory next to this SKILL.md file. Before running any scripts, resolve the absolute path to this skill's directory:

```
SKILL_DIR="$(dirname "$(readlink -f "$(find ~/.claude/skills -name SKILL.md -path '*/mxsploit/*' 2>/dev/null | head -1)")")"
```

Then run scripts with `python "$SKILL_DIR/scripts/<name>.py" <args>` and parse their JSON stdout.

---

## Phase 1 — Enumerate attack surface

Run all four enumeration scripts **in parallel** (four Bash calls in one message):

```
python "$SKILL_DIR/scripts/get_sessiondata.py" <url>
python "$SKILL_DIR/scripts/check_webservices.py" <url>
python "$SKILL_DIR/scripts/check_headers.py" <url>
python "$SKILL_DIR/scripts/check_mendix_version.py" <url>
```

Record:
- `get_sessiondata` → `constants`, `microflows`, `accessible_entities`, `demo_users`, `is_devmode_enabled`, `xas_status`
- `check_webservices` → which of `/api-doc/`, `/rest-doc/`, `/ws-doc/`, `/odata/` are accessible
- `check_headers` → which security headers are missing, any CSP issues
- `check_mendix_version` → detected version and any version hints

---

## Phase 2 — Deterministic checks

Run in parallel:

```
python "$SKILL_DIR/scripts/check_defaultcreds.py" <url>
python "$SKILL_DIR/scripts/check_demousers.py" <url>
python "$SKILL_DIR/scripts/check_devmode.py" <url>
```

Flag immediately on findings:
- `check_defaultcreds.vulnerable == true` → **CRITICAL** (TSU-07)
- `check_demousers.loginable` non-empty → **HIGH** (TSU-07)
- `check_demousers.demo_users` non-empty but not loginable → **INFO** (TSU-07)
- `check_devmode.devmode_enabled == true` → **HIGH** (TSU-10)

---

## Phase 3 — LLM reasoning on session data

Apply your own judgment to the data collected in Phase 1. Do not skip this step even if the lists are short.

### Entity classification

For each name in `accessible_entities`, classify and assign a sensitivity tier:

| Tier | Patterns | Action |
|------|----------|--------|
| **CRITICAL** | `Account`, `Password`, `Credential`, `Token`, `Session`, `ApiKey`, `Secret` | Queue for `fetch_entity_data.py` and `write_entity_data.py` |
| **HIGH** | `User`, `Customer`, `Patient`, `Employee`, `Person`, `Email`, `Address`, `Phone`, `Payment`, `Invoice`, `Order`, `Transaction`, `Salary`, `SSN`, `DOB` | Queue for `fetch_entity_data.py` |
| **HIGH** | `Admin`, `Config`, `Setting`, `Audit`, `Log`, `Role`, `Permission`, `Key` | Queue for `fetch_entity_data.py` |
| **MEDIUM** | Business-domain entities that sound application-specific and sensitive given context | Consider `fetch_entity_data.py` |
| **LOW/INFO** | Reference/catalog data (`Product`, `Category`, `Country`, `Language`, `Status`) | Note but do not exploit |

Use the full module path context: `Administration.Account` is more concerning than `Catalog.ProductCategory`. Consider what the application appears to do.

**Even if enumerated entities seem benign**: note the finding that `accessible_entities` is populated at all — it means the session data exposes the entity model without authentication (TSU-02, MEDIUM at minimum).

### Constants classification

For each constant in `constants`, flag as **HIGH** (TSU-09) if the name OR value matches any of:
`password`, `passwd`, `secret`, `key`, `token`, `api_key`, `apikey`, `auth`, `smtp`, `credential`, `private`, `bearer`

Note: Mendix constants with `Expose to Client = Yes` are intentionally sent to the browser, but secrets should never be in that list.

### Microflow classification

- If `microflows` is populated (non-empty, non-obfuscated names): flag as **MEDIUM** (TSU-03) — information disclosure of application logic.
- Flag each microflow name matching: `Admin`, `Delete`, `Remove`, `Export`, `Override`, `ChangePassword`, `CreateUser`, `GrantRole`, `Sudo`, `Bypass`, `SetRole`, `Escalat`, `ImportAll`, `Purge` as **HIGH** (TSU-03) — queue for `check_microflow_access.py`.

### Published services reasoning

For each accessible endpoint from `check_webservices`:
- `/api-doc/` accessible → **MEDIUM** (TSU-04, TSU-10): service definitions exposed
- Parse the `/api-doc/` or `/rest-doc/` page content if accessible, extract individual API endpoint paths, queue each for `check_published_api_auth.py`

---

## Phase 4 — Targeted exploitation

Run based on what Phase 3 flagged. Use parallel Bash calls where multiple probes are independent.

**Entity read access** (for each CRITICAL/HIGH entity queued):
```
python "$SKILL_DIR/scripts/fetch_entity_data.py" <url> //<entity_xpath>
```
XPath format: `//Module.EntityName` (e.g. `//Administration.Account`)

If `fetch_entity_data` returns `accessible: true` with `count > 0` or non-empty `sample`:
- Confirm the finding: this entity's data is readable without authentication
- Note any sensitive field names visible in `sample`
- Severity: CRITICAL if auth/credential entity, HIGH if PII/financial

**Entity write access** (for each CRITICAL entity queued):
```
python "$SKILL_DIR/scripts/write_entity_data.py" <url> <Module.Entity>
```
If `created: true`: CRITICAL write-without-authentication finding (TSU-02)

**Microflow invocation** (for each dangerous microflow queued):
```
python "$SKILL_DIR/scripts/check_microflow_access.py" <url> <Module.MicroflowName>
```
If `invocable: true`: HIGH finding (TSU-03)

**Published API auth** (for each discovered endpoint):
```
python "$SKILL_DIR/scripts/check_published_api_auth.py" <url> <endpoint_path>
```
If `unauthenticated_access: true`: HIGH finding (TSU-04)

**XPath injection** (when entities are accessible):
```
python "$SKILL_DIR/scripts/check_xpath_injection.py" <url> <Module.Entity>
```
If `vulnerable: true`: HIGH finding (TSU-08)

**Page access** (derive page names from microflow/entity names — strip module prefix and append `_Overview`, `_NewEdit`, `_Detail`):
```
python "$SKILL_DIR/scripts/check_page_access.py" <url> <PageName>
```
If `accessible: true` (HTTP 200): MEDIUM finding (TSU-01/TSU-03)

---

## Phase 5 — Report

Produce a markdown pentest report using this structure:

```markdown
# Mendix Security Assessment: <appname>
**Target:** <url>
**Date:** <today>

## Executive Summary
<2-3 sentences. State the number of critical/high findings and the most severe confirmed vulnerability. If no critical findings, state that.>

## Findings

### [CRITICAL] <Title> — TSU-XX
**Description:** ...
**Evidence:**
\`\`\`json
<truncated JSON from the script that confirmed it>
\`\`\`
**Recommendation:** ...

---
```

Severity order in the report: CRITICAL → HIGH → MEDIUM → LOW → INFO

### Standard recommendations by category

- **Default creds (TSU-07)**: Change MxAdmin password immediately; rotate all admin credentials.
- **Demo users (TSU-07)**: Disable demo users in production environment settings.
- **Dev mode (TSU-10)**: Disable developer mode; it should never be enabled in production.
- **Entity access (TSU-02)**: Apply XPath constraints to all entity access rules; audit module roles.
- **Microflow access (TSU-03)**: Restrict microflow allowed roles; enable "Apply entity access" where missing.
- **Published API no auth (TSU-04)**: Configure authentication (OAuth, basic auth, or custom) on all published integrations.
- **Exposed constants (TSU-09)**: Move secrets out of Mendix constants into environment variables; never expose to client.
- **Missing CSP (TSU-10)**: Configure a strict Content-Security-Policy in deployment environment settings.
- **Exposed service docs (TSU-04/10)**: Disable documentation endpoints (`/api-doc/`, `/rest-doc/`) in production.
- **XPath injection (TSU-08)**: Sanitize all user-controlled input before use in XPath expressions; prefer parameterized queries.

---

## TSU-05 Note

TSU-05 (Insecure Consumption of Integrations) cannot be assessed dynamically from the outside — it requires source code or traffic inspection. Flag it as **requires manual review** in the report.

---

## Safety constraints

- Never run more than one login attempt per username (no credential stuffing or brute force).
- Do not attempt to delete, commit, or persist objects created during write testing — note the creation in the finding and stop.
- All scripts use a 5-second timeout; do not retry on connection errors.
- Do not follow redirect chains that lead off the target domain.
