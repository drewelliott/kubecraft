# Network Fundamentals Lab - Course Plan

## Course Overview

**Course Name:** Network Fundamentals Lab
**Target Audience:** Junior DevOps engineers with basic Docker, Linux, and Kubernetes knowledge but limited networking experience
**Format:** 6-8 video lessons (10-15 minutes each) with hands-on labs
**Environment:** Native Linux with containerlab
**Part of:** Larger DevOps curriculum (assumes K8s fundamentals completed)

---

## Learning Outcomes

By the end of this series, students will be able to:

1. **Troubleshoot network issues** - Diagnose connectivity problems, read routing tables, trace network paths
2. **Design simple topologies** - Create containerlab environments for testing network changes
3. **Automate network configuration** - Write playbooks and configs for network device automation using GitOps principles

---

## Series Outline (9 Lessons)

### Prerequisite Lesson

#### Lesson 0: Docker Networking Fundamentals
**Duration:** 10-15 minutes
**Objective:** Bridge knowledge from K8s course to network-specific concepts

**Topics:**
- Docker network drivers: bridge, host, none, macvlan
- Container network namespaces
- Port mapping and exposure
- Docker Compose networking
- How containers communicate (within host, across hosts)
- Container DNS resolution
- Inspecting container networks

**Hands-on Exercise:**
- Create custom bridge network
- Connect containers and test communication
- Inspect network configuration with `docker network inspect`
- Compare bridge vs host networking behavior

**GitOps Tool:** Docker Compose for defining networks

---

### Foundation Lessons (1-3)

#### Lesson 1: Containerlab Primer
**Duration:** 10-15 minutes
**Objective:** Set up containerlab environment and deploy your first network topology

**Topics:**
- What is containerlab and why DevOps engineers should care
- Containerlab resources: documentation, Discord community, GitHub topics
- Setting up the containerlab environment
- Pulling free network OS images (Nokia SR Linux)
- Understanding topology files (YAML structure)
- Deploying your first 2-node topology
- Essential containerlab commands (deploy, destroy, inspect, graph)
- Connecting to network devices

**Hands-on Exercise:**
- Deploy a simple 2-node topology
- Connect to both nodes and verify connectivity
- Modify topology and redeploy

**GitOps Tool:** Git basics for versioning topology files

---

#### Lesson 2: IP Fundamentals & Basic Connectivity
**Duration:** 10-15 minutes
**Objective:** Configure IP addressing and validate connectivity

**Topics:**
- IP addressing fundamentals (IPv4, subnets, CIDR notation)
- Interface configuration on network devices
- The networking stack (L2 vs L3)
- Connectivity testing (ping, traceroute)
- ARP and neighbor discovery
- Reading and interpreting output

**Hands-on Exercise:**
- Configure IP addresses on a 3-node linear topology
- Verify connectivity between adjacent nodes
- Troubleshoot intentionally broken connectivity

**GitOps Tool:** Introduction to Ansible for configuration management

---

#### Lesson 3: Routing Basics
**Duration:** 10-15 minutes
**Objective:** Understand routing tables and configure static routes

**Topics:**
- Routing table fundamentals
- Default gateways and route selection
- Static routing configuration
- Multi-hop topologies
- Route verification and debugging
- When packets get dropped

**Hands-on Exercise:**
- Build a 4-node topology with multiple subnets
- Configure static routes for end-to-end connectivity
- Use Ansible playbook to deploy routing configuration

**GitOps Tool:** Ansible playbooks for network config (continued)

---

### Domain-Specific Lessons (4-6)

#### Lesson 4: Dynamic Routing with BGP
**Duration:** 10-15 minutes
**Objective:** Replace static routes with eBGP and understand dynamic route propagation

**Topics:**
- Why dynamic routing? Limitations of static routes at scale
- eBGP fundamentals: autonomous systems, peering, route advertisement
- Path selection and convergence behavior
- Comparing static vs dynamic: predictability vs adaptability
- Relevant for: Kubernetes networking, cloud provider backbone design

**Hands-on Exercise:**
- Deploy the evolved hub-and-spoke topology with eBGP
- Use gNMIc to observe BGP state and route propagation
- Simulate link failures and observe convergence
- Compare routing tables before and after BGP

**GitOps Tool:** gNMIc for streaming telemetry and configuration

---

#### Lesson 5: Spine-Leaf Networking with BGP
**Duration:** 10-15 minutes
**Objective:** Build a CLOS fabric with eBGP and understand ECMP

**Topics:**
- Why spine-leaf architecture? (vs traditional 3-tier)
- CLOS fabric design: spines, leaves, and hosts
- eBGP in the data center: one AS per leaf, shared spine AS
- ECMP: equal-cost multipath for load distribution
- Fabric resilience: surviving spine and leaf failures
- Relevant for: Kubernetes networking, container orchestration

**Hands-on Exercise:**
- Deploy a 2-spine, 2-leaf fabric with hosts
- Verify full-mesh BGP peering and ECMP paths
- Simulate spine and leaf failures, observe resilience
- Use gNMIc to monitor fabric health

**GitOps Tool:** gNMIc + startup-config for declarative fabric provisioning

---

#### Lessons 6+: TBD
Future topics under consideration:
- EVPN/VXLAN overlay networking
- Cloud provider networking patterns
- Network troubleshooting methodology
- Capstone: full GitOps network lab

---

### Skills & Capstone (7-8)

#### Lesson 7: Network Troubleshooting for DevOps
**Duration:** 10-15 minutes
**Objective:** Systematic approach to diagnosing network issues

**Topics:**
- Troubleshooting methodology (OSI model approach)
- Essential diagnostic commands
- Packet capture in containerlab (tcpdump, Wireshark)
- Common issues and their symptoms
- When to escalate to network team

**Hands-on Exercise:**
- Diagnose 3 pre-broken topologies
- Document findings and fixes
- Create automated health check tests

**GitOps Tool:** pytest-based network validation tests

---

#### Lesson 8: Capstone - Full GitOps Network Lab
**Duration:** 10-15 minutes
**Objective:** Combine all skills in a real-world scenario

**Topics:**
- Multi-domain topology (DC + Cloud + Edge)
- Full GitOps workflow demonstration
- Automated testing pipeline
- CI/CD for network changes
- Best practices summary

**Hands-on Exercise:**
- Deploy comprehensive topology from Git
- Make a change via PR workflow
- Watch automated validation run
- Merge and see changes applied

**GitOps Tool:** Full pipeline (Git + Ansible + pytest + CI)

---

## Repository Structure

```
kubecraft/
├── README.md                           # Course overview, prerequisites
├── CONTRIBUTING.md                     # Fork workflow for students
│
├── docs/                               # User-facing documentation
│   ├── getting-started/
│   │   ├── prerequisites.md            # What you need before starting
│   │   ├── linux-setup.md              # Linux environment setup guide
│   │   └── fork-workflow.md            # How to fork and submit exercises
│   │
│   ├── reference/
│   │   ├── containerlab-cheatsheet.md  # Quick command reference
│   │   ├── srlinux-cheatsheet.md       # SR Linux CLI basics
│   │   ├── network-commands.md         # Common network diagnostic commands
│   │   └── troubleshooting.md          # Common issues and solutions
│   │
│   └── resources/
│       ├── links.md                    # External resources, docs, Discord
│       └── glossary.md                 # Networking terms for DevOps
│
└── lessons/
    └── clab/
        ├── README.md                   # Series overview and lesson index
        │
        ├── 01-containerlab-primer/
        │   ├── README.md               # Lesson objectives, outline
        │   ├── topology/
        │   │   └── lab.clab.yml        # Containerlab topology file
        │   ├── configs/                # Device configuration files
        │   ├── exercises/
        │   │   └── README.md           # Exercise instructions
        │   ├── solutions/
        │   │   └── README.md           # Exercise solutions
        │   ├── tests/
        │   │   └── test_connectivity.py # Automated validation
        │   └── script.md               # Video script
        │
        ├── 02-ip-fundamentals/
        │   └── ... (same structure)
        │
        ├── 03-routing-basics/
        │   └── ... (same structure)
        │
        ├── 04-dynamic-routing-bgp/
        │   └── ... (same structure)
        │
        └── 05-spine-leaf-bgp/
            └── ... (same structure)
```

---

## Lesson 1 Detailed Outline: Containerlab Primer

### Video Script Outline

**Opening (1 minute)**
- Hook: "As a DevOps engineer, you'll inevitably hit a networking issue. This series gives you the skills to understand, debug, and even automate network infrastructure."
- What we'll cover today: containerlab setup, first topology, essential commands

**Section 1: What is Containerlab? (2 minutes)**
- Container-based network emulation
- Why it matters for DevOps:
  - Test network changes before production
  - Understand how your apps traverse the network
  - Reproduce network issues locally
- Show: containerlab.dev documentation site
- Show: GitHub topics for containerlab examples
- Mention: Discord community for help

**Section 2: Environment Setup (3 minutes)**
- Linux environment setup (reference linux-setup.md)
- Verify containerlab installation: `containerlab version`
- Pull Nokia SR Linux image (explain: free, no license needed)
- Verify Docker is running: `docker ps`

**Section 3: Your First Topology (4 minutes)**
- Explain topology file structure (YAML)
- Walk through example: 2 SR Linux nodes connected
- Key elements:
  - `name`: Lab name
  - `topology.nodes`: Define devices
  - `topology.links`: Connect them
- Deploy: `containerlab deploy -t lab.clab.yml`
- Show output, explain what's happening

**Section 4: Working with Your Lab (3 minutes)**
- `containerlab inspect`: See running containers
- `docker ps`: Alternative view
- Connect to a node: `docker exec -it <node> sr_cli`
- Basic SR Linux commands:
  - `show interface brief`
  - `show version`
- Generate topology diagram: `containerlab graph`

**Section 5: Cleanup (1 minute)**
- `containerlab destroy -t lab.clab.yml`
- Verify cleanup
- Mention: `--cleanup` flag for removing configs

**Closing (1 minute)**
- Recap what we learned
- Tease next lesson: IP addressing and connectivity
- Point to exercises in the repo

---

### Exercise Specification

**Exercise 1: Deploy and Explore**
1. Deploy the provided 2-node topology
2. Connect to each node and run `show interface brief`
3. Record the interface names and MAC addresses
4. Generate the topology graph and save it

**Exercise 2: Modify the Topology**
1. Add a third node to the topology
2. Connect it to one of the existing nodes
3. Deploy the modified topology
4. Verify all three nodes are running

**Exercise 3: Challenge - Find the Documentation**
1. Find the containerlab documentation for SR Linux
2. Locate the Discord invite link
3. Find a GitHub repository with containerlab examples for a topic that interests you
4. Document your findings in a markdown file

---

### Automated Test Specification

```python
# tests/test_lab_deployed.py

def test_nodes_running():
    """Verify all topology nodes are running containers"""
    # Check docker ps for expected containers

def test_node_connectivity():
    """Verify we can exec into each node"""
    # docker exec should succeed

def test_interfaces_exist():
    """Verify expected interfaces are present"""
    # Run show interface, parse output
```

---

## Free Network OS Options

For this course, we'll use exclusively free, containerized network operating systems:

| NOS | Vendor | License | Notes |
|-----|--------|---------|-------|
| SR Linux | Nokia | Free | Primary choice - excellent docs, full-featured |
| FRRouting | Open Source | Free | Linux-based, familiar environment |
| VyOS | Open Source | Free | Full router/firewall, good for edge lessons |
| Arista cEOS | Arista | Free* | Requires Arista account, download separately |
| SONiC | Microsoft/OCP | Free | Advanced option for DC lessons |

*cEOS is free but requires registration. We'll note this in lessons where it's used.

---

## GitOps Tools Progression

| Lesson | Tool | Concept |
|--------|------|---------|
| 1 | Git | Version control for topology files |
| 2-3 | Ansible | Configuration management, playbooks |
| 4 | gNMIc | Streaming telemetry and network state |
| 5 | gNMIc + startup-config | Declarative fabric provisioning |
| 6+ | TBD | Future lessons in development |

---

## Next Steps

1. [ ] Review and approve this course plan
2. [ ] Create repository folder structure
3. [ ] Create Lesson 1 topology files
4. [ ] Write Lesson 1 exercises and solutions
5. [ ] Create automated tests for Lesson 1
6. [ ] Record Lesson 1 video
7. [ ] Write transcript
8. [ ] Iterate for remaining lessons

---

## Questions for Review

1. Does the 8-lesson structure feel right, or should we consolidate to 6?
2. Should Lesson 4 (Data Center) come before or after Lesson 5 (Cloud Patterns)?
3. Are there specific network concepts critical for your curriculum that we should ensure are covered?
4. Should we include a "Lesson 0" that covers Docker networking basics as a bridge from the K8s course?
