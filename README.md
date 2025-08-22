# Network Automation Mini-Project (vSphere + ITSM)
**Default Flow:** Terraform (vSphere) + Ansible + GitLab CI/CD → **provision VM** → **create ServiceNow/Jira ticket** via Python API.  
AWS variant still included; switch by setting `TF_DIR=terraform/aws`.

---

## What’s New
1. **vSphere is the default compute target** (`TF_DIR=terraform/vsphere` in pipeline).
2. **ITSM step added**: `notify_itsm` creates a **ServiceNow** CMDB/Incident and/or a **Jira** Issue from `cmdb.json`.
3. **Inventory builder** supports both **AWS** (`public_ip`) and **vSphere** (`vm_ip`).
4. **Integration step** writes a generic `cmdb.json` even if not tagging on AWS.

---

## What you’ll build
1. **Terraform (vSphere by default)**: clones a VM from a template and outputs `vm_ip`.
2. **Ansible**: connects to the VM and installs/configures **NGINX**.
3. **GitLab CI/CD**: `validate → plan → apply → deploy → integrate → notify_itsm` (+ manual `destroy`).
4. **Python integration**:
   - `scripts/tag_and_register.py`: builds a lightweight `cmdb.json` from Terraform outputs and tags **AWS** instances when using the AWS path.
   - `scripts/servicenow_jira.py`: reads `cmdb.json` and creates records in **ServiceNow** and/or **Jira**.

---

## Prerequisites
- **GitLab** project with runners.
- **vSphere** credentials (user, password, server) and a valid **template** to clone.
- (Optional) **AWS** credentials if you switch to the AWS path.
- SSH connectivity to VM; set **`ANSIBLE_SSH_USER`** according to your template OS (e.g., `ubuntu`).

---

## GitLab CI/CD Variables (Settings → CI/CD → Variables)
Mark secrets Masked/Protected where appropriate.

### Common
| Key | Value | Notes |
|---|---|---|
| `TF_DIR` | `terraform/vsphere` | Default (set `terraform/aws` to use AWS) |
| `PROJECT_NAME` | `netauto-mini` | Tagging + ticket context |
| `ANSIBLE_SSH_USER` | `ubuntu` | Typical for Ubuntu templates; change if needed |
| `ANSIBLE_PRIVATE_KEY` (File) | *your private key file* | Pipeline writes it to `ansible/.ssh/id_rsa` |

### vSphere
| Key | Value |
|---|---|
| `VSPHERE_USER` | user@example |
| `VSPHERE_PASSWORD` | ***** |
| `VSPHERE_SERVER` | vcsa.example.local |

Map IDs/names inside `terraform/vsphere/variables.tf` and pass them via TF VARS or defaults: `datacenter`, `cluster`, `datastore`, `network_name`, `template_name`, `vm_name`, `cpu`, `memory_mb`.

### ServiceNow (optional, any subset)
| Key | Value | Example |
|---|---|---|
| `SNOW_INSTANCE` | base url without protocol | `dev12345.service-now.com` |
| `SNOW_USER` | user | `api.user` |
| `SNOW_PASSWORD` | password | `*****` |
| `SNOW_TABLE` | `incident` or CMDB table | `incident` or `cmdb_ci_server` |

### Jira (optional, any subset)
| Key | Value | Example |
|---|---|---|
| `JIRA_BASE_URL` | base url with https | `https://your-domain.atlassian.net` |
| `JIRA_USER` | user email | `you@domain.com` |
| `JIRA_API_TOKEN` | token | `*****` |
| `JIRA_PROJECT_KEY` | project key | `OPS` |
| `JIRA_ISSUE_TYPE` | type | `Incident` or `Task` |

> The ITSM step will **only** call the systems for which complete variables are present.

---

## How the pipeline works
1. **tf_validate** → init + validate.
2. **tf_plan** → create plan artifact.
3. **tf_apply** → apply infra and write **`terraform/outputs.json`**.
4. **ansible_deploy** → create inventory from outputs (supports `vm_ip` or `public_ip`), install NGINX.
5. **py_integrate** → write **`cmdb.json`** (and tags AWS instance when on the AWS path).
6. **notify_itsm** → create **ServiceNow** record and/or **Jira** issue from `cmdb.json`.
7. **tf_destroy (manual)** → teardown.

---

## Local quick test (vSphere path)
```bash
# 1) Export vSphere variables for Terraform (or put in a tfvars file)
export VSPHERE_USER="user" VSPHERE_PASSWORD="pass" VSPHERE_SERVER="vcsa.local"

cd terraform/vsphere
terraform init
terraform apply -auto-approve   -var="datacenter=YOUR_DC"   -var="cluster=YOUR_CLUSTER"   -var="datastore=YOUR_DATASTORE"   -var="network_name=YOUR_PORTGROUP"   -var="template_name=YOUR_TEMPLATE"   -var="vm_name=netauto-web"

terraform output -json > ../outputs.json

# 2) Build Ansible inventory from outputs
python3 ../../scripts/make_inventory.py --in ../outputs.json --out ../../ansible/inventory.ini

# 3) Run Ansible
pip3 install ansible
ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i ../../ansible/inventory.ini ../../ansible/playbook.yml -u ubuntu --private-key ~/.ssh/id_rsa

# 4) Integration (generic cmdb.json; AWS tagging skipped if no AWS outputs)
pip3 install boto3 requests
python3 ../../scripts/tag_and_register.py --in ../outputs.json --project netauto-mini --region us-east-1

# 5) ITSM creation (ServiceNow/Jira) – set env vars as needed
python3 ../../scripts/servicenow_jira.py --cmdb ../../cmdb.json
```

---

## Demo talking points
- **Network automation** across hypervisor/cloud targets (vSphere/AWS) using the same delivery pipeline.
- **TOGAF mapping**: governance (artifacts, tags, traceability), architecture continuity (IaC modules), compliance checkpoints.
- **Python integrations** to enterprise systems (ServiceNow/Jira) post‑provision.
- **Repeatable pattern** extendable to Cisco with Ansible network modules or to multi-cloud.

---

## Cleanup
Run the **tf_destroy** job or `terraform destroy` locally to avoid compute costs.
