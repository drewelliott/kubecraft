# Tests -- Lesson 3: Routing Basics

## What These Tests Validate

- **Environment:** containerlab, Docker, and Ansible are installed
- **Topology structure:** 6 nodes, 5 links, management IPs, host exec commands, no `latest` tags
- **Ansible configuration:** inventory (3 routers), playbook, templates, host_vars with static routes
- **Lab deployment:** all 6 containers come up
- **Connectivity:** host1<->host2, host1<->host3, host2<->host3 after Ansible config

## Prerequisites

- Docker running and SR Linux image pulled
- Ansible installed
- Deployment and connectivity tests deploy the lab and run Ansible (takes ~2 minutes)

## Running Tests

From this lesson's directory (`lessons/clab/03-routing-basics/`):

```bash
uv run --project ../../.. --group test pytest tests/ -v
```

To run only structural tests (no lab deployment):

```bash
uv run --project ../../.. --group test pytest tests/test_routing_basics.py -v -k "not TestLabDeployment and not TestConnectivity"
```
