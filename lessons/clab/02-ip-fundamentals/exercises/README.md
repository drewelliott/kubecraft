# Lesson 2 Exercises: IP Fundamentals & Basic Connectivity

Complete these exercises to build your IP addressing and Ansible skills.

## Exercise 1: Deploy and Verify

**Objective:** Deploy the lab topology, apply configuration with Ansible, and verify connectivity.

### Steps

1. Deploy the topology:
   ```bash
   cd lessons/clab/02-ip-fundamentals
   containerlab deploy -t topology/lab.clab.yml
   ```

2. Apply router configuration with Ansible:
   ```bash
   cd ansible
   ansible-playbook -i inventory.yml playbook.yml
   ```

3. Verify host-to-router connectivity:
   ```bash
   docker exec clab-ip-fundamentals-host1 ping -c 3 10.1.1.1
   docker exec clab-ip-fundamentals-host2 ping -c 3 10.1.3.1
   ```

4. Verify router-to-router connectivity:
   ```bash
   docker exec -it clab-ip-fundamentals-srl1 sr_cli
   ```
   Inside SR Linux:
   ```
   ping 10.1.2.2 network-instance default
   exit
   ```

5. Try cross-subnet ping (this should fail):
   ```bash
   docker exec clab-ip-fundamentals-host1 ping -c 3 10.1.3.2
   ```

6. Inspect ARP tables:
   ```bash
   # On host1
   docker exec clab-ip-fundamentals-host1 arp -n

   # On srl1
   docker exec -it clab-ip-fundamentals-srl1 sr_cli -c "show arpnd arp-entries"
   ```

### Deliverables

Create a file `exercises/exercise1-results.md` with:
- Which pings succeeded and which failed
- The ARP table entries you observed
- Your explanation of why cross-subnet ping fails

---

## Exercise 2: Read the Config

**Objective:** Understand how Jinja2 templates generate device-specific configurations.

### Steps

1. Open the Jinja2 template:
   ```bash
   cat ansible/templates/srl_interfaces.json.j2
   ```

2. Open srl2's host variables:
   ```bash
   cat ansible/host_vars/srl2.yml
   ```

3. Manually trace through the template, substituting srl2's variables. For each `{{ iface.name }}` and `{{ iface.ipv4_address }}`, write out what the actual value would be.

4. Write out the complete list of CLI commands that would be generated for srl2.

### Deliverables

Create a file `exercises/srl2-commands.txt` with the exact CLI commands generated when the template is rendered for srl2.

---

## Exercise 3: Add a Loopback Interface

**Objective:** Modify the Ansible configuration to add a new interface.

### Steps

1. Edit `ansible/host_vars/srl1.yml` and add a loopback interface:
   ```yaml
   - name: lo0
     ipv4_address: 10.10.10.1/32
     description: Loopback for management
   ```

2. Re-run the playbook:
   ```bash
   cd ansible
   ansible-playbook -i inventory.yml playbook.yml
   ```

3. Verify the loopback is configured:
   ```bash
   docker exec -it clab-ip-fundamentals-srl1 sr_cli -c "show interface lo0"
   ```

4. Check the routing table to see the new /32 route:
   ```bash
   docker exec -it clab-ip-fundamentals-srl1 sr_cli -c "show network-instance default route-table ipv4-unicast summary"
   ```

### Deliverables

- Your modified `ansible/host_vars/srl1.yml`
- Output of `show interface lo0`

---

## Exercise 4: Break/Fix -- Interface Down

**Objective:** Diagnose and fix an admin-disabled interface.

### Setup (break it)

```bash
docker exec -it clab-ip-fundamentals-srl1 sr_cli
```

Inside SR Linux:
```
enter candidate
set / interface ethernet-1/1 admin-state disable
commit now
```

### Symptom

```bash
docker exec clab-ip-fundamentals-host1 ping -c 3 10.1.1.1
# FAILS -- no response
```

### Your Task

1. Diagnose: Which interface is down? Use `show interface brief` on srl1.
2. Fix: Re-enable the interface and commit.
3. Verify: Confirm ping works again.

### Deliverables

Document the diagnostic commands you used and the fix you applied.

---

## Exercise 5: Break/Fix -- Subnet Mismatch

**Objective:** Diagnose connectivity failure caused by mismatched subnet configuration.

### Setup (break it)

```bash
docker exec clab-ip-fundamentals-host1 ip addr del 10.1.1.2/24 dev eth1
docker exec clab-ip-fundamentals-host1 ip addr add 10.1.1.200/30 dev eth1
```

### Symptom

```bash
docker exec clab-ip-fundamentals-host1 ping -c 3 10.1.1.1
# FAILS -- "Network is unreachable"
```

### Your Task

1. Check host1's IP configuration:
   ```bash
   docker exec clab-ip-fundamentals-host1 ip addr show eth1
   ```

2. Calculate the /30 subnet for 10.1.1.200:
   - Network: 10.1.1.200
   - Broadcast: 10.1.1.203
   - Usable range: 10.1.1.201 - 10.1.1.202

3. Is srl1 (10.1.1.1) within that range? Why or why not?

4. Fix by restoring the correct address:
   ```bash
   docker exec clab-ip-fundamentals-host1 ip addr del 10.1.1.200/30 dev eth1
   docker exec clab-ip-fundamentals-host1 ip addr add 10.1.1.2/24 dev eth1
   ```

5. Verify ping works again.

### Deliverables

Explain why a /30 mask at .200 prevents reaching .1, and how subnet masks determine what is "local."

---

## Exercise 6: Break/Fix -- Missing Gateway

**Objective:** Understand why a default route is needed for cross-subnet communication.

### Setup (break it)

```bash
docker exec clab-ip-fundamentals-host1 ip route del default
```

### Symptom

```bash
# This works (same subnet)
docker exec clab-ip-fundamentals-host1 ping -c 3 10.1.1.1

# This fails (different subnet)
docker exec clab-ip-fundamentals-host1 ping -c 3 10.1.2.1
# "Network is unreachable"
```

### Your Task

1. Check the routing table:
   ```bash
   docker exec clab-ip-fundamentals-host1 ip route show
   ```

2. Notice: only the `10.1.1.0/24` route exists (directly connected). No default route.

3. Explain: Why does 10.1.1.1 work but 10.1.2.1 doesn't?

4. Fix by restoring the default route:
   ```bash
   docker exec clab-ip-fundamentals-host1 ip route add default via 10.1.1.1 dev eth1
   ```

5. Verify: ping 10.1.2.1 now works (srl1 has that subnet directly connected).

### Deliverables

Explain the difference between local and remote subnets, and why gateways are needed.

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

- [ ] Exercise 1: Deployed lab, applied config, verified adjacent pings work
- [ ] Exercise 2: Traced Jinja2 template for srl2, wrote generated commands
- [ ] Exercise 3: Added loopback interface via Ansible
- [ ] Exercise 4: Diagnosed and fixed admin-disabled interface
- [ ] Exercise 5: Diagnosed and fixed subnet mismatch
- [ ] Exercise 6: Diagnosed and fixed missing default route

## Next Steps

Commit your exercises to your fork and proceed to [Lesson 3: Routing Basics](../03-routing-basics/).
