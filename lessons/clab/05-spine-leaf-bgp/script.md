# Lesson 5: Spine-Leaf Networking with BGP - Video Script

## Lesson Information

| Field | Value |
|-------|-------|
| **Lesson Number** | 05 |
| **Title** | Spine-Leaf Networking with BGP |
| **Duration Target** | 12-14 minutes |
| **Prerequisites** | Lessons 0-4, gNMIc installed (`gnmic version`), 16 GB RAM |
| **Learning Objectives** | Explain Clos architecture, configure eBGP underlay on a 6-router fabric, observe ECMP across spines, diagnose fabric resilience under spine failure |

---

## Pre-Recording Checklist

- [ ] Lab environment tested (containerlab installed, Docker running)
- [ ] gNMIc installed: `gnmic version`
- [ ] Lesson 04 lab destroyed: `containerlab destroy --all`
- [ ] SR Linux image pulled: `docker pull ghcr.io/nokia/srlinux:24.10.1`
- [ ] Alpine image pulled: `docker pull alpine:3.20`
- [ ] Minimum 16 GB RAM available: `free -h`
- [ ] Screen resolution set (1920x1080)
- [ ] Terminal font size increased (14-16pt)
- [ ] Notifications disabled
- [ ] Clean terminal: `clear && history -c`
- [ ] No labs running: `containerlab inspect --all`

---

## Script

### Opening Hook (30 seconds)

> **[VOICEOVER - Terminal visible]**
>
> "Last lesson, you configured BGP on 3 routers and watched them exchange routes. That was the mechanics. Today we use those mechanics to build something real -- a spine-leaf fabric. In a data center, every server needs to reach every other server with predictable latency and maximum bandwidth. Spine-leaf delivers both: equal-cost paths between every pair of racks, all links active, no wasted capacity. This is the topology running under every major cloud provider and every large-scale Kubernetes deployment."

**Visual:** Terminal showing lesson 04 triangle topology diagram, then transition to spine-leaf diagram

---

### Section 1: Why Spine-Leaf? (2 minutes)

> **[VOICEOVER]**
>
> "In lesson 4, our 3 routers were fully meshed -- every router had a direct link to every other router. That's 3 links total. Add a 4th router and you need 6 links. With 10 routers, 45 links. With 50, over 1,200. Full mesh grows as N-squared -- it collapses under its own weight.
>
> Traditional data centers solved this with a 3-tier architecture: core, distribution, and access layers. But those designs relied on Spanning Tree Protocol, which blocks redundant links to prevent loops. You pay for redundant cables, then STP disables half of them. Wasteful.
>
> Clos spine-leaf architecture fixes both problems. Instead of connecting everything to everything, you split the network into two tiers: spines and leaves. Every leaf connects to every spine, but there are no leaf-to-leaf or spine-to-spine links. With 4 leaves and 2 spines, that's only 8 links -- not 15 for a full mesh of 6 devices. Every path between any two leaves is exactly 2 router hops -- leaf, spine, leaf. And because all paths are equal length, the router can use ECMP -- equal-cost multipath -- to load-balance across all spines simultaneously. No blocked links. No wasted bandwidth.
>
> The key insight: to add more bandwidth, you add more spines. To add more servers, you add more leaves. Each tier scales independently without redesigning the other."

**Visual:** Three diagrams side by side -- full mesh (link explosion highlighted), 3-tier with STP (blocked links in red), Clos (all links green/active)

**Key Points:**
- Full mesh: link count grows as N*(N-1)/2, doesn't scale
- 3-tier + STP: blocks redundant links, wastes capacity
- Clos: structured 2-tier, all links active via ECMP, tiers scale independently

**Transition:** "Let's look at the specific design of our fabric."

---

### Section 2: Clos Design (2 minutes)

> **[VOICEOVER]**
>
> "Here's our fabric: 2 spines, 4 leaves, 4 hosts. Every leaf connects to every spine -- that's 8 links. Each link gets a /31 point-to-point subnet, just like lesson 4. Each leaf also connects to one host on a /24 subnet.
>
> For BGP, we use the RFC 7938 model: one unique AS number per device. Spines are AS 65100 and 65101. Leaves are AS 65001 through 65004. This means every link is an eBGP session. The spines' peer-group is called 'leaves' with 4 neighbors each. The leaves' peer-group is called 'spines' with 2 neighbors each. Total: 8 unique BGP sessions across the fabric.
>
> Why a unique AS per device? It keeps the BGP configuration simple and uniform. Every device has the same structure -- just different AS numbers and neighbor IPs. And it makes AS path the natural metric for path selection: a 2-hop path through one spine has AS path length 2, and there's no shorter alternative. All spine paths are equal cost, which is the prerequisite for ECMP -- though on SR Linux you still need to explicitly enable multipath to get load balancing."

**Visual:** Topology diagram with AS numbers labeled, /31 subnets on links, /24 subnets on host segments

```
     spine1 (AS 65100)    spine2 (AS 65101)
      / |  \    \          / |   \    \
   leaf1 leaf2 leaf3  leaf4
 (65001)(65002)(65003)(65004)
    |      |      |      |
  host1  host2  host3  host4
```

**Key Points:**
- /31 point-to-point links between every spine-leaf pair
- RFC 7938: unique ASN per device, every link is eBGP
- 8 total BGP sessions (4 leaves x 2 spines)
- Equal AS path length enables ECMP (with multipath configured)

**Transition:** "Let's deploy this and see it work."

---

### Section 3: Deploying the Fabric (2 minutes)

> **[VOICEOVER]**
>
> "The topology file defines 10 containers: 6 SR Linux routers and 4 Alpine hosts. Startup configs in the topology/configs directory handle the base interface addressing -- each router's /31 uplinks and /24 host-facing interface are pre-configured. BGP is not configured yet. We'll apply that separately with gNMIc, just like lesson 4."

```bash
cd lessons/clab/05-spine-leaf-bgp
containerlab deploy -t topology/lab.clab.yml
```

**Expected output:** Table showing 10 running containers

> "10 containers are up. Let's verify that cross-leaf connectivity doesn't work yet -- without BGP, the leaves don't know about each other's host subnets."

```bash
docker exec clab-spine-leaf-bgp-host1 ping -c 2 -W 3 10.20.4.2
```

> "Ping fails. leaf1 has no route to 10.20.4.0/24. The fabric is physically wired, but without BGP, no routes are exchanged. Same lesson we learned in lesson 2 -- wires alone don't create connectivity."

**Visual:** Terminal showing deploy output and failed ping

**Transition:** "Now let's light up BGP across the entire fabric."

---

### Section 4: Live Demo -- Configure and Verify (3 minutes)

> **[VOICEOVER]**
>
> "Six gNMIc commands, one per router. Each config file does four things: creates routing policies -- import-all, export-connected with a prefix-set filter for host subnets only, and export-bgp for re-advertising learned routes. It enables the ipv4-unicast address family with multipath for ECMP. And it configures BGP with the correct AS, router-ID, peer-group, and neighbors."

```bash
cd gnmic
gnmic -a clab-spine-leaf-bgp-spine1:57400 set --request-file configs/spine1-bgp.json
gnmic -a clab-spine-leaf-bgp-spine2:57400 set --request-file configs/spine2-bgp.json
gnmic -a clab-spine-leaf-bgp-leaf1:57400 set --request-file configs/leaf1-bgp.json
gnmic -a clab-spine-leaf-bgp-leaf2:57400 set --request-file configs/leaf2-bgp.json
gnmic -a clab-spine-leaf-bgp-leaf3:57400 set --request-file configs/leaf3-bgp.json
gnmic -a clab-spine-leaf-bgp-leaf4:57400 set --request-file configs/leaf4-bgp.json
```

> "All six applied. Let's check the sessions. I'll start with spine1 -- it should have 4 established sessions, one to each leaf."

```bash
docker exec -it clab-spine-leaf-bgp-spine1 sr_cli -c \
  "show network-instance default protocols bgp neighbor"
```

> "Four neighbors, all Established. Now leaf1 -- it should have 2 sessions, one to each spine."

```bash
docker exec -it clab-spine-leaf-bgp-leaf1 sr_cli -c \
  "show network-instance default protocols bgp neighbor"
```

> "Two sessions, both Established. Now let's look at the routing table on leaf1."

```bash
docker exec -it clab-spine-leaf-bgp-leaf1 sr_cli -c \
  "show network-instance default route-table ipv4-unicast summary"
```

> "This is the key moment. Look at the remote host subnets -- 10.20.2.0/24, 10.20.3.0/24, 10.20.4.0/24. Each one shows two next-hops: one via spine1 at 10.10.1.0, one via spine2 at 10.10.2.0. That's ECMP. The router will hash traffic flows across both spines for load distribution.
>
> Now the connectivity test."

```bash
docker exec clab-spine-leaf-bgp-host1 ping -c 3 10.20.2.2
docker exec clab-spine-leaf-bgp-host1 ping -c 3 10.20.3.2
docker exec clab-spine-leaf-bgp-host1 ping -c 3 10.20.4.2
```

> "All three succeed. host1 can reach host2, host3, and host4 -- all on different leaves, all going through the spine tier. Notice TTL is 61: starting at 64, minus 3 hops -- leaf1, spine, leaf. Every cross-leaf path is exactly 2 router hops."

**Visual:** Full terminal showing BGP neighbors, routing table with ECMP entries, successful pings

---

### Section 5: Live Demo -- Spine Failure (2 minutes)

> **[VOICEOVER]**
>
> "The whole point of a multi-spine fabric is resilience. Let's take down spine1 and watch what happens."

```bash
docker exec -it clab-spine-leaf-bgp-spine1 sr_cli
```

```
enter candidate
set / interface ethernet-1/1 admin-state disable
set / interface ethernet-1/2 admin-state disable
set / interface ethernet-1/3 admin-state disable
set / interface ethernet-1/4 admin-state disable
commit now
exit
```

> "All four spine1 interfaces are down. In another terminal, let's run a continuous ping."

```bash
docker exec clab-spine-leaf-bgp-host1 ping -c 20 -i 1 10.20.4.2
```

> "A few packets lost during BGP convergence, then it recovers. All traffic now flows through spine2. Let's check the routing table."

```bash
docker exec -it clab-spine-leaf-bgp-leaf1 sr_cli -c \
  "show network-instance default route-table ipv4-unicast summary"
```

> "The ECMP entries dropped from 2 next-hops to 1. All routes now point only to spine2 at 10.10.2.0. We lost 50% of our aggregate bandwidth, but zero connectivity. Every host can still reach every other host.
>
> Let's bring spine1 back."

```bash
docker exec -it clab-spine-leaf-bgp-spine1 sr_cli
```

```
enter candidate
set / interface ethernet-1/1 admin-state enable
set / interface ethernet-1/2 admin-state enable
set / interface ethernet-1/3 admin-state enable
set / interface ethernet-1/4 admin-state enable
commit now
exit
```

> "After a few seconds, BGP re-establishes and ECMP returns to 2 paths. The fabric healed itself -- twice. Once when spine1 went down, once when it came back. No human intervention for either event."

**Visual:** Split view -- ping output showing loss/recovery on one side, routing table showing ECMP change on the other

---

### Recap (30 seconds)

> **[VOICEOVER]**
>
> "Let's recap:
>
> - Clos spine-leaf replaces full mesh with a structured 2-tier design that scales. Every leaf connects to every spine, creating equal-cost paths across the fabric.
> - RFC 7938 gives each device a unique AS number. Every link is eBGP. But ECMP isn't automatic on SR Linux -- you need to set multipath maximum-paths to enable load balancing across spines.
> - Prefix-set filters keep the routing table clean. Only host subnets belong in BGP -- the /31 fabric links are already known via direct connection.
> - Spine failures degrade capacity but not connectivity. With 2 spines, you lose 50% bandwidth. With 4 spines, only 25%. The fabric degrades gracefully.
> - This is the architecture under every major cloud and Kubernetes deployment. When you troubleshoot pod networking, this is what's underneath."

---

### Closing (30 seconds)

> **[VOICEOVER]**
>
> "Head to the exercises folder. You'll deploy the fabric yourself, observe ECMP in the routing table, simulate a spine failure, and -- in the challenge exercise -- see how a rogue prefix can hijack traffic across the entire fabric using longest-prefix-match.
>
> This lesson gave us pure L3 routing: packets move between racks based on IP prefixes. But what about VMs and containers that need to be on the same Layer 2 subnet across different racks? That's the problem EVPN/VXLAN solves -- and that's coming next.
>
> Happy labbing!"

**Visual:** Show exercises folder, then Clos diagram with "EVPN/VXLAN overlay" teaser text

---

## Post-Recording Checklist

- [ ] Lab destroyed: `containerlab destroy --all`
- [ ] Timing verified: ~12-14 minutes
- [ ] All commands worked correctly
- [ ] Transcript updated with actual output

---

## B-Roll / Supplementary Footage Needed

1. Clos spine-leaf topology diagram with AS numbers and IP addressing
2. ECMP animation showing traffic hashing across two spines
3. Side-by-side comparison: full mesh vs 3-tier vs Clos
4. Spine failure visualization (spine going dark, traffic rerouting through remaining spine)
5. ECMP routing table transition: 2 next-hops -> 1 next-hop -> 2 next-hops

---

## Notes for Editing

- **0:00-0:30** - Hook, overlay lesson 04 triangle topology diagram
- **0:30-2:30** - Why spine-leaf, three architecture comparison diagrams
- **2:30-4:30** - Clos design, topology diagram with AS numbers and addressing
- **4:30-6:30** - Deploy fabric, show 10 containers and failed ping (no BGP yet)
- **6:30-9:30** - Configure BGP, verify sessions, show ECMP routing table, cross-leaf pings
- **9:30-11:30** - Spine failure demo, ping loss/recovery, ECMP path count change, restore
- **11:30-12:00** - Recap bullet points overlay
- **12:00-12:30** - Closing, exercises call-to-action, EVPN/VXLAN teaser
