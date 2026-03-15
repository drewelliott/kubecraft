# Lesson 3 Exercises: Routing Basics & Static Routes

Complete these exercises to build your routing and troubleshooting skills.

## Exercise 1: Deploy, Configure, and Verify End-to-End

**Objective:** Deploy the hub-and-spoke topology, apply Ansible configuration, and verify full connectivity.

### Steps

1. Deploy the topology:
   ```bash
   cd lessons/clab/03-routing-basics
   containerlab deploy -t topology/lab.clab.yml
   ```

2. Wait for SR Linux to initialize (about 30 seconds), then apply config:
   ```bash
   cd ansible
   ansible-playbook -i inventory.yml playbook.yml
   ```

3. Verify host-to-router connectivity (same subnet):
   ```bash
   docker exec clab-routing-basics-host1 ping -c 3 10.1.1.1
   docker exec clab-routing-basics-host2 ping -c 3 10.1.4.1
   docker exec clab-routing-basics-host3 ping -c 3 10.1.5.1
   ```

4. Verify end-to-end cross-subnet connectivity (this is the lesson 02 cliffhanger payoff):
   ```bash
   docker exec clab-routing-basics-host1 ping -c 3 10.1.4.2
   docker exec clab-routing-basics-host1 ping -c 3 10.1.5.2
   docker exec clab-routing-basics-host2 ping -c 3 10.1.5.2
   ```

5. Check the routing table on srl1:
   ```bash
   docker exec -it clab-routing-basics-srl1 sr_cli -c "show network-instance default route-table ipv4-unicast summary"
   ```

### Deliverables

- Which pings succeeded (all should work now -- unlike lesson 02)
- Routing table output from srl1 showing both directly connected and static routes

---

## Exercise 2: Read the Routing Table

**Objective:** Understand routing table entries and trace a packet's path hop by hop.

### Steps

1. Examine the routing table on all 3 routers:
   ```bash
   docker exec -it clab-routing-basics-srl1 sr_cli -c "show network-instance default route-table ipv4-unicast summary"
   docker exec -it clab-routing-basics-srl2 sr_cli -c "show network-instance default route-table ipv4-unicast summary"
   docker exec -it clab-routing-basics-srl3 sr_cli -c "show network-instance default route-table ipv4-unicast summary"
   ```

2. For each router, identify:
   - Which routes are "directly connected" (local)
   - Which routes are "static"

3. Trace the path of a packet from host2 (10.1.4.2) to host3 (10.1.5.2):
   - Step 1: host2 sends to its default gateway (10.1.4.1 = srl2)
   - Step 2: srl2 looks up 10.1.5.0/24 in its routing table -- what does it find?
   - Step 3: The packet arrives at srl1 -- what route does srl1 use for 10.1.5.0/24?
   - Step 4: The packet arrives at srl3 -- how does it reach host3?

4. Now trace the RETURN path (host3 -> host2):
   - What route does srl3 use to reach 10.1.4.0/24?

### Deliverables

- Routing table screenshots from all 3 routers
- Written hop-by-hop trace for host2 -> host3 AND the return path

---

## Exercise 3: Break/Fix -- Missing Route

**Objective:** Understand what happens when a router is missing a route and why both directions can break even when only one router is affected.

### Setup (break it)

```bash
docker exec -it clab-routing-basics-srl2 sr_cli
```

Inside SR Linux:
```
enter candidate
delete / network-instance default static-routes route 10.1.5.0/24
delete / network-instance default next-hop-groups group nhg-10-1-5-0-24
commit now
exit
```

### Symptom

```bash
# This FAILS -- host2 cannot reach host3
docker exec clab-routing-basics-host2 ping -c 3 -W 5 10.1.5.2

# This ALSO FAILS -- host3 cannot reach host2 (why?)
docker exec clab-routing-basics-host3 ping -c 3 -W 5 10.1.4.2

# But this WORKS -- host1 can still reach host3
docker exec clab-routing-basics-host1 ping -c 3 10.1.5.2
```

### Your Task

1. Check srl2's routing table -- what's missing?
   ```bash
   docker exec -it clab-routing-basics-srl2 sr_cli -c "show network-instance default route-table ipv4-unicast summary"
   ```

2. Explain why both host2->host3 AND host3->host2 fail, even though only srl2 is missing a route (hint: trace both the forward path and the return path for each ping).

3. Fix by re-adding the route:
   ```bash
   docker exec -it clab-routing-basics-srl2 sr_cli
   ```
   Inside SR Linux:
   ```
   enter candidate
   set / network-instance default next-hop-groups group nhg-10-1-5-0-24 admin-state enable
   set / network-instance default next-hop-groups group nhg-10-1-5-0-24 nexthop 1 ip-address 10.1.2.1
   set / network-instance default static-routes route 10.1.5.0/24 admin-state enable
   set / network-instance default static-routes route 10.1.5.0/24 next-hop-group nhg-10-1-5-0-24
   commit now
   exit
   ```

4. Verify the fix:
   ```bash
   docker exec clab-routing-basics-host2 ping -c 3 10.1.5.2
   ```

### Deliverables

- Explanation of why the missing route breaks both directions (forward path vs return path)
- The diagnostic commands you used

---

## Exercise 4: Break/Fix -- Wrong Next-Hop (Black Hole)

**Objective:** Understand what happens when a static route points to a non-existent next-hop.

### Setup (break it)

```bash
docker exec -it clab-routing-basics-srl1 sr_cli
```

Inside SR Linux:
```
enter candidate
set / network-instance default next-hop-groups group nhg-10-1-5-0-24 nexthop 1 ip-address 10.1.3.99
commit now
exit
```

### Symptom

```bash
# host1 cannot reach host3
docker exec clab-routing-basics-host1 ping -c 3 -W 5 10.1.5.2
```

### Your Task

1. Check srl1's routing table -- does the route exist?
   ```bash
   docker exec -it clab-routing-basics-srl1 sr_cli -c "show network-instance default route-table ipv4-unicast summary"
   ```

2. The route exists but points to 10.1.3.99. Check the ARP table:
   ```bash
   docker exec -it clab-routing-basics-srl1 sr_cli -c "show arpnd arp-entries"
   ```

3. Explain why a valid-looking route can still black-hole traffic.

4. Fix by restoring the correct next-hop:
   ```bash
   docker exec -it clab-routing-basics-srl1 sr_cli
   ```
   Inside SR Linux:
   ```
   enter candidate
   set / network-instance default next-hop-groups group nhg-10-1-5-0-24 nexthop 1 ip-address 10.1.3.2
   commit now
   exit
   ```

5. Verify:
   ```bash
   docker exec clab-routing-basics-host1 ping -c 3 10.1.5.2
   ```

### Deliverables

- Explanation of black hole routing
- ARP output showing failed resolution for 10.1.3.99

---

## Exercise 5: Break/Fix -- Routing Loop

**Objective:** Observe what happens when two routers send traffic back and forth in a loop, and understand how TTL prevents infinite loops.

### Setup (break it)

```bash
docker exec -it clab-routing-basics-srl1 sr_cli
```

Inside SR Linux:
```
enter candidate
set / network-instance default next-hop-groups group nhg-10-1-5-0-24 nexthop 1 ip-address 10.1.2.2
commit now
exit
```

Now srl1 sends 10.1.5.0/24 traffic to srl2, and srl2 sends it back to srl1 (via its existing route through the hub).

### Symptom

```bash
# Ping fails
docker exec clab-routing-basics-host1 ping -c 3 -W 10 10.1.5.2

# Traceroute reveals the loop
docker exec clab-routing-basics-host1 traceroute -n -w 2 10.1.5.2
```

### Your Task

1. Run traceroute and observe the alternating hops between srl1 and srl2.

2. Explain: What is TTL? Why does the packet eventually stop?

3. Fix by restoring srl1's correct next-hop:
   ```bash
   docker exec -it clab-routing-basics-srl1 sr_cli
   ```
   Inside SR Linux:
   ```
   enter candidate
   set / network-instance default next-hop-groups group nhg-10-1-5-0-24 nexthop 1 ip-address 10.1.3.2
   commit now
   exit
   ```

4. Verify:
   ```bash
   docker exec clab-routing-basics-host1 ping -c 3 10.1.5.2
   ```

### Deliverables

- Traceroute output showing the routing loop pattern
- Explanation of TTL and how it prevents infinite loops

---

## Exercise 6: Break/Fix -- Unreachable Next-Hop (Link Down)

**Objective:** Understand that a route can exist in the routing table even when the physical path is broken.

### Setup (break it)

```bash
docker exec -it clab-routing-basics-srl1 sr_cli
```

Inside SR Linux:
```
enter candidate
set / interface ethernet-1/3 admin-state disable
commit now
exit
```

### Symptom

```bash
# host1 cannot reach host3
docker exec clab-routing-basics-host1 ping -c 3 -W 5 10.1.5.2
```

### Your Task

1. Check interface status on srl1:
   ```bash
   docker exec -it clab-routing-basics-srl1 sr_cli -c "show interface brief"
   ```

2. Notice ethernet-1/3 is admin-disabled. The route to 10.1.5.0/24 may still exist but the next-hop is unreachable.

3. Explain: Why can a route exist even when the link is down?

4. Fix by re-enabling the interface:
   ```bash
   docker exec -it clab-routing-basics-srl1 sr_cli
   ```
   Inside SR Linux:
   ```
   enter candidate
   set / interface ethernet-1/3 admin-state enable
   commit now
   exit
   ```

5. Verify:
   ```bash
   docker exec clab-routing-basics-host1 ping -c 3 10.1.5.2
   ```

### Deliverables

- Interface status output showing the disabled link
- Explanation of why route existence does not guarantee path availability

---

## Cleanup

After completing all exercises:

```bash
# Destroy the lab
containerlab destroy -t topology/lab.clab.yml --cleanup

# Verify
docker ps | grep clab
```

## Validation

Run the automated tests:

```bash
pytest tests/ -v
```

## Completion Checklist

- [ ] Exercise 1: Deployed lab, applied Ansible config, verified end-to-end connectivity
- [ ] Exercise 2: Read routing tables, traced packet path hop by hop
- [ ] Exercise 3: Diagnosed and fixed missing route (return path analysis)
- [ ] Exercise 4: Diagnosed and fixed wrong next-hop (black hole)
- [ ] Exercise 5: Diagnosed and fixed routing loop (TTL)
- [ ] Exercise 6: Diagnosed and fixed unreachable next-hop (link down)

## Next Steps

Commit your exercises to your fork and proceed to Lesson 4 (coming soon).
