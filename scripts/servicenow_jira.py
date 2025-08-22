#!/usr/bin/env python3
import os, json, argparse, sys, pathlib, base64
import requests

ap = argparse.ArgumentParser(description="Create ServiceNow CMDB/Incident and/or Jira Issue from cmdb.json")
ap.add_argument("--cmdb", required=True, help="Path to cmdb.json")
args = ap.parse_args()

cmdb = json.load(open(args.cmdb))

result = {"servicenow": None, "jira": None}

# ---- ServiceNow ----
snow_instance = os.getenv("SNOW_INSTANCE")
snow_user     = os.getenv("SNOW_USER")
snow_password = os.getenv("SNOW_PASSWORD")
snow_table    = os.getenv("SNOW_TABLE","incident")  # could be incident or cmdb_ci_server, etc.

if snow_instance and snow_user and snow_password:
    try:
        base = f"https://{snow_instance}/api/now/table/{snow_table}"
        # Minimal payload; adjust fields per your table
        if snow_table.lower() == "incident":
            payload = {
                "short_description": f"[{cmdb.get('project','netauto-mini')}] Provisioned {cmdb.get('platform')} resource",
                "description": json.dumps(cmdb, indent=2),
                "severity": "3",
                "urgency": "3",
                "impact": "3"
            }
        else:
            payload = {
                "name": cmdb.get("vm_name") or cmdb.get("instance_id") or "provisioned-resource",
                "ip_address": cmdb.get("vm_ip") or cmdb.get("public_ip"),
                "u_project": cmdb.get("project","netauto-mini"),
                "u_platform": cmdb.get("platform")
            }

        r = requests.post(base, auth=(snow_user, snow_password), headers={"Content-Type":"application/json"}, data=json.dumps(payload), timeout=30)
        r.raise_for_status()
        result["servicenow"] = r.json()
        print("ServiceNow record created.")
    except Exception as e:
        print(f"ServiceNow error: {e}", file=sys.stderr)
        result["servicenow"] = {"error": str(e)}
else:
    print("ServiceNow variables not fully set; skipping.")

# ---- Jira ----
jira_base   = os.getenv("JIRA_BASE_URL")
jira_user   = os.getenv("JIRA_USER")
jira_token  = os.getenv("JIRA_API_TOKEN")
jira_proj   = os.getenv("JIRA_PROJECT_KEY")
jira_type   = os.getenv("JIRA_ISSUE_TYPE","Task")

if jira_base and jira_user and jira_token and jira_proj:
    try:
        url = f"{jira_base}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": jira_proj},
                "issuetype": {"name": jira_type},
                "summary": f"[{cmdb.get('project','netauto-mini')}] Provisioned {cmdb.get('platform')} resource",
                "description": {
                    "type": "doc","version": 1,
                    "content": [{
                        "type": "paragraph",
                        "content": [{"text": json.dumps(cmdb, indent=2), "type": "text"}]
                    }]
                }
            }
        }
        headers = {"Content-Type":"application/json"}
        r = requests.post(url, headers=headers, auth=(jira_user, jira_token), data=json.dumps(payload), timeout=30)
        r.raise_for_status()
        result["jira"] = r.json()
        print("Jira issue created.")
    except Exception as e:
        print(f"Jira error: {e}", file=sys.stderr)
        result["jira"] = {"error": str(e)}
else:
    print("Jira variables not fully set; skipping.")

pathlib.Path("itsm_result.json").write_text(json.dumps(result, indent=2))
print("Wrote itsm_result.json")
