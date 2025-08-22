#!/usr/bin/env python3
import json, argparse, sys, pathlib

p = argparse.ArgumentParser(description="Build Ansible inventory from Terraform outputs.json (supports AWS public_ip or vSphere vm_ip)")
p.add_argument("--in", dest="inputs", required=True)
p.add_argument("--out", dest="out", required=True)
a = p.parse_args()

try:
    data = json.load(open(a.inputs))
except Exception as e:
    print(f"ERROR: Failed to read {a.inputs}: {e}", file=sys.stderr); sys.exit(1)

ip = None
if "public_ip" in data and "value" in data["public_ip"]:
    ip = data["public_ip"]["value"]
elif "vm_ip" in data and "value" in data["vm_ip"]:
    ip = data["vm_ip"]["value"]

if not ip:
    print("ERROR: No 'public_ip' or 'vm_ip' found in outputs.json", file=sys.stderr); sys.exit(2)

content = "[web]\n" + str(ip) + "\n"
pathlib.Path(a.out).write_text(content)
print(f"Wrote inventory to {a.out}:\n{content}")
