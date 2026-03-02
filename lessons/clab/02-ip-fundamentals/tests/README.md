# Tests -- Lesson 2: IP Fundamentals

## What These Tests Validate

- **Environment:** containerlab, Docker, and Ansible are installed
- **Topology structure:** valid YAML, correct nodes/links, no `latest` tags
- **Ansible configuration:** inventory, playbook, templates, and host_vars are valid
- **Lab deployment:** all 4 containers come up
- **Connectivity:** adjacent hosts can ping after Ansible config is applied

## Prerequisites

- Docker running and SR Linux image pulled
- Ansible installed
- Deployment and connectivity tests deploy the lab (takes ~60 seconds)

## Running Tests

From this lesson's directory (`lessons/clab/02-ip-fundamentals/`):

```bash
uv run --project ../../.. --group test pytest tests/ -v
```

To run only structural tests (no lab deployment):

```bash
uv run --project ../../.. --group test pytest tests/test_ip_fundamentals.py -v -k "not TestLabDeployment and not TestConnectivity"
```
