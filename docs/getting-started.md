# Getting Started

Everything you need to start the Network Fundamentals Lab course.

## Required Skills

You should be comfortable with:

- **Containers** -- pulling images, running containers, reading `docker ps` output
- **Linux command line** -- navigating the filesystem, editing files, using pipes
- **Git basics** -- cloning repos, committing changes, pushing to a remote

If you need to brush up:
- [Docker Getting Started](https://docs.docker.com/get-started/)
- [Linux Command Line Basics](https://ubuntu.com/tutorials/command-line-for-beginners)
- [Git Handbook](https://guides.github.com/introduction/git-handbook/)

## Required Tools

Install these before starting. Follow each project's official install guide:

| Tool | Purpose | Install Guide |
|------|---------|---------------|
| Docker | Container runtime | [docs.docker.com/engine/install](https://docs.docker.com/engine/install/) |
| containerlab | Network lab orchestration | [containerlab.dev/install](https://containerlab.dev/install/) |
| uv | Python package runner (for tests) | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| Git | Version control | [git-scm.com](https://git-scm.com) |

After installing, verify everything works:

```bash
docker version
containerlab version
uv --version
git --version
```

### SR Linux Image

Pull the Nokia SR Linux image used throughout the course:

```bash
docker pull ghcr.io/nokia/srlinux:24.10.1
```

## Hardware Requirements

| | Minimum | Recommended |
|---|---------|-------------|
| RAM | 8 GB | 16 GB |
| Disk | 20 GB free | 50 GB free |
| CPU | 4 cores | 8 cores |

## Fork and Clone

```bash
# Fork the repo (requires GitHub CLI)
gh repo fork drewelliott/kubecraft --clone
cd kubecraft

# Add upstream remote for future updates
git remote add upstream https://github.com/drewelliott/kubecraft.git
```

If you don't have the GitHub CLI, fork via the GitHub web UI, then:

```bash
git clone https://github.com/YOUR-USERNAME/kubecraft.git
cd kubecraft
git remote add upstream https://github.com/drewelliott/kubecraft.git
```

### Syncing Updates

When new lessons are published:

```bash
git fetch upstream
git merge upstream/main
git push origin main
```

## Running Tests

Each lesson has automated tests in its `tests/` directory. Run them with uv from the lesson folder:

```bash
cd lessons/clab/01-containerlab-primer
uv run --project ../../.. --group test pytest tests/ -v
```

See each lesson's `tests/README.md` for details on what the tests validate.

## Self-Assessment

Before starting, verify you can:

- [ ] Run `docker ps` and understand the output
- [ ] Run `containerlab version` successfully
- [ ] Clone a Git repository
- [ ] Explain what an IP address is (even at a basic level)

## Start Learning

Begin with [Lesson 0: Docker Networking Fundamentals](../lessons/clab/00-docker-networking/).

Already comfortable with Docker networking? Skip to [Lesson 1: Containerlab Primer](../lessons/clab/01-containerlab-primer/).
