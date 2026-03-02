# Tests -- Lesson 1: Containerlab Primer

## What These Tests Validate

- **Environment:** containerlab and Docker are installed
- **Topology structure:** valid YAML, correct nodes/links, no `latest` tags
- **Lab deployment:** lab deploys, containers run, inspect works, lab destroys cleanly
- **Exercise files:** solutions directory exists with valid topology files

## Prerequisites

- Topology and deployment tests require Docker running and SR Linux image pulled
- `TestLabDeployment` tests deploy and destroy the lab (takes ~60 seconds)

## Running Tests

From this lesson's directory (`lessons/clab/01-containerlab-primer/`):

```bash
uv run --project ../../.. --group test pytest tests/ -v
```

To run only the fast structural tests (no lab deployment):

```bash
uv run --project ../../.. --group test pytest tests/test_lab.py -v -k "not TestLabDeployment"
```
