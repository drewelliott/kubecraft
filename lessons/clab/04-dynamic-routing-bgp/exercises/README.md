# Lesson 4 Exercises: Dynamic Routing with BGP

Complete these exercises to understand how BGP replaces static routes with dynamic, self-healing routing.

## Exercise 1: Deploy and Configure eBGP

**Objective:** Deploy the topology, observe that routers have no routes beyond their directly connected subnets, then configure eBGP to restore full connectivity.

### Steps

1. Deploy the topology:
   ```bash
   cd lessons/clab/04-dynamic-routing-bgp
   containerlab deploy -t topology/lab.clab.yml
   ```

2. Install gNMIc if needed:
   ```bash
   brew install gnmic
   ```

3. Verify cross-subnet pings FAIL -- routers only know their directly connected subnets:
   ```bash
   docker exec clab-dynamic-routing-bgp-host1 ping -c 2 -W 3 10.1.4.2
   docker exec clab-dynamic-routing-bgp-host1 ping -c 2 -W 3 10.1.5.2
   ```

4. Check the routing table on srl1 -- only `local` routes for directly connected interfaces:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl1 sr_cli -c "show network-instance default route-table ipv4-unicast summary"
   ```

5. Examine the pre-wired but unconfigured srl2-srl3 link:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl2 sr_cli -c "show interface ethernet-1/3"
   ```

6. Apply BGP config using gNMIc:
   ```bash
   cd gnmic
   gnmic -a clab-dynamic-routing-bgp-srl1:57400 -u admin -p NokiaSrl1! \
     --skip-verify -e json_ietf set --request-file configs/srl1-bgp.json
   gnmic -a clab-dynamic-routing-bgp-srl2:57400 -u admin -p NokiaSrl1! \
     --skip-verify -e json_ietf set --request-file configs/srl2-bgp.json
   gnmic -a clab-dynamic-routing-bgp-srl3:57400 -u admin -p NokiaSrl1! \
     --skip-verify -e json_ietf set --request-file configs/srl3-bgp.json
   ```

7. Verify BGP sessions are established:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl1 sr_cli -c "show network-instance default protocols bgp neighbor"
   ```

8. Verify cross-subnet pings now work:
   ```bash
   docker exec clab-dynamic-routing-bgp-host1 ping -c 3 10.1.4.2
   docker exec clab-dynamic-routing-bgp-host1 ping -c 3 10.1.5.2
   docker exec clab-dynamic-routing-bgp-host2 ping -c 3 10.1.5.2
   ```

9. Check the routing table -- remote subnets now show as `bgp`:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl1 sr_cli -c "show network-instance default route-table ipv4-unicast summary"
   ```

### Deliverables

- Routing table before BGP (only local routes) and after (local + bgp routes)
- All cross-subnet pings succeeding

---

## Exercise 2: Enable the Direct Link and Observe Path Selection

**Objective:** Enable the pre-wired srl2-srl3 link and observe BGP selecting the shorter AS path.

### Steps

1. Traceroute BEFORE the new link -- host2 to host3 goes through the hub (3 router hops):
   ```bash
   docker exec clab-dynamic-routing-bgp-host2 traceroute -n -w 2 10.1.5.2
   ```
   Expected: 10.1.4.1 (srl2) -> 10.1.2.1 (srl1) -> 10.1.3.2... -> 10.1.5.2

2. Configure the srl2-srl3 interfaces:
   ```bash
   gnmic -a clab-dynamic-routing-bgp-srl2:57400 -u admin -p NokiaSrl1! \
     --skip-verify -e json_ietf set --request-file configs/srl2-new-link.json
   gnmic -a clab-dynamic-routing-bgp-srl3:57400 -u admin -p NokiaSrl1! \
     --skip-verify -e json_ietf set --request-file configs/srl3-new-link.json
   ```

3. Add BGP neighbors for the new link:
   ```bash
   gnmic -a clab-dynamic-routing-bgp-srl2:57400 -u admin -p NokiaSrl1! \
     --skip-verify -e json_ietf set --request-file configs/srl2-bgp-srl3.json
   gnmic -a clab-dynamic-routing-bgp-srl3:57400 -u admin -p NokiaSrl1! \
     --skip-verify -e json_ietf set --request-file configs/srl3-bgp-srl2.json
   ```

4. Verify the new BGP session is established:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl2 sr_cli -c "show network-instance default protocols bgp neighbor"
   ```

5. Traceroute AFTER -- host2 to host3 now goes direct (2 router hops):
   ```bash
   docker exec clab-dynamic-routing-bgp-host2 traceroute -n -w 2 10.1.5.2
   ```
   Expected: 10.1.4.1 (srl2) -> 10.1.6.2 (srl3) -> 10.1.5.2

6. Check received routes on srl2 to see the AS path difference:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl2 sr_cli -c "show network-instance default protocols bgp routes ipv4 summary"
   ```

Note: In lesson 03, adding a cable accomplished nothing without adding static routes. With BGP, adding a cable and a peering session changes the forwarding path within seconds.

### Deliverables

- Before/after traceroute output
- Explanation of AS path selection

---

## Exercise 3: Break/Fix -- Missing Export Policy

**Objective:** Understand that a BGP session being Established does not mean routes are flowing.

### Setup (break it)

```bash
docker exec -it clab-dynamic-routing-bgp-srl3 sr_cli
```

Inside SR Linux:
```
enter candidate
delete / network-instance default protocols bgp group ebgp-peers export-policy
commit now
exit
```

### Symptom

```bash
# host1 and host2 CANNOT reach host3
docker exec clab-dynamic-routing-bgp-host1 ping -c 3 -W 5 10.1.5.2
docker exec clab-dynamic-routing-bgp-host2 ping -c 3 -W 5 10.1.5.2

# But host3 CAN still reach host1 and host2 (it still receives routes)
docker exec clab-dynamic-routing-bgp-host3 ping -c 3 10.1.1.2
```

### Your Task

1. Check BGP neighbor detail on srl3:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl3 sr_cli -c "show network-instance default protocols bgp neighbor 10.1.3.1 detail"
   ```

2. Look at received vs sent route counts. srl3 receives routes (it can reach out) but sends 0 (nobody can reach it).

3. Fix by re-adding the export policy:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl3 sr_cli
   ```
   Inside SR Linux:
   ```
   enter candidate
   set / network-instance default protocols bgp group ebgp-peers export-policy [export-connected]
   commit now
   exit
   ```

4. Verify:
   ```bash
   docker exec clab-dynamic-routing-bgp-host1 ping -c 3 10.1.5.2
   ```

### Deliverables

- BGP neighbor detail showing sent-routes=0
- Explanation of SR Linux default-deny export behavior

---

## Exercise 4: Break/Fix -- Link Failure with Automatic Reroute

**Objective:** Observe dynamic routing self-healing -- the same break from lesson 03 exercise 6 that was permanent now fixes itself.

### Setup (break it)

```bash
docker exec -it clab-dynamic-routing-bgp-srl1 sr_cli
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
# Brief connectivity loss to host3, then recovery
# Run continuous ping to watch:
docker exec clab-dynamic-routing-bgp-host1 ping -c 30 -i 1 10.1.5.2
```

### Your Task

1. While the continuous ping is running, watch for packet loss then recovery.

2. Check srl1's BGP neighbors -- the srl3 session should drop:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl1 sr_cli -c "show network-instance default protocols bgp neighbor"
   ```

3. Traceroute to see the new path (traffic now goes srl1 -> srl2 -> srl3 instead of direct):
   ```bash
   docker exec clab-dynamic-routing-bgp-host1 traceroute -n -w 2 10.1.5.2
   ```

4. Re-enable the link:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl1 sr_cli
   ```
   Inside SR Linux:
   ```
   enter candidate
   set / interface ethernet-1/3 admin-state enable
   commit now
   exit
   ```

5. Watch the BGP session come back up and traffic shift back to the direct path.

Callback: In lesson 03, disabling this same link permanently broke connectivity to host3. Now with BGP, the network found an alternate path automatically.

### Deliverables

- Ping output showing loss then recovery
- Before/after traceroute
- Explanation of BGP convergence

---

## Exercise 5: Break/Fix -- Wrong ASN

**Objective:** Understand what happens when BGP peers disagree on AS numbers.

### Setup (break it)

```bash
docker exec -it clab-dynamic-routing-bgp-srl2 sr_cli
```

Inside SR Linux:
```
enter candidate
set / network-instance default protocols bgp neighbor 10.1.2.1 peer-as 65099
commit now
exit
```

### Symptom

```bash
# Pings through srl2 fail (srl2 loses routes from srl1)
docker exec clab-dynamic-routing-bgp-host2 ping -c 3 -W 5 10.1.1.2
```

### Your Task

1. Check BGP neighbors on srl2 -- the srl1 session should be stuck in `active` or `connect`:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl2 sr_cli -c "show network-instance default protocols bgp neighbor"
   ```

2. Check srl1's view -- it expects AS 65002, but srl2 now announces itself as expecting AS 65099.

3. Fix by restoring the correct peer-as:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl2 sr_cli
   ```
   Inside SR Linux:
   ```
   enter candidate
   set / network-instance default protocols bgp neighbor 10.1.2.1 peer-as 65001
   commit now
   exit
   ```

4. Verify:
   ```bash
   docker exec clab-dynamic-routing-bgp-host2 ping -c 3 10.1.1.2
   ```

### Deliverables

- BGP neighbor output showing non-established state
- Explanation of AS mismatch

---

## Exercise 6: Break/Fix -- Stale Static Route Masks BGP

**Objective:** Understand administrative distance -- why a manually added static route overrides a correct BGP-learned route.

### Setup (break it)

```bash
docker exec -it clab-dynamic-routing-bgp-srl1 sr_cli
```

Inside SR Linux:
```
enter candidate
set / network-instance default next-hop-groups group nhg-wrong admin-state enable
set / network-instance default next-hop-groups group nhg-wrong nexthop 1 ip-address 10.1.3.2
set / network-instance default static-routes route 10.1.4.0/24 admin-state enable
set / network-instance default static-routes route 10.1.4.0/24 next-hop-group nhg-wrong
commit now
exit
```

This adds a static route on srl1 for host2's subnet (10.1.4.0/24) pointing at srl3 (10.1.3.2) -- the wrong direction. BGP correctly points this prefix at srl2 (10.1.2.2).

### Symptom

```bash
# host1 CANNOT reach host2
docker exec clab-dynamic-routing-bgp-host1 ping -c 3 -W 5 10.1.4.2

# But host1 CAN still reach host3
docker exec clab-dynamic-routing-bgp-host1 ping -c 3 10.1.5.2
```

### Your Task

1. Check the routing table on srl1:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl1 sr_cli -c "show network-instance default route-table ipv4-unicast summary"
   ```

2. Look at the route type for 10.1.4.0/24. It should show `static` instead of `bgp` -- even though BGP is still running and the session is healthy.

3. Check BGP neighbors on srl1 -- sessions are all `established`:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl1 sr_cli -c "show network-instance default protocols bgp neighbor"
   ```

4. Fix by deleting the stale static route:
   ```bash
   docker exec -it clab-dynamic-routing-bgp-srl1 sr_cli
   ```
   Inside SR Linux:
   ```
   enter candidate
   delete / network-instance default static-routes route 10.1.4.0/24
   delete / network-instance default next-hop-groups group nhg-wrong
   commit now
   exit
   ```

5. Verify:
   ```bash
   docker exec clab-dynamic-routing-bgp-host1 ping -c 3 10.1.4.2
   ```

### Deliverables

- Routing table showing `static` type for 10.1.4.0/24 with the wrong next-hop
- Explanation of why static routes (admin distance 5) beat BGP routes (admin distance 170)

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

- [ ] Exercise 1: Deployed lab, verified broken state, configured eBGP, compared routing tables
- [ ] Exercise 2: Enabled direct link, observed AS path selection via traceroute
- [ ] Exercise 3: Diagnosed and fixed missing export policy (sent-routes=0)
- [ ] Exercise 4: Observed link failure with automatic reroute (BGP convergence)
- [ ] Exercise 5: Diagnosed and fixed wrong ASN (peer-as mismatch)
- [ ] Exercise 6: Diagnosed stale static route masking BGP (administrative distance)

## Next Steps

Commit your exercises to your fork and proceed to Lesson 5 (coming soon).
