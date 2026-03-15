# Lesson 4 Solutions

Reference solutions for the Dynamic Routing with BGP exercises.

## Exercise 1: Deploy and Verify Baseline

**Cross-subnet pings (all succeed with static routes):**

```bash
$ docker exec clab-dynamic-routing-bgp-host1 ping -c 3 10.1.4.2
PING 10.1.4.2 (10.1.4.2): 56 data bytes
64 bytes from 10.1.4.2: seq=0 ttl=62 time=2.345 ms
64 bytes from 10.1.4.2: seq=1 ttl=62 time=1.123 ms
64 bytes from 10.1.4.2: seq=2 ttl=62 time=0.987 ms
--- 10.1.4.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

```bash
$ docker exec clab-dynamic-routing-bgp-host1 ping -c 3 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes
64 bytes from 10.1.5.2: seq=0 ttl=62 time=2.456 ms
64 bytes from 10.1.5.2: seq=1 ttl=62 time=1.234 ms
64 bytes from 10.1.5.2: seq=2 ttl=62 time=1.012 ms
--- 10.1.5.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

```bash
$ docker exec clab-dynamic-routing-bgp-host2 ping -c 3 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes
64 bytes from 10.1.5.2: seq=0 ttl=61 time=3.456 ms
64 bytes from 10.1.5.2: seq=1 ttl=61 time=2.123 ms
64 bytes from 10.1.5.2: seq=2 ttl=61 time=1.876 ms
--- 10.1.5.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

This is the lesson 03 end state. Static routes provide full connectivity. All cross-subnet traffic flows through srl1 (the hub) because it is the only router with routes to every subnet.

**Routing table on srl1 (all routes are `static`):**

```
A:srl1# show network-instance default route-table ipv4-unicast summary
+------------+-------+------------+-------------------+----------+
|   Prefix   | Type  | Route-Owner| Next-hop          | Metric   |
+============+=======+============+===================+==========+
| 10.1.1.0/24| local | net_inst   | ethernet-1/1.0    | 0        |
| 10.1.2.0/24| local | net_inst   | ethernet-1/2.0    | 0        |
| 10.1.3.0/24| local | net_inst   | ethernet-1/3.0    | 0        |
| 10.1.4.0/24| static| static     | 10.1.2.2          | 1        |
| 10.1.5.0/24| static| static     | 10.1.3.2          | 1        |
+------------+-------+------------+-------------------+----------+
```

Note the `static` type on the remote subnets. These are the manually configured routes from lesson 03. The `local` routes are automatically created for directly connected interfaces.

**Unconfigured srl2-srl3 link (ethernet-1/3 on srl2):**

```
A:srl2# show interface ethernet-1/3
===============================================================================
  ethernet-1/3 is up, speed 25G, type None
    ethernet-1/3.0 is admin-state disable
      Network-instance: --
      Oper state      : down
      IPv4 addr       : --
===============================================================================
```

ethernet-1/3 is physically up (the cable is wired in the topology) but has no subinterface configured and is not assigned to a network instance. This link will be activated in exercise 3.

---

## Exercise 2: Replace Static Routes with eBGP

**Step 1: Delete static routes on all routers using gNMIc.**

```bash
$ gnmic -a clab-dynamic-routing-bgp-srl1:57400 -u admin -p NokiaSrl1! \
    --skip-verify -e json_ietf set \
    --delete /network-instance[name=default]/static-routes \
    --delete /network-instance[name=default]/next-hop-groups
{
  "time": "2026-03-15T12:00:01Z",
  "results": [
    {
      "operation": "DELETE",
      "path": "network-instance[name=default]/static-routes"
    },
    {
      "operation": "DELETE",
      "path": "network-instance[name=default]/next-hop-groups"
    }
  ]
}
```

Repeat for srl2 and srl3 (changing `-a` to `clab-dynamic-routing-bgp-srl2:57400` and `clab-dynamic-routing-bgp-srl3:57400`). An empty or acknowledgment response with no errors means the delete succeeded.

**Step 2: Cross-subnet pings now FAIL.**

```bash
$ docker exec clab-dynamic-routing-bgp-host1 ping -c 2 -W 3 10.1.4.2
PING 10.1.4.2 (10.1.4.2): 56 data bytes

--- 10.1.4.2 ping statistics ---
2 packets transmitted, 0 packets received, 100% packet loss
```

With the static routes removed, each router only knows about its directly connected subnets. srl1 has no route to 10.1.4.0/24 (host2's subnet), so it drops the packet. This is the same broken state from lesson 02.

**Step 3: Apply BGP configuration via gNMIc.**

```bash
$ gnmic -a clab-dynamic-routing-bgp-srl1:57400 -u admin -p NokiaSrl1! \
    --skip-verify -e json_ietf set --update-file configs/srl1-bgp.json
{
  "time": "2026-03-15T12:01:15Z",
  "results": [
    {
      "operation": "UPDATE",
      "path": "routing-policy/policy[name=export-connected]"
    },
    {
      "operation": "UPDATE",
      "path": "network-instance[name=default]/protocols/bgp"
    }
  ]
}
```

Repeat for srl2 and srl3 with their respective config files. Each config creates the `export-connected` routing policy and enables BGP with the appropriate AS number and neighbors.

**Step 4: BGP neighbors all Established.**

```
A:srl1# show network-instance default protocols bgp neighbor
+---------------+--------+--------+-----------+--------+--------+--------+
| Peer          | Group  | AS     | Admin     | Session| Rcv    | Active |
|               |        |        | State     | State  | Routes | Routes |
+===============+========+========+===========+========+========+========+
| 10.1.2.2      |ebgp-pe | 65002  | enable    |establis| 2      | 2      |
|               |  ers   |        |           | hed    |        |        |
+---------------+--------+--------+-----------+--------+--------+--------+
| 10.1.3.2      |ebgp-pe | 65003  | enable    |establis| 2      | 2      |
|               |  ers   |        |           | hed    |        |        |
+---------------+--------+--------+-----------+--------+--------+--------+
```

Both sessions show `established` -- the only healthy BGP state. srl1 receives 2 routes from each peer: srl2 advertises 10.1.2.0/24 and 10.1.4.0/24 (its connected subnets), and srl3 advertises 10.1.3.0/24 and 10.1.5.0/24.

**Step 5: Cross-subnet pings work again.**

```bash
$ docker exec clab-dynamic-routing-bgp-host1 ping -c 3 10.1.4.2
PING 10.1.4.2 (10.1.4.2): 56 data bytes
64 bytes from 10.1.4.2: seq=0 ttl=62 time=2.567 ms
64 bytes from 10.1.4.2: seq=1 ttl=62 time=1.234 ms
64 bytes from 10.1.4.2: seq=2 ttl=62 time=0.987 ms
--- 10.1.4.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

**Step 6: Routing table now shows `bgp` instead of `static`.**

```
A:srl1# show network-instance default route-table ipv4-unicast summary
+------------+-------+------------+-------------------+----------+
|   Prefix   | Type  | Route-Owner| Next-hop          | Metric   |
+============+=======+============+===================+==========+
| 10.1.1.0/24| local | net_inst   | ethernet-1/1.0    | 0        |
| 10.1.2.0/24| local | net_inst   | ethernet-1/2.0    | 0        |
| 10.1.3.0/24| local | net_inst   | ethernet-1/3.0    | 0        |
| 10.1.4.0/24| bgp   | bgp_mgr   | 10.1.2.2          | 0        |
| 10.1.5.0/24| bgp   | bgp_mgr   | 10.1.3.2          | 0        |
+------------+-------+------------+-------------------+----------+
```

**Side-by-side comparison:**

| Prefix | Before (static) | After (BGP) |
|--------|-----------------|-------------|
| 10.1.4.0/24 | Type: `static`, Owner: `static`, Metric: 1 | Type: `bgp`, Owner: `bgp_mgr`, Metric: 0 |
| 10.1.5.0/24 | Type: `static`, Owner: `static`, Metric: 1 | Type: `bgp`, Owner: `bgp_mgr`, Metric: 0 |

The next-hops are identical -- the same routers are reachable via the same interfaces. What changed is how the routes were learned. Static routes were manually configured; BGP routes were dynamically exchanged between peers.

**Why we delete static routes first:** On SR Linux, static routes have an administrative distance of 5 while BGP routes have an administrative distance of 170. Lower administrative distance wins. If you apply BGP config without removing the static routes first, the BGP routes are learned but never installed in the forwarding table because the static routes have priority. The routing table would still show `static` and you would think BGP was broken. Deleting the static routes first ensures BGP routes are the only option and get installed immediately.

**Key lesson:** Administrative distance determines which routing source is trusted most. Static routes (distance 5) beat BGP (distance 170) on SR Linux. When migrating from static to dynamic routing, always remove the static routes or the old routes will mask the new ones.

---

## Exercise 3: Enable Direct Link and Path Selection

**Step 1: Traceroute BEFORE the new link (3 router hops through the hub).**

```bash
$ docker exec clab-dynamic-routing-bgp-host2 traceroute -n -w 2 10.1.5.2
traceroute to 10.1.5.2 (10.1.5.2), 30 hops max, 60 byte packets
 1  10.1.4.1  1.234 ms  0.567 ms  0.432 ms
 2  10.1.2.1  1.456 ms  1.123 ms  0.987 ms
 3  10.1.3.2  1.678 ms  1.345 ms  1.234 ms
 4  10.1.5.2  2.123 ms  1.567 ms  1.456 ms
```

The path is host2 -> srl2 (10.1.4.1) -> srl1 (10.1.2.1) -> srl3 (10.1.3.2) -> host3 (10.1.5.2). Three router hops because srl2 has no direct route to srl3 -- it must go through the hub.

**Step 2: Configure the srl2-srl3 interfaces.**

```bash
$ gnmic -a clab-dynamic-routing-bgp-srl2:57400 -u admin -p NokiaSrl1! \
    --skip-verify -e json_ietf set --update-file configs/srl2-new-link.json
{
  "time": "2026-03-15T12:05:00Z",
  "results": [
    {
      "operation": "UPDATE",
      "path": "interface[name=ethernet-1/3]"
    },
    {
      "operation": "UPDATE",
      "path": "network-instance[name=default]"
    }
  ]
}

$ gnmic -a clab-dynamic-routing-bgp-srl3:57400 -u admin -p NokiaSrl1! \
    --skip-verify -e json_ietf set --update-file configs/srl3-new-link.json
{
  "time": "2026-03-15T12:05:05Z",
  "results": [
    {
      "operation": "UPDATE",
      "path": "interface[name=ethernet-1/3]"
    },
    {
      "operation": "UPDATE",
      "path": "network-instance[name=default]"
    }
  ]
}
```

**Step 3: Add BGP neighbors for the new link.**

```bash
$ gnmic -a clab-dynamic-routing-bgp-srl2:57400 -u admin -p NokiaSrl1! \
    --skip-verify -e json_ietf set --update-file configs/srl2-bgp-srl3.json
{
  "time": "2026-03-15T12:05:30Z",
  "results": [
    {
      "operation": "UPDATE",
      "path": "network-instance[name=default]/protocols/bgp/neighbor[peer-address=10.1.6.2]"
    }
  ]
}

$ gnmic -a clab-dynamic-routing-bgp-srl3:57400 -u admin -p NokiaSrl1! \
    --skip-verify -e json_ietf set --update-file configs/srl3-bgp-srl2.json
{
  "time": "2026-03-15T12:05:35Z",
  "results": [
    {
      "operation": "UPDATE",
      "path": "network-instance[name=default]/protocols/bgp/neighbor[peer-address=10.1.6.1]"
    }
  ]
}
```

**Step 4: New BGP session established.**

```
A:srl2# show network-instance default protocols bgp neighbor
+---------------+--------+--------+-----------+--------+--------+--------+
| Peer          | Group  | AS     | Admin     | Session| Rcv    | Active |
|               |        |        | State     | State  | Routes | Routes |
+===============+========+========+===========+========+========+========+
| 10.1.2.1      |ebgp-pe | 65001  | enable    |establis| 3      | 3      |
|               |  ers   |        |           | hed    |        |        |
+---------------+--------+--------+-----------+--------+--------+--------+
| 10.1.6.2      |ebgp-pe | 65003  | enable    |establis| 2      | 1      |
|               |  ers   |        |           | hed    |        |        |
+---------------+--------+--------+-----------+--------+--------+--------+
```

srl2 now has two BGP peers: srl1 (via 10.1.2.1) and srl3 (via 10.1.6.2). The new session to srl3 shows `established`. srl2 receives 2 routes from srl3 (10.1.3.0/24 and 10.1.5.0/24) but only installs 1 as active -- specifically, 10.1.5.0/24 is now preferred via the direct link because it has a shorter AS path.

**Step 5: Traceroute AFTER the new link (2 router hops, direct).**

```bash
$ docker exec clab-dynamic-routing-bgp-host2 traceroute -n -w 2 10.1.5.2
traceroute to 10.1.5.2 (10.1.5.2), 30 hops max, 60 byte packets
 1  10.1.4.1  1.234 ms  0.567 ms  0.432 ms
 2  10.1.6.2  1.345 ms  0.987 ms  0.876 ms
 3  10.1.5.2  1.567 ms  1.123 ms  1.012 ms
```

The path is now host2 -> srl2 (10.1.4.1) -> srl3 (10.1.6.2) -> host3 (10.1.5.2). Two router hops -- srl1 is bypassed entirely.

**Why BGP chose the direct path:** BGP path selection prefers shorter AS paths. Before the new link, srl2's only route to 10.1.5.0/24 was through srl1:

- **Old path AS path:** [65001, 65003] -- the route was learned from srl1 (AS 65001), who learned it from srl3 (AS 65003). Two AS hops.
- **New path AS path:** [65003] -- the route was learned directly from srl3 (AS 65003). One AS hop.

BGP prefers the path with fewer AS hops, so the direct route through srl3 wins automatically. No manual route changes were needed -- BGP recalculated the best path the moment the new session came up.

In lesson 03, adding a cable accomplished nothing. The physical link existed, but without manually adding static routes on both srl2 and srl3, it sat idle. With BGP, the new link was automatically discovered and traffic shifted within seconds. This is the fundamental difference between static and dynamic routing: dynamic protocols react to topology changes on their own.

**Key lesson:** BGP path selection prefers shorter AS paths. Adding a direct link between two routers creates a shorter AS path that BGP automatically prefers over the longer path through the hub. No manual intervention is required.

---

## Exercise 4: Break/Fix -- Missing Export Policy

**Symptom: host1 and host2 cannot reach host3, but host3 can reach them.**

```bash
$ docker exec clab-dynamic-routing-bgp-host1 ping -c 3 -W 5 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes

--- 10.1.5.2 ping statistics ---
3 packets transmitted, 0 packets received, 100% packet loss

$ docker exec clab-dynamic-routing-bgp-host3 ping -c 3 10.1.1.2
PING 10.1.1.2 (10.1.1.2): 56 data bytes
64 bytes from 10.1.1.2: seq=0 ttl=62 time=2.345 ms
64 bytes from 10.1.1.2: seq=1 ttl=62 time=1.123 ms
64 bytes from 10.1.1.2: seq=2 ttl=62 time=0.987 ms
--- 10.1.1.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

The asymmetry is the clue. host3 can ping out (it has routes from srl1 and srl2) but nobody can reach host3 (srl3 is not advertising its routes).

**BGP neighbor detail on srl3 showing sent-routes=0:**

```
A:srl3# show network-instance default protocols bgp neighbor 10.1.3.1 detail
+---------------------------------------------------------------------+
| Peer: 10.1.3.1                                                     |
| Group: ebgp-peers                                                   |
| Peer AS: 65001                                                      |
| Session state: established                                          |
| Last state: established                                             |
| Export policy: --                                                   |
| Import policy: --                                                   |
|                                                                     |
| Messages:                                                           |
|   Sent:          12    Received:      14                            |
| Routes:                                                             |
|   Received:       3    Active:         3                            |
|   Sent:           0                                                 |
+---------------------------------------------------------------------+
```

The critical fields: `Export policy: --` (no export policy) and `Sent: 0` (srl3 is advertising zero routes). The session is `established` -- the TCP connection and BGP OPEN/KEEPALIVE exchange are working perfectly. The problem is in the UPDATE messages: srl3 has nothing to announce because the export policy was deleted.

**Why this happens:** SR Linux is secure by default. BGP sessions use a default-deny model for route export. Without an explicit export policy, a router receives routes from its peers (it can learn about the world) but advertises nothing back (the world cannot learn about it). The `export-connected` policy we created earlier matched `protocol local` (directly connected subnets) and accepted them for advertisement. Deleting that policy means srl3's connected routes (10.1.3.0/24 and 10.1.5.0/24) are never placed into UPDATE messages.

**Why the asymmetry exists:** srl3 still receives routes from srl1 and srl2 because their export policies are intact -- they are happily advertising their subnets. So srl3 has a full routing table and host3 can reach everything. But srl1 and srl2 have no routes to 10.1.3.0/24 or 10.1.5.0/24 because srl3 is advertising nothing. From their perspective, those subnets do not exist.

**Fix (re-add the export policy):**

```
A:srl3# enter candidate
set / network-instance default protocols bgp group ebgp-peers export-policy [export-connected]
commit now
```

**Verification:**

```bash
$ docker exec clab-dynamic-routing-bgp-host1 ping -c 3 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes
64 bytes from 10.1.5.2: seq=0 ttl=62 time=2.345 ms
64 bytes from 10.1.5.2: seq=1 ttl=62 time=1.123 ms
64 bytes from 10.1.5.2: seq=2 ttl=62 time=0.987 ms
--- 10.1.5.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

After restoring the export policy, srl3 immediately sends UPDATE messages containing its connected routes. srl1 and srl2 install them in their routing tables and connectivity is restored.

**Key lesson:** BGP session UP does not mean routes are flowing. Always check prefix counts. A session in `established` state only means the two routers can communicate -- it says nothing about whether routes are actually being exchanged. On SR Linux, the most common cause of "session up, no routes" is a missing or misconfigured export policy.

---

## Exercise 5: Break/Fix -- Link Failure with Automatic Reroute

**Continuous ping showing loss then recovery:**

```bash
$ docker exec clab-dynamic-routing-bgp-host1 ping -c 30 -i 1 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes
64 bytes from 10.1.5.2: seq=0 ttl=62 time=2.345 ms
64 bytes from 10.1.5.2: seq=1 ttl=62 time=1.123 ms
64 bytes from 10.1.5.2: seq=2 ttl=62 time=0.987 ms

--- link disabled here ---

64 bytes from 10.1.5.2: seq=3 ttl=62 time=1.234 ms

--- BGP hold timer expires, session drops, route withdrawn ---
--- srl1 installs alternate path via srl2 ---

(several packets lost)

64 bytes from 10.1.5.2: seq=10 ttl=61 time=3.456 ms
64 bytes from 10.1.5.2: seq=11 ttl=61 time=2.123 ms
64 bytes from 10.1.5.2: seq=12 ttl=61 time=1.876 ms
...
64 bytes from 10.1.5.2: seq=29 ttl=61 time=1.567 ms
--- 10.1.5.2 ping statistics ---
30 packets transmitted, 24 packets received, 20% packet loss
```

Notice the TTL change: before the link failure, TTL=62 (2 router hops: srl1 -> srl3). After convergence, TTL=61 (3 router hops: srl1 -> srl2 -> srl3). The network found a longer but working path.

**BGP neighbor table on srl1 showing srl3 session down:**

```
A:srl1# show network-instance default protocols bgp neighbor
+---------------+--------+--------+-----------+--------+--------+--------+
| Peer          | Group  | AS     | Admin     | Session| Rcv    | Active |
|               |        |        | State     | State  | Routes | Routes |
+===============+========+========+===========+========+========+========+
| 10.1.2.2      |ebgp-pe | 65002  | enable    |establis| 4      | 4      |
|               |  ers   |        |           | hed    |        |        |
+---------------+--------+--------+-----------+--------+--------+--------+
| 10.1.3.2      |ebgp-pe | 65003  | enable    |active  | 0      | 0      |
|               |  ers   |        |           |        |        |        |
+---------------+--------+--------+-----------+--------+--------+--------+
```

The srl3 session (10.1.3.2) dropped to `active` state because the underlying interface went down and BGP keepalives stopped. The srl2 session now shows 4 received routes instead of 2 -- srl2 is advertising srl3's subnets because srl2 still peers with srl3 via the 10.1.6.0/24 link.

**Traceroute after convergence (traffic reroutes through srl2):**

```bash
$ docker exec clab-dynamic-routing-bgp-host1 traceroute -n -w 2 10.1.5.2
traceroute to 10.1.5.2 (10.1.5.2), 30 hops max, 60 byte packets
 1  10.1.1.1  1.234 ms  0.567 ms  0.432 ms
 2  10.1.2.2  1.456 ms  1.123 ms  0.987 ms
 3  10.1.6.2  1.678 ms  1.345 ms  1.234 ms
 4  10.1.5.2  2.123 ms  1.567 ms  1.456 ms
```

The path is now host1 -> srl1 (10.1.1.1) -> srl2 (10.1.2.2) -> srl3 (10.1.6.2) -> host3 (10.1.5.2). The traffic takes the longer triangle path because the direct srl1-srl3 link is down.

**What happened step by step:**

1. When ethernet-1/3 on srl1 was disabled, the srl1-srl3 BGP session lost its underlying transport.
2. After the BGP hold timer expired (~90 seconds by default), srl1 declared the session dead and withdrew the direct route to srl3's prefixes (10.1.3.0/24 and 10.1.5.0/24).
3. But srl1 still had an alternate path: srl2 peers with both srl1 (via 10.1.2.0/24) and srl3 (via 10.1.6.0/24). srl2 learned srl3's routes directly and re-advertised them to srl1 with AS path [65002, 65003].
4. srl1 installed this alternate path and traffic resumed through srl2.

**In lesson 03 exercise 6, disabling this same interface (ethernet-1/3 on srl1) permanently broke connectivity to host3.** The static route kept pointing at the dead link: the routing table said "send to 10.1.3.2 via ethernet-1/3" but ethernet-1/3 was down, so every packet to host3 was silently dropped. There was no mechanism to detect the failure or find an alternate path. Here, BGP detected the failure and automatically rerouted through the alternate path via srl2. This is the fundamental advantage of dynamic routing.

**Re-enable the link:**

```
A:srl1# enter candidate
set / interface ethernet-1/3 admin-state enable
commit now
```

**After re-enabling, BGP converges back to the direct path:**

```bash
$ docker exec clab-dynamic-routing-bgp-host1 traceroute -n -w 2 10.1.5.2
traceroute to 10.1.5.2 (10.1.5.2), 30 hops max, 60 byte packets
 1  10.1.1.1  1.234 ms  0.567 ms  0.432 ms
 2  10.1.3.2  1.345 ms  0.987 ms  0.876 ms
 3  10.1.5.2  1.567 ms  1.123 ms  1.012 ms
```

Traffic shifts back to the direct srl1 -> srl3 path because the direct route has a shorter AS path ([65003]) compared to the indirect route ([65002, 65003]).

**Key lesson:** Dynamic routing adapts to failures. The network healed itself. When the direct link went down, BGP found an alternate path through the triangle. When the link came back, BGP preferred the shorter path again. No human intervention was needed at any point.

---

## Exercise 6: Break/Fix -- Wrong ASN

**BGP neighbor table on srl2 showing `active` state:**

```
A:srl2# show network-instance default protocols bgp neighbor
+---------------+--------+--------+-----------+--------+--------+--------+
| Peer          | Group  | AS     | Admin     | Session| Rcv    | Active |
|               |        |        | State     | State  | Routes | Routes |
+===============+========+========+===========+========+========+========+
| 10.1.2.1      |ebgp-pe | 65099  | enable    |active  | 0      | 0      |
|               |  ers   |        |           |        |        |        |
+---------------+--------+--------+-----------+--------+--------+--------+
| 10.1.6.2      |ebgp-pe | 65003  | enable    |establis| 2      | 1      |
|               |  ers   |        |           | hed    |        |        |
+---------------+--------+--------+-----------+--------+--------+--------+
```

The srl1 session (10.1.2.1) shows `active` state and peer-as is 65099 (wrong). The srl3 session remains healthy.

**What `active` means:** The `active` state is confusing because it sounds like the session is working. In BGP, `active` means "actively trying to connect" -- it is actually a failure state. The state machine is stuck in a retry loop: srl2 opens a TCP connection to srl1, sends a BGP OPEN message claiming to expect peer-as 65099, but srl1 is AS 65001. srl1 checks: "This peer says I'm AS 65099, but I'm AS 65001." srl1 rejects the OPEN with a NOTIFICATION message (Bad Peer AS), tears down the TCP connection, and srl2 goes back to `active` to try again. This cycle repeats indefinitely.

`established` is the only healthy BGP state. Any other state -- `idle`, `connect`, `active`, `opensent`, `openconfirm` -- indicates a problem.

**Impact on traffic:** srl2 loses all routes learned from srl1. host2 can no longer reach host1 (10.1.1.0/24) or any subnet only reachable through srl1. However, host2 can still reach host3 because the srl2-srl3 BGP session (via 10.1.6.2) is unaffected.

```bash
$ docker exec clab-dynamic-routing-bgp-host2 ping -c 3 -W 5 10.1.1.2
PING 10.1.1.2 (10.1.1.2): 56 data bytes

--- 10.1.1.2 ping statistics ---
3 packets transmitted, 0 packets received, 100% packet loss

$ docker exec clab-dynamic-routing-bgp-host2 ping -c 3 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes
64 bytes from 10.1.5.2: seq=0 ttl=62 time=1.456 ms
64 bytes from 10.1.5.2: seq=1 ttl=62 time=0.987 ms
64 bytes from 10.1.5.2: seq=2 ttl=62 time=0.876 ms
--- 10.1.5.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

**Fix (restore the correct peer-as):**

```
A:srl2# enter candidate
set / network-instance default protocols bgp neighbor 10.1.2.1 peer-as 65001
commit now
```

**Verification:**

```bash
$ docker exec -it clab-dynamic-routing-bgp-srl2 sr_cli -c \
    "show network-instance default protocols bgp neighbor"
+---------------+--------+--------+-----------+--------+--------+--------+
| Peer          | Group  | AS     | Admin     | Session| Rcv    | Active |
|               |        |        | State     | State  | Routes | Routes |
+===============+========+========+===========+========+========+========+
| 10.1.2.1      |ebgp-pe | 65001  | enable    |establis| 3      | 3      |
|               |  ers   |        |           | hed    |        |        |
+---------------+--------+--------+-----------+--------+--------+--------+
| 10.1.6.2      |ebgp-pe | 65003  | enable    |establis| 2      | 1      |
|               |  ers   |        |           | hed    |        |        |
+---------------+--------+--------+-----------+--------+--------+--------+
```

```bash
$ docker exec clab-dynamic-routing-bgp-host2 ping -c 3 10.1.1.2
PING 10.1.1.2 (10.1.1.2): 56 data bytes
64 bytes from 10.1.1.2: seq=0 ttl=62 time=2.345 ms
64 bytes from 10.1.1.2: seq=1 ttl=62 time=1.123 ms
64 bytes from 10.1.1.2: seq=2 ttl=62 time=0.987 ms
--- 10.1.1.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

**Key lesson:** Both sides must agree on AS numbers. When debugging BGP, check session state first. If a session is stuck in `active` or `connect`, the most likely causes are: wrong peer-as, wrong peer-address, or a firewall blocking TCP port 179. The `active` state specifically suggests the TCP connection succeeds but the OPEN message is rejected -- which points to an AS number mismatch.

---

## Key Takeaways

1. **Dynamic routing replaces manual route management with automatic route exchange** -- routers learn about remote subnets from their BGP peers instead of relying on hand-configured static routes
2. **BGP sessions use explicit peering** -- you must configure both sides with matching AS numbers and reachable peer addresses before routes can flow
3. **Export policies control what gets advertised** -- SR Linux default-deny means no routes are shared without a policy; a session can be Established with zero routes exchanged
4. **BGP path selection prefers shorter AS paths** -- adding a direct link between two routers creates a shorter AS path that BGP automatically prefers, shifting traffic without manual intervention
5. **Dynamic routing self-heals** -- link failures trigger automatic rerouting through alternate paths; the same failure that permanently broke static routing in lesson 03 was automatically recovered here
6. **BGP session states matter** -- Established is the only healthy state; Active and Connect indicate configuration mismatches despite their misleading names
7. **Route type matters** -- static routes (administrative distance 5) beat BGP routes (170) on SR Linux; failing to remove static routes before enabling BGP will mask the dynamically learned routes
8. **gNMIc provides model-driven network configuration via gRPC** -- structured JSON payloads targeting YANG paths replace CLI text parsing, making network automation more reliable and programmatic
