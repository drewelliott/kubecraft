# Lesson 3 Solutions

Reference solutions for the Routing Basics exercises.

## Exercise 1: Deploy, Configure, and Verify End-to-End

**Adjacent pings (all succeed):**

```bash
$ docker exec clab-routing-basics-host1 ping -c 3 10.1.1.1
PING 10.1.1.1 (10.1.1.1): 56 data bytes
64 bytes from 10.1.1.1: seq=0 ttl=64 time=1.234 ms
64 bytes from 10.1.1.1: seq=1 ttl=64 time=0.567 ms
64 bytes from 10.1.1.1: seq=2 ttl=64 time=0.432 ms
--- 10.1.1.1 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

```bash
$ docker exec clab-routing-basics-host2 ping -c 3 10.1.4.1
PING 10.1.4.1 (10.1.4.1): 56 data bytes
64 bytes from 10.1.4.1: seq=0 ttl=64 time=1.123 ms
64 bytes from 10.1.4.1: seq=1 ttl=64 time=0.456 ms
64 bytes from 10.1.4.1: seq=2 ttl=64 time=0.389 ms
--- 10.1.4.1 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

```bash
$ docker exec clab-routing-basics-host3 ping -c 3 10.1.5.1
PING 10.1.5.1 (10.1.5.1): 56 data bytes
64 bytes from 10.1.5.1: seq=0 ttl=64 time=1.098 ms
64 bytes from 10.1.5.1: seq=1 ttl=64 time=0.512 ms
64 bytes from 10.1.5.1: seq=2 ttl=64 time=0.401 ms
--- 10.1.5.1 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

All adjacent pings succeed because each host is on the same subnet as its directly connected router interface.

**Cross-subnet pings (all succeed -- the lesson 02 cliffhanger is resolved):**

```bash
$ docker exec clab-routing-basics-host1 ping -c 3 10.1.4.2
PING 10.1.4.2 (10.1.4.2): 56 data bytes
64 bytes from 10.1.4.2: seq=0 ttl=62 time=2.345 ms
64 bytes from 10.1.4.2: seq=1 ttl=62 time=1.123 ms
64 bytes from 10.1.4.2: seq=2 ttl=62 time=0.987 ms
--- 10.1.4.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

```bash
$ docker exec clab-routing-basics-host1 ping -c 3 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes
64 bytes from 10.1.5.2: seq=0 ttl=62 time=2.456 ms
64 bytes from 10.1.5.2: seq=1 ttl=62 time=1.234 ms
64 bytes from 10.1.5.2: seq=2 ttl=62 time=1.012 ms
--- 10.1.5.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

```bash
$ docker exec clab-routing-basics-host2 ping -c 3 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes
64 bytes from 10.1.5.2: seq=0 ttl=61 time=3.456 ms
64 bytes from 10.1.5.2: seq=1 ttl=61 time=2.123 ms
64 bytes from 10.1.5.2: seq=2 ttl=61 time=1.876 ms
--- 10.1.5.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

Notice the TTL values. host1 to host2 shows TTL=62: each router hop decrements TTL by 1, and the path host1 -> srl1 -> srl2 -> host2 crosses 2 routers, so TTL drops from 64 to 62. host2 to host3 shows TTL=61: the path host2 -> srl2 -> srl1 -> srl3 -> host3 crosses 3 routers (through the hub), so TTL drops from 64 to 61.

**Routing table on srl1:**

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

srl1 (the hub) has 3 directly connected routes (type `local`) for the subnets on its physical interfaces, plus 2 static routes pointing to the spoke routers as next-hops. The static route for 10.1.4.0/24 points to srl2 (10.1.2.2) and the static route for 10.1.5.0/24 points to srl3 (10.1.3.2). This is what was missing in lesson 02 -- without these static routes, the hub had no idea where to forward cross-subnet traffic.

---

## Exercise 2: Read the Routing Table

**srl2's routing table:**

```
A:srl2# show network-instance default route-table ipv4-unicast summary
+------------+-------+------------+-------------------+----------+
|   Prefix   | Type  | Route-Owner| Next-hop          | Metric   |
+============+=======+============+===================+==========+
| 10.1.1.0/24| static| static     | 10.1.2.1          | 1        |
| 10.1.2.0/24| local | net_inst   | ethernet-1/1.0    | 0        |
| 10.1.3.0/24| static| static     | 10.1.2.1          | 1        |
| 10.1.4.0/24| local | net_inst   | ethernet-1/2.0    | 0        |
| 10.1.5.0/24| static| static     | 10.1.2.1          | 1        |
+------------+-------+------------+-------------------+----------+
```

srl2 has 2 local routes (its directly connected subnets) and 3 static routes. All static routes point to 10.1.2.1 (srl1) because in a hub-and-spoke topology, the spoke sends everything it does not know about through the hub.

**srl3's routing table:**

```
A:srl3# show network-instance default route-table ipv4-unicast summary
+------------+-------+------------+-------------------+----------+
|   Prefix   | Type  | Route-Owner| Next-hop          | Metric   |
+============+=======+============+===================+==========+
| 10.1.1.0/24| static| static     | 10.1.3.1          | 1        |
| 10.1.2.0/24| static| static     | 10.1.3.1          | 1        |
| 10.1.3.0/24| local | net_inst   | ethernet-1/1.0    | 0        |
| 10.1.4.0/24| static| static     | 10.1.3.1          | 1        |
| 10.1.5.0/24| local | net_inst   | ethernet-1/2.0    | 0        |
+------------+-------+------------+-------------------+----------+
```

srl3 mirrors the same pattern: 2 local routes and 3 static routes, all pointing to srl1 (10.1.3.1) as the hub.

**Hop-by-hop trace: host2 (10.1.4.2) -> host3 (10.1.5.2):**

1. **host2** has a default route via 10.1.4.1 (srl2). Since 10.1.5.2 is not on host2's local subnet (10.1.4.0/24), the packet is sent to the default gateway.

2. **srl2** receives the packet and looks up 10.1.5.0/24 in its routing table. It finds a static route with next-hop 10.1.2.1 (srl1). srl2 forwards the packet to srl1 via the 10.1.2.0/24 link.

3. **srl1** receives the packet and looks up 10.1.5.0/24 in its routing table. It finds a static route with next-hop 10.1.3.2 (srl3). srl1 forwards the packet to srl3 via the 10.1.3.0/24 link.

4. **srl3** receives the packet and looks up 10.1.5.0/24. This is a directly connected subnet (local route via ethernet-1/2.0). srl3 delivers the packet to host3 on the local link.

**Return path (host3 -> host2):**

1. **host3** sends the reply to its default gateway 10.1.5.1 (srl3).
2. **srl3** looks up 10.1.4.0/24 in its routing table and finds a static route via 10.1.3.1 (srl1). The reply goes back to the hub.
3. **srl1** looks up 10.1.4.0/24 and finds a static route via 10.1.2.2 (srl2). The reply continues toward srl2.
4. **srl2** has 10.1.4.0/24 as a directly connected subnet, so it delivers the reply to host2.

The return path mirrors the forward path through the hub. Every hop makes an independent routing decision based solely on its own routing table. This is a fundamental principle: routers do not remember the path a packet came from. Each router only knows the destination address and consults its own table to decide the next hop.

---

## Exercise 3: Break/Fix -- Missing Route (Return Path Analysis)

**srl2's routing table after deleting the route:**

```
A:srl2# show network-instance default route-table ipv4-unicast summary
+------------+-------+------------+-------------------+----------+
|   Prefix   | Type  | Route-Owner| Next-hop          | Metric   |
+============+=======+============+===================+==========+
| 10.1.1.0/24| static| static     | 10.1.2.1          | 1        |
| 10.1.2.0/24| local | net_inst   | ethernet-1/1.0    | 0        |
| 10.1.3.0/24| static| static     | 10.1.2.1          | 1        |
| 10.1.4.0/24| local | net_inst   | ethernet-1/2.0    | 0        |
+------------+-------+------------+-------------------+----------+
```

The 10.1.5.0/24 route is gone from srl2's table.

**Why host2 -> host3 fails:**

host2 sends the packet to its default gateway (srl2). srl2 looks up 10.1.5.0/24 and has no matching route. srl2 drops the packet. The ICMP echo request never leaves srl2.

**Why host3 -> host2 also fails:**

This is a subtle but important point. Let's trace both the forward path and the return path:

- **Forward (echo request):** host3 -> srl3 -> srl1 -> srl2 -> host2. This path works because srl3 and srl1 both have valid routes, and srl2 has 10.1.4.0/24 directly connected. The ICMP echo request arrives at host2.
- **Return (echo reply):** host2 -> srl2. host2 sends the reply to its default gateway (srl2). The reply is destined for 10.1.5.2 (host3). srl2 looks up 10.1.5.0/24 -- but that route was deleted. srl2 drops the reply.

The echo request reaches host2, but the echo reply cannot get back. Ping reports 100% packet loss in both directions because ping requires a complete round trip. This demonstrates why routing must work in both directions -- a packet reaching its destination is only half the story.

**What still works:**

host1 and host3 can still ping each other. The path host1 -> srl1 -> srl3 -> host3 (and the return path host3 -> srl3 -> srl1 -> host1) does not involve srl2 at all. The missing route on srl2 only affects paths that traverse srl2.

**Fix (re-add the route):**

```
A:srl2# enter candidate
set / network-instance default next-hop-groups group nhg-10-1-5-0-24 admin-state enable
set / network-instance default next-hop-groups group nhg-10-1-5-0-24 nexthop 1 ip-address 10.1.2.1
set / network-instance default static-routes route 10.1.5.0/24 admin-state enable
set / network-instance default static-routes route 10.1.5.0/24 next-hop-group nhg-10-1-5-0-24
commit now
```

**Verification:**

```bash
$ docker exec clab-routing-basics-host2 ping -c 3 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes
64 bytes from 10.1.5.2: seq=0 ttl=61 time=3.456 ms
64 bytes from 10.1.5.2: seq=1 ttl=61 time=2.123 ms
64 bytes from 10.1.5.2: seq=2 ttl=61 time=1.876 ms
--- 10.1.5.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

**Key lesson:** A missing route on any router in the path (including the return path) breaks connectivity. The failure is not always obvious -- the forward direction might work fine while the return silently fails. Always trace both directions when debugging.

---

## Exercise 4: Break/Fix -- Wrong Next-Hop (Black Hole)

**srl1's routing table after the change:**

```
A:srl1# show network-instance default route-table ipv4-unicast summary
+------------+-------+------------+-------------------+----------+
|   Prefix   | Type  | Route-Owner| Next-hop          | Metric   |
+============+=======+============+===================+==========+
| 10.1.1.0/24| local | net_inst   | ethernet-1/1.0    | 0        |
| 10.1.2.0/24| local | net_inst   | ethernet-1/2.0    | 0        |
| 10.1.3.0/24| local | net_inst   | ethernet-1/3.0    | 0        |
| 10.1.4.0/24| static| static     | 10.1.2.2          | 1        |
| 10.1.5.0/24| static| static     | 10.1.3.99         | 1        |
+------------+-------+------------+-------------------+----------+
```

The route to 10.1.5.0/24 exists and looks valid at first glance. But the next-hop is 10.1.3.99, which is not a real device on the 10.1.3.0/24 link.

**ARP table on srl1:**

```
A:srl1# show arpnd arp-entries
+-----------+-----------+-----------+-----------+
| Interface | IP Addr   | MAC       | State     |
+===========+===========+===========+===========+
| e1-1.0    | 10.1.1.2  | aa:c1:... | reachable |
| e1-2.0    | 10.1.2.2  | aa:c1:... | reachable |
| e1-3.0    | 10.1.3.2  | aa:c1:... | reachable |
| e1-3.0    | 10.1.3.99 |           | incomplete|
+-----------+-----------+-----------+-----------+
```

The ARP entry for 10.1.3.99 shows `incomplete` -- srl1 sent ARP requests asking "who has 10.1.3.99?" but nobody answered. Without a MAC address, srl1 cannot encapsulate the packet in a Layer 2 frame, so the packet is silently dropped.

**Why this is called a "black hole":** The routing table says the route is valid. The router faithfully looks up the destination, finds a next-hop, and tries to forward. But the next-hop does not exist at Layer 2. The packet vanishes into the void with no error message sent back to the sender (ARP failures are silent). From the sender's perspective, it looks identical to a network timeout.

**Fix (restore the correct next-hop):**

```
A:srl1# enter candidate
set / network-instance default next-hop-groups group nhg-10-1-5-0-24 nexthop 1 ip-address 10.1.3.2
commit now
```

**Verification:**

```bash
$ docker exec clab-routing-basics-host1 ping -c 3 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes
64 bytes from 10.1.5.2: seq=0 ttl=62 time=2.345 ms
64 bytes from 10.1.5.2: seq=1 ttl=62 time=1.123 ms
64 bytes from 10.1.5.2: seq=2 ttl=62 time=0.987 ms
--- 10.1.5.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

**Key lesson:** A routing table entry is just data -- the router trusts it completely. If the data is wrong, traffic disappears into a black hole. The routing table says the route is valid, but the forwarding plane cannot deliver. Always verify that next-hops are reachable at Layer 2, not just that routes exist in the table.

---

## Exercise 5: Break/Fix -- Routing Loop

**Traceroute output:**

```bash
$ docker exec clab-routing-basics-host1 traceroute -n -w 2 10.1.5.2
traceroute to 10.1.5.2 (10.1.5.2), 30 hops max, 60 byte packets
 1  10.1.1.1  1.234 ms  0.567 ms  0.432 ms
 2  10.1.2.2  1.345 ms  1.123 ms  0.987 ms
 3  10.1.2.1  1.456 ms  1.234 ms  1.123 ms
 4  10.1.2.2  1.567 ms  1.345 ms  1.234 ms
 5  10.1.2.1  1.678 ms  1.456 ms  1.345 ms
 6  10.1.2.2  1.789 ms  1.567 ms  1.456 ms
 7  10.1.2.1  1.890 ms  1.678 ms  1.567 ms
...
30  * * *
```

The packet bounces between srl1 (10.1.2.1) and srl2 (10.1.2.2) endlessly:

1. host1 sends the packet to srl1 (its default gateway).
2. srl1 looks up 10.1.5.0/24 and finds next-hop 10.1.2.2 (srl2). Forwards to srl2.
3. srl2 looks up 10.1.5.0/24 and finds next-hop 10.1.2.1 (srl1). Forwards back to srl1.
4. srl1 looks up 10.1.5.0/24 and finds next-hop 10.1.2.2 (srl2). Forwards to srl2 again.
5. The loop continues indefinitely.

**TTL (Time To Live):** Every IP packet carries a TTL field (set to 64 by default on Linux). Each router that forwards the packet decrements the TTL by 1. When the TTL reaches 0, the router drops the packet and sends an ICMP "Time Exceeded" message back to the sender. This is what prevents routing loops from consuming network resources forever. Without TTL, a looping packet would circulate until the link saturated.

Traceroute exploits this mechanism: it sends packets with incrementally increasing TTL values (1, 2, 3, ...) to discover each hop along the path. This is why traceroute can reveal a routing loop -- you see the same two IP addresses alternating at every hop.

**Fix (restore srl1's correct next-hop):**

```
A:srl1# enter candidate
set / network-instance default next-hop-groups group nhg-10-1-5-0-24 nexthop 1 ip-address 10.1.3.2
commit now
```

**Verification:**

```bash
$ docker exec clab-routing-basics-host1 ping -c 3 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes
64 bytes from 10.1.5.2: seq=0 ttl=62 time=2.345 ms
64 bytes from 10.1.5.2: seq=1 ttl=62 time=1.123 ms
64 bytes from 10.1.5.2: seq=2 ttl=62 time=0.987 ms
--- 10.1.5.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

**Key lesson:** A routing loop occurs when two or more routers point at each other for the same destination. The packet bounces back and forth until TTL expires. Traceroute is the best diagnostic tool for detecting loops because it reveals the actual forwarding path.

---

## Exercise 6: Break/Fix -- Unreachable Next-Hop (Link Down)

**Interface status on srl1:**

```
A:srl1# show interface brief
+---------------------+----------+----------+-------+----------+
|      Interface      |  Admin   |  Oper    | Speed |   Type   |
+=====================+==========+==========+=======+==========+
| ethernet-1/1        | enable   | up       | 25G   | ethernet |
| ethernet-1/2        | enable   | up       | 25G   | ethernet |
| ethernet-1/3        | disable  | down     |       |          |
+---------------------+----------+----------+-------+----------+
```

ethernet-1/3 (the srl1-to-srl3 link) is admin-disabled. The `Admin` column shows `disable` and the `Oper` state is `down`.

srl1's routing table may still show the static route to 10.1.5.0/24 via 10.1.3.2 -- but ethernet-1/3 is the interface needed to reach that next-hop. With the interface down, srl1 cannot forward the packet even though the routing table says it should.

**Why this differs from the black hole (Exercise 4):** In Exercise 4, the interface was up but the next-hop IP did not exist (ARP failed). Here, the next-hop IP is correct (10.1.3.2 is srl3), but the physical link to reach it is down. Both result in dropped packets, but the root cause is different: one is a data-plane issue (wrong IP), the other is a physical-layer issue (link down).

**Why the static route persists:** Static routes are manually configured entries. The router does not automatically remove them when a link goes down. Dynamic routing protocols like BGP or OSPF would detect the link failure and withdraw the route from the table, but static routes are "dumb" -- they stay in the table regardless of link state.

**Fix (re-enable the interface):**

```
A:srl1# enter candidate
set / interface ethernet-1/3 admin-state enable
commit now
```

**Verification:**

```bash
$ docker exec clab-routing-basics-host1 ping -c 3 10.1.5.2
PING 10.1.5.2 (10.1.5.2): 56 data bytes
64 bytes from 10.1.5.2: seq=0 ttl=62 time=2.345 ms
64 bytes from 10.1.5.2: seq=1 ttl=62 time=1.123 ms
64 bytes from 10.1.5.2: seq=2 ttl=62 time=0.987 ms
--- 10.1.5.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

**Key lesson:** A route in the routing table is a forwarding instruction, not a guarantee. The route says "send to 10.1.3.2 via ethernet-1/3" but if ethernet-1/3 is down, the instruction cannot be executed. Route existence does not equal path availability. This is a major limitation of static routes compared to dynamic routing protocols, which automatically adapt to topology changes.

---

## Key Takeaways

1. **Routing tables are per-hop** -- each router makes an independent forwarding decision based only on its own table
2. **Both directions must work** -- a packet reaching its destination is only half the story; the reply must find its way back through every router in the return path
3. **Static routes are trusted blindly** -- the router forwards based on what the table says, even if the data is wrong (black hole, loop, or down link)
4. **TTL prevents infinite loops** -- without TTL, a routing loop would circulate packets forever, consuming bandwidth and processing power
5. **Route existence does not equal path availability** -- a route can point to a valid-looking next-hop even when the physical link is down or the next-hop IP does not exist
6. **Hub-and-spoke concentrates risk** -- all spoke-to-spoke traffic flows through the hub; a missing route on any router in the path (including for the return traffic) breaks connectivity
7. **Automation prevents misconfiguration** -- using Ansible templates to generate routes from data reduces the chance of typos and inconsistencies that lead to black holes and loops
8. **Traceroute is your best friend** -- it reveals the actual path packets take, making loops and black holes visible when ping alone just shows "timeout"
