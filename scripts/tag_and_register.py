#!/usr/bin/env python3
import json, argparse, os, sys, pathlib

# Optional AWS tagging if AWS outputs exist
def try_tag_aws(instance_id, region):
    try:
        import boto3
        ec2 = boto3.client("ec2", region_name=region)
        tags = [{"Key": "ManagedBy", "Value": "GitLab"}, {"Key": "Project", "Value": os.getenv("PROJECT_NAME","netauto-mini")}]
        ec2.create_tags(Resources=[instance_id], Tags=tags)
        print(f"Tagged AWS instance {instance_id} in {region}: {tags}")
        return {"aws_tagged": True, "tags": {t['Key']: t['Value'] for t in tags}}
    except Exception as e:
        print(f"NOTE: AWS tagging skipped or failed: {e}", file=sys.stderr)
        return {"aws_tagged": False, "error": str(e)}

ap = argparse.ArgumentParser(description="Create cmdb.json from Terraform outputs and optionally tag AWS instance")
ap.add_argument("--in", dest="inputs", required=True)
ap.add_argument("--project", default=os.getenv("PROJECT_NAME","netauto-mini"))
ap.add_argument("--region", default=os.getenv("AWS_DEFAULT_REGION","us-east-1"))
args = ap.parse_args()

data = json.load(open(args.inputs))
cmdb = {"project": args.project}

# Prefer vSphere outputs
vm_ip = data.get("vm_ip",{}).get("value")
vm_name = data.get("vm_name",{}).get("value")
if vm_ip or vm_name:
    cmdb.update({"platform":"vsphere","vm_ip": vm_ip, "vm_name": vm_name})

# AWS outputs fallback
public_ip = data.get("public_ip",{}).get("value")
instance_id = data.get("instance_id",{}).get("value")
region = data.get("region",{}).get("value") or args.region
if public_ip or instance_id:
    cmdb.update({"platform":"aws","public_ip": public_ip, "instance_id": instance_id, "region": region})

# Try AWS tagging only if instance_id found
if instance_id:
    res = try_tag_aws(instance_id, region)
    cmdb["aws"] = res

pathlib.Path("cmdb.json").write_text(json.dumps(cmdb, indent=2))
print("Wrote cmdb.json")
