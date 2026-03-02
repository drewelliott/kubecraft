# Tests -- Lesson 0: Docker Networking

## What These Tests Validate

- Exercise 1: Docker bridge, veth pairs, container networking
- Exercise 2: Manual namespace lab (red/blue with br-study)
- Exercise 3: NAT/masquerade for internet access

## Prerequisites

Some tests require exercises to be completed first. Read each test's docstring for specifics.

## Running Tests

From this lesson's directory (`lessons/clab/00-docker-networking/`):

```bash
uv run --project ../../.. --group test pytest tests/ -v
```

To run a specific test class:

```bash
uv run --project ../../.. --group test pytest tests/test_docker_networking.py::TestClassName -v
```
