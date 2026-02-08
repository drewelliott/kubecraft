# CLAUDE.md - Project Instructions for Claude Code

## Project Overview

This repository contains a network fundamentals training course for junior DevOps engineers. The course uses **containerlab** to teach networking concepts through hands-on labs with real network operating systems running in containers.

**Target audience:** Junior DevOps engineers with Docker/Linux/Kubernetes knowledge but limited networking experience.

## Repository Structure

```
kubecraft/
├── docs/                    # User-facing documentation
│   ├── getting-started/     # Prerequisites, setup guides
│   ├── reference/           # Cheatsheets, command references
│   └── resources/           # External links, glossary
├── lessons/
│   └── clab/                # Containerlab training series
│       ├── XX-lesson-name/  # Individual lessons
│       │   ├── README.md    # Student-facing
│       │   ├── topology/    # Student-facing
│       │   ├── exercises/   # Student-facing
│       │   ├── solutions/   # Student-facing
│       │   ├── tests/       # Student-facing
│       │   └── script.md    # Instructor-only (video script)
│       ├── COURSE_PLAN.md
│       └── VIDEO_SCRIPT_TEMPLATE.md
└── CLAUDE.md                # This file
```

## Content Audience Convention

The `main` branch contains both student-facing and instructor-only content. The convention:

**Student-facing** (what students interact with after forking):
- `README.md` -- Lesson overview, objectives, key concepts
- `topology/` -- Containerlab topology files
- `exercises/` -- Hands-on exercises
- `solutions/` -- Exercise solutions (intentionally visible)
- `tests/` -- Automated validation

**Instructor-only** (video production and personal notes):
- `script.md` -- Video recording script
- `COURSE_PLAN.md` -- Course-level planning
- `VIDEO_SCRIPT_TEMPLATE.md` -- Template for scripts

Students fork the repo and work through lessons in order. Instructor-only files are present in the fork but students are not directed to them.

## Git Workflow

**IMPORTANT:** Always follow this workflow:

1. **Never commit directly to main** - Always create a feature branch first
2. **Branch naming:** `feature/<descriptive-name>` (e.g., `feature/lesson-2-ip-fundamentals`)
3. **Push branches to origin** before creating PRs
4. **Use GitHub CLI** for PR creation: `gh pr create --base main`

```bash
# Standard workflow
git checkout -b feature/your-feature-name
# ... make changes ...
git add <specific-files>
git commit -m "Descriptive message"
git push -u origin feature/your-feature-name
gh pr create --base main --title "Title" --body "Description"
```

## Content Guidelines

### Lesson Structure

Each lesson must include:
- `README.md` - Objectives, outline, key concepts
- `topology/` - Containerlab topology files
- `exercises/README.md` - Hands-on exercises (typically 3-5)
- `solutions/README.md` - Exercise solutions
- `tests/` - pytest-based automated validation
- `script.md` - Video recording script

### Writing Style

- **No emojis** unless explicitly requested
- **Plain markdown** with Mermaid diagrams for visuals
- **Concise explanations** - explain concepts, show commands
- **DevOps perspective** - always relate networking to DevOps use cases

### Network Operating Systems

**Use only free, containerized network OS images:**
- Nokia SR Linux: `ghcr.io/nokia/srlinux:<version>` (primary choice)
- FRRouting: Open source Linux routing
- VyOS: For edge/firewall scenarios
- Alpine Linux: For host containers

**IMPORTANT:** Never use `latest` tag - always specify version tags for reproducibility.

### Video Scripts

Use `VIDEO_SCRIPT_TEMPLATE.md` for all lesson scripts. Include:
- Pre-recording checklist
- Timed sections with voiceover text
- Exact commands with expected output
- Post-recording checklist
- B-roll/editing notes

### Automated Tests

Tests should verify:
- Environment setup (tools installed, Docker working)
- Topology file validity (YAML structure, required fields)
- Lab deployment success
- Exercise completion validation

Use pytest with descriptive test classes:
```python
class TestEnvironment:
    """Verify lab environment is correctly set up."""

class TestTopologyStructure:
    """Verify topology file has correct structure."""
```

## Course Content Guidelines

### GitOps Tool Progression

Each lesson introduces a new automation tool:
| Lesson | Tool |
|--------|------|
| 0-1 | Git, Docker Compose |
| 2-3 | Ansible |
| 4 | Terraform |
| 5 | ArgoCD patterns |
| 6 | Ansible + Jinja2 |
| 7 | pytest for network validation |
| 8 | Full CI/CD pipeline |

### Domain Focus

Prioritize topics by DevOps relevance:
1. Data center (spine-leaf, BGP, EVPN-VXLAN) - K8s networking foundation
2. Cloud patterns (VPC simulation, hybrid connectivity)
3. Edge/WAN (site-to-site, NAT)

### Exercise Design

- **Structured exercises** with clear steps and expected outcomes
- **Solutions provided** in separate folder
- **Automated validation** via pytest
- **Challenge exercises** for advanced learners (optional)

## Technical Constraints

- **No paid/licensed tools** - Strictly free and open source
- **No `latest` tags** - Always pin specific versions
- **Native Linux environment** - Students run containerlab directly on Linux
- **Fork workflow** - Students fork and submit via PR

## Common Commands

```bash
# Containerlab
containerlab deploy -t topology/lab.clab.yml
containerlab destroy -t topology/lab.clab.yml --cleanup
containerlab inspect -t topology/lab.clab.yml

# SR Linux CLI access
docker exec -it clab-<lab>-<node> sr_cli

# Run tests
pytest tests/ -v

# Create PR
gh pr create --base main --title "Title" --body "Description"
```

## File Naming Conventions

- Lessons: `XX-kebab-case-name/` (e.g., `01-containerlab-primer/`)
- Topology files: `*.clab.yml`
- Test files: `test_*.py`
- Scripts: `script.md`

## When Adding New Lessons

1. Copy structure from existing lesson
2. Update `lessons/clab/README.md` lesson index
3. Update `lessons/clab/COURSE_PLAN.md` if scope changes
4. Create topology files for the lesson
5. Write exercises before solutions
6. Write tests that validate exercise completion
7. Create video script using template

## PR Description Template

```markdown
## Summary
- Brief description of changes

## Lesson(s) Affected
- List lessons modified or added

## Test plan
- [ ] Topology files tested with containerlab
- [ ] Exercises verified to work
- [ ] Automated tests pass
- [ ] Video script reviewed for accuracy
```
