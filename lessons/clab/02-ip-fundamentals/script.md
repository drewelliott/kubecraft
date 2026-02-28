# Lesson 2: IP Fundamentals & Basic Connectivity - Video Script

## Lesson Information

| Field | Value |
|-------|-------|
| **Lesson Number** | 02 |
| **Title** | IP Fundamentals & Basic Connectivity |
| **Duration Target** | 12-15 minutes |
| **Prerequisites** | Lesson 0: Docker Networking, Lesson 1: Containerlab Primer, Ansible installed |
| **Learning Objectives** | Explain OSI Layers 1-4, configure IP addresses, use Ansible with Jinja2, verify connectivity, diagnose issues |

---

## Pre-Recording Checklist

- [ ] Lab environment tested (containerlab installed, Docker running)
- [ ] Ansible installed: `ansible --version`
- [ ] SR Linux image pulled: `docker pull ghcr.io/nokia/srlinux:24.10.1`
- [ ] Alpine image pulled: `docker pull alpine:3.20`
- [ ] Screen resolution set (1920x1080)
- [ ] Terminal font size increased (14-16pt)
- [ ] Notifications disabled
- [ ] Clean terminal: `clear && history -c`
- [ ] No labs running: `containerlab destroy --all`

---

## Script

### Opening Hook (30 seconds)

> **[VOICEOVER - Terminal visible]**
>
> "Your app returns 'connection refused.' Is it a network problem or an application problem? By the end of this lesson, you'll know exactly how to tell -- because you'll understand what IP addresses actually are, how devices find each other on a network, and how to automate configuration so you never have to type the same settings twice."

**Visual:** Terminal with clean prompt

---

### Section 1: The Networking Stack -- Layers 1-4 (3 minutes)

> **[VOICEOVER]**
>
> "In Lesson 0, you built container networking from scratch using Linux primitives. You may not have realized it, but you were working through the networking stack -- the same model that every packet follows.
>
> Let me map what you already know to the official layers."

**Visual:** Show table or diagram (Excalidraw recommended)

> "Layer 1 -- Physical. In our labs, this is the veth pair. It's the virtual cable between two endpoints. If it's not there, nothing else matters.
>
> Layer 2 -- Data Link. This is where MAC addresses and bridges live. Remember docker0? That's a Layer 2 switch. It forwards frames based on MAC addresses. The question at this layer is: 'Which device on this wire?'
>
> Layer 3 -- Network. This is what we're configuring today. IP addresses and subnets. The question here is: 'Which network? Which host on that network?'
>
> Layer 4 -- Transport. TCP and UDP ports. This is what your applications use. Port 80 for HTTP, port 443 for HTTPS, port 5432 for PostgreSQL.
>
> Here's the key insight for troubleshooting: always work bottom-up. Is the link up? Can you see the MAC? Can you reach the IP? Is the port open? If you skip layers, you'll waste hours."

**Key Points:**
- L1 = veth pairs = "cable"
- L2 = MAC + bridges = "which device on this wire?"
- L3 = IP + subnets = "which network? which host?"
- L4 = TCP/UDP ports = "which application?"

**Transition:** "Now let's focus on Layer 3 -- IP addressing."

---

### Section 2: IP Addressing & Subnets (3 minutes)

> **[VOICEOVER]**
>
> "An IP address has two parts: a network portion and a host portion. The subnet mask tells you where the split is.
>
> Take 10.1.1.2 with a /24 mask. The /24 means the first 24 bits are the network: 10.1.1. The last 8 bits are the host: .2. This gives us 256 addresses in the 10.1.1.0/24 subnet -- from .0 to .255.
>
> A /30 mask gives you only 4 addresses -- useful for point-to-point links between routers. A /32 is a single address -- used for loopbacks.
>
> Here's the critical question: are two devices on the same network? If 10.1.1.2/24 wants to talk to 10.1.1.1/24, they share the same network portion -- 10.1.1. They can communicate directly using Layer 2. The sending device uses ARP to discover the destination's MAC address.
>
> But if 10.1.1.2 wants to talk to 10.1.3.2? Different network. That packet needs to go through a router. And that's what we'll set up in Lesson 3.
>
> ARP -- Address Resolution Protocol -- is the bridge between Layer 3 and Layer 2. When host1 wants to send a packet to 10.1.1.1, it broadcasts: 'Who has 10.1.1.1? Tell 10.1.1.2.' The router responds with its MAC address, and now host1 can build the Ethernet frame."

**Visual:** Show ARP request/reply diagram

```bash
# View ARP table
docker exec clab-ip-fundamentals-host1 arp -n
```

**Transition:** "Now that we understand IP addressing, let's automate the configuration."

---

### Section 3: Ansible 101 with Jinja2 (3 minutes)

> **[VOICEOVER]**
>
> "We have two routers to configure today. We could log into each one and type commands manually. But what if we had 200 routers? Manual configuration doesn't scale, and it's error-prone.
>
> Ansible solves this. It has four key pieces."

**Visual:** Show `ansible/inventory.yml`

> "First, the inventory. This tells Ansible what devices to manage. We have two routers with their management IP addresses."

```yaml
# ansible/inventory.yml
all:
  children:
    routers:
      hosts:
        srl1:
          ansible_host: 172.20.20.11
        srl2:
          ansible_host: 172.20.20.12
```

**Visual:** Show `ansible/host_vars/srl1.yml`

> "Second, host variables. Each device gets its own data file. For srl1, we define two interfaces with their IP addresses."

```yaml
# ansible/host_vars/srl1.yml
interfaces:
  - name: ethernet-1/1
    ipv4_address: 10.1.1.1/24
    description: Link to host1
  - name: ethernet-1/2
    ipv4_address: 10.1.2.1/24
    description: Link to srl2
```

**Visual:** Show `ansible/templates/srl_interfaces.json.j2`

> "Third, the Jinja2 template. This is where the magic happens. Watch the for loop: for each interface in the interfaces list, it generates a set of SR Linux CLI commands. The double curly braces pull in values from the host variables.
>
> This one template works for every router. Only the data changes. That's the power of templating -- you write the logic once, and the data drives the output."

```jinja2
{% for iface in interfaces %}
set / interface {{ iface.name }} subinterface 0 ipv4 address {{ iface.ipv4_address }}
{% endfor %}
```

> "Fourth, the playbook ties it all together. It renders the template for each router using that router's host variables, then pushes the commands via the SR Linux JSON-RPC API."

**Key Points:**
- Inventory = what to configure
- Host vars = the data for each device
- Template = the logic (one template, many devices)
- Playbook = the orchestration

**Transition:** "Let's see it in action."

---

### Section 4: Live Demo -- Deploy and Configure (3 minutes)

> **[VOICEOVER]**
>
> "Let's deploy our 4-node topology and configure it."

```bash
cd lessons/clab/02-ip-fundamentals

# Deploy the topology
containerlab deploy -t topology/lab.clab.yml
```

> "Containerlab is creating four containers -- two SR Linux routers and two Alpine Linux hosts -- and wiring them together with virtual links. The hosts get their IP addresses automatically from the topology file's exec commands."

**Expected output:** Table showing 4 running containers

```bash
# Now apply the router configuration
cd ansible
ansible-playbook -i inventory.yml playbook.yml
```

> "Ansible is rendering the Jinja2 template for each router, then sending the CLI commands via HTTP to the JSON-RPC API. Watch -- srl1 gets configured first, then srl2."

**Expected output:** Ansible play recap showing `ok=4` for each host

> "Let's verify on srl1."

```bash
docker exec -it clab-ip-fundamentals-srl1 sr_cli -c "show interface brief"
```

> "Both interfaces are up with IP addresses assigned. The configuration worked."

---

### Section 5: Verification (2 minutes)

> **[VOICEOVER]**
>
> "Let's test connectivity."

```bash
# Adjacent ping -- host1 to srl1 (same subnet)
docker exec clab-ip-fundamentals-host1 ping -c 3 10.1.1.1
```

> "Three packets sent, three received. host1 and srl1 are on the same 10.1.1.0/24 subnet, so they communicate directly."

```bash
# Cross-subnet ping -- host1 to host2 (different subnets)
docker exec clab-ip-fundamentals-host1 ping -c 3 10.1.3.2
```

> "Zero packets received. host1 sends the packet to its gateway -- srl1. But srl1 only knows about 10.1.1.0/24 and 10.1.2.0/24. It has no route to 10.1.3.0/24, so the packet is dropped.
>
> This is exactly the problem that routing solves -- and that's what we'll configure in Lesson 3."

```bash
# Check ARP table
docker exec clab-ip-fundamentals-host1 arp -n
```

> "Notice the ARP entry -- host1 has learned srl1's MAC address. That's Layer 3 resolving to Layer 2."

---

### Recap (30 seconds)

> **[VOICEOVER]**
>
> "Let's recap what we covered:
>
> - The networking stack has layers: physical, data link, network, and transport. Troubleshoot bottom-up.
> - IP addresses have a network part and a host part. The subnet mask determines which is which.
> - Devices on the same subnet communicate directly via ARP. Different subnets need a router.
> - Ansible with Jinja2 templates lets you write configuration logic once and apply it to any number of devices."

---

### Closing (30 seconds)

> **[VOICEOVER]**
>
> "Now it's your turn. In the exercises folder, you'll:
> - Trace through the Jinja2 template to understand exactly what it generates
> - Add a loopback interface by modifying only the data, not the template
> - Diagnose three intentionally broken scenarios: a disabled interface, a subnet mismatch, and a missing gateway
>
> In the next lesson, we'll add static routes so that host1 can finally reach host2 across the routers.
>
> Happy labbing!"

**Visual:** Show exercises folder

---

## Post-Recording Checklist

- [ ] Lab destroyed: `containerlab destroy --all`
- [ ] Timing verified: ~12-15 minutes
- [ ] All commands worked correctly
- [ ] Transcript updated with actual output

---

## B-Roll / Supplementary Footage Needed

1. OSI layer diagram (Excalidraw) -- show packet traversing all 4 layers
2. ARP request/reply animation
3. Jinja2 template rendering visualization (show variables being substituted)
4. Split-screen: template on left, rendered output for srl1 on right, then srl2

---

## Notes for Editing

- **0:00-0:30** - Hook, can overlay network diagram animation
- **0:30-3:30** - OSI layers, use Excalidraw or diagram overlay
- **3:30-6:30** - IP/subnets, highlight subnet calculations on screen
- **6:30-9:30** - Ansible 101, split screen for template + host_vars
- **9:30-12:30** - Live demo, full terminal
- **12:30-14:00** - Verification, highlight ping output
- **End** - Call-to-action overlay for exercises
