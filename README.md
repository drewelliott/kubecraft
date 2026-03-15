<p align="center">
  <img src="https://img.shields.io/badge/platform-Linux-informational?style=flat&logo=linux&logoColor=white" alt="Linux">
  <img src="https://img.shields.io/badge/containerlab-network%20labs-blue?style=flat&logo=docker&logoColor=white" alt="Containerlab">
  <img src="https://img.shields.io/badge/SR%20Linux-24.10.1-orange?style=flat&logo=nokia&logoColor=white" alt="SR Linux">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat" alt="License">
  <a href="https://github.com/drewelliott/kubecraft/actions/workflows/sync-student-branch.yml">
    <img src="https://github.com/drewelliott/kubecraft/actions/workflows/sync-student-branch.yml/badge.svg?branch=instructor" alt="Sync Status">
  </a>
</p>

# Kubecraft: Network Fundamentals for DevOps Engineers

Hands-on networking labs built on [containerlab](https://containerlab.dev) -- real network operating systems running in containers, configured with real automation tools.

## Who This Is For

You know Docker, Linux, and Kubernetes. You don't know (or want to know more about) networking. This course bridges that gap through labs you can run on your own machine -- no cloud accounts, no expensive equipment, no licenses.

## What You'll Learn

```
Lesson 0   Docker Networking              Linux bridges, namespaces, veth pairs, NAT
Lesson 1   Containerlab Primer            Topology files, deploy/destroy, SR Linux CLI
Lesson 2   IP Fundamentals                Addressing, subnets, Ansible + Jinja2 automation
Lesson 3   Routing Basics                 Static routes, routing tables, break/fix labs
Lesson 4   Dynamic Routing Protocols      Coming soon
```

Each lesson introduces automation tools alongside networking concepts -- Git, Ansible, Jinja2 -- so you build DevOps muscle memory, not just networking knowledge.

> **[Browse the full course outline and lesson details](lessons/clab/)**

## Quick Start

### 1. Fork and clone

```bash
gh repo fork drewelliott/kubecraft --clone
cd kubecraft
```

### 2. Install prerequisites

- **Docker** -- running and accessible
- **containerlab** -- [install guide](https://containerlab.dev/install/)
- **uv** -- [install guide](https://docs.astral.sh/uv/getting-started/installation/)
- **SR Linux image** -- `docker pull ghcr.io/nokia/srlinux:24.10.1`

> See the [Getting Started guide](docs/getting-started.md) for full prerequisites and setup.

### 3. Start learning

```bash
cd lessons/clab/00-docker-networking
```

Each lesson has a README with objectives, exercises, solutions, and automated tests. Work through them in order.

## Reference

| Resource | Description |
|----------|-------------|
| [Containerlab Cheatsheet](docs/reference/containerlab-cheatsheet.md) | Deploy, inspect, destroy, graph |
| [SR Linux CLI Cheatsheet](docs/reference/srlinux-cheatsheet.md) | Interface config, show commands, modes |
| [Network Commands](docs/reference/network-commands.md) | ping, traceroute, ip, tcpdump |
| [Troubleshooting Guide](docs/reference/troubleshooting.md) | Common issues and fixes |
| [Glossary](docs/resources/glossary.md) | Networking terms defined |

## How It Works

Each lesson follows the same pattern:

1. **Read** the lesson README for concepts and objectives
2. **Deploy** the lab with `containerlab deploy`
3. **Complete** the exercises (including break/fix troubleshooting)
4. **Validate** your work with `pytest tests/ -v`
5. **Destroy** the lab and commit your answers

Solutions are provided. Tests are provided. The only way to fail is to not try.

## Contributing

Found a bug? Have a suggestion? [Open an issue](https://github.com/drewelliott/kubecraft/issues) or see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This training material is provided for educational purposes. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <a href="https://containerlab.dev"><img src="https://img.shields.io/badge/powered%20by-containerlab-blue?style=for-the-badge" alt="Powered by containerlab"></a>
  <a href="https://learn.srlinux.dev"><img src="https://img.shields.io/badge/runs-Nokia%20SR%20Linux-orange?style=for-the-badge" alt="Nokia SR Linux"></a>
</p>
