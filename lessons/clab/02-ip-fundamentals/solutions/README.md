# Lesson 2 Solutions

Reference solutions for the IP Fundamentals exercises.

## Exercise 1: Deploy and Verify

**Adjacent pings (succeed):**

```bash
$ docker exec clab-ip-fundamentals-host1 ping -c 3 10.1.1.1
PING 10.1.1.1 (10.1.1.1): 56 data bytes
64 bytes from 10.1.1.1: seq=0 ttl=64 time=1.234 ms
64 bytes from 10.1.1.1: seq=1 ttl=64 time=0.567 ms
64 bytes from 10.1.1.1: seq=2 ttl=64 time=0.432 ms
--- 10.1.1.1 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

Router-to-router (succeeds):
```
A:srl1# ping 10.1.2.2 network-instance default
Using network instance default
PING 10.1.2.2 (10.1.2.2) 56(84) bytes of data.
64 bytes from 10.1.2.2: icmp_seq=1 ttl=64 time=1.12 ms
```

**Cross-subnet ping (fails):**

```bash
$ docker exec clab-ip-fundamentals-host1 ping -c 3 10.1.3.2
PING 10.1.3.2 (10.1.3.2): 56 data bytes
--- 10.1.3.2 ping statistics ---
3 packets transmitted, 0 packets received, 100% packet loss
```

**Why cross-subnet fails:** host1 sends the packet to its default gateway (srl1 at 10.1.1.1). srl1 receives it and checks its routing table. srl1 only knows about its directly connected subnets: 10.1.1.0/24 and 10.1.2.0/24. It has no route to 10.1.3.0/24, so it drops the packet. This is what static or dynamic routing solves (Lesson 3).

**ARP table on host1:**
```bash
$ docker exec clab-ip-fundamentals-host1 arp -n
Address         HWtype  HWaddress           Flags  Iface
10.1.1.1        ether   aa:c1:ab:xx:xx:xx   C      eth1
```

host1 has learned srl1's MAC address via ARP -- this is how Layer 3 (IP) resolves to Layer 2 (MAC) for local communication.

---

## Exercise 2: Read the Config

**srl2's host_vars:**
```yaml
interfaces:
  - name: ethernet-1/1
    ipv4_address: 10.1.2.2/24
    description: Link to srl1
  - name: ethernet-1/2
    ipv4_address: 10.1.3.1/24
    description: Link to host2
```

**Generated CLI commands for srl2:**

```
enter candidate
set / interface ethernet-1/1 admin-state enable
set / interface ethernet-1/1 subinterface 0 admin-state enable
set / interface ethernet-1/1 subinterface 0 description Link to srl1
set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable
set / interface ethernet-1/1 subinterface 0 ipv4 address 10.1.2.2/24
set / network-instance default interface ethernet-1/1.0
set / interface ethernet-1/2 admin-state enable
set / interface ethernet-1/2 subinterface 0 admin-state enable
set / interface ethernet-1/2 subinterface 0 description Link to host2
set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable
set / interface ethernet-1/2 subinterface 0 ipv4 address 10.1.3.1/24
set / network-instance default interface ethernet-1/2.0
commit now
```

The template loops twice (once per interface in srl2's host_vars), generating the full set of CLI commands. The same template with srl1's variables would produce different commands with different IPs -- that's the value of templating.

---

## Exercise 3: Add a Loopback Interface

**Modified `ansible/host_vars/srl1.yml`:**

```yaml
---
interfaces:
  - name: ethernet-1/1
    ipv4_address: 10.1.1.1/24
    description: Link to host1
  - name: ethernet-1/2
    ipv4_address: 10.1.2.1/24
    description: Link to srl2
  - name: lo0
    ipv4_address: 10.10.10.1/32
    description: Loopback for management
```

**Verification:**
```
A:srl1# show interface lo0
==========================================================
lo0 is up
  lo0.0 is up
    Network-instances:
      * Name: default
    Encapsulation   : null
    Type            : None
    IPv4 addr    : 10.10.10.1/32 (static)
```

The Jinja2 template didn't need any changes -- the `{% for iface in interfaces %}` loop automatically handles the new entry. This demonstrates a key benefit of templating: adding a new interface only requires changing the data, not the template.

---

## Exercise 4: Break/Fix -- Interface Down

**Diagnosis:**
```
A:srl1# show interface brief
+---------------------+----------+----------+-------+----------+
|      Interface      |  Admin   |  Oper    | Speed |   Type   |
+=====================+==========+==========+=======+==========+
| ethernet-1/1        | disable  | down     |       |          |  <-- PROBLEM
| ethernet-1/2        | enable   | up       | 25G   | ethernet |
+---------------------+----------+----------+-------+----------+
```

The `Admin` column shows `disable` for ethernet-1/1. This means someone (us) explicitly disabled the interface. The `Oper` state is `down` because the admin state overrides.

**Fix:**
```
A:srl1# enter candidate
set / interface ethernet-1/1 admin-state enable
commit now
```

**Verification:**
```bash
$ docker exec clab-ip-fundamentals-host1 ping -c 3 10.1.1.1
3 packets transmitted, 3 packets received, 0% packet loss
```

**Key lesson:** Always check admin-state first. An operationally down interface might just be admin-disabled, not physically broken.

---

## Exercise 5: Break/Fix -- Subnet Mismatch

**Diagnosis:**
```bash
$ docker exec clab-ip-fundamentals-host1 ip addr show eth1
    inet 10.1.1.200/30 scope global eth1
```

**The math:**

With `10.1.1.200/30`:
- A /30 subnet contains 4 addresses
- Network address: 10.1.1.200 (the .200 aligned to /30 boundary)
- Broadcast: 10.1.1.203
- Usable hosts: 10.1.1.201 and 10.1.1.202

srl1 is at 10.1.1.1 -- this is NOT in the 10.1.1.200/30 range. From host1's perspective, 10.1.1.1 is on a completely different network. host1 would need to route to reach it, but it has no route for that destination (the default gateway might not be reachable either).

**Fix:**
```bash
docker exec clab-ip-fundamentals-host1 ip addr del 10.1.1.200/30 dev eth1
docker exec clab-ip-fundamentals-host1 ip addr add 10.1.1.2/24 dev eth1
```

**Key lesson:** Subnet masks determine what's "local" (reachable via Layer 2) and what's "remote" (needs a router). Both endpoints must agree on the subnet for direct communication to work.

---

## Exercise 6: Break/Fix -- Missing Gateway

**Diagnosis:**
```bash
$ docker exec clab-ip-fundamentals-host1 ip route show
10.1.1.0/24 dev eth1 scope link src 10.1.1.2
```

Only one route exists: the directly connected 10.1.1.0/24 subnet. No default route.

- **10.1.1.1 works** because it's in the 10.1.1.0/24 subnet -- host1 can reach it directly at Layer 2 (ARP + MAC).
- **10.1.2.1 fails** because it's NOT in any known subnet. With no default route, the kernel returns "Network is unreachable" immediately (it doesn't even try to send the packet).

**Fix:**
```bash
docker exec clab-ip-fundamentals-host1 ip route add default via 10.1.1.1 dev eth1
```

**After fix:**
```bash
$ docker exec clab-ip-fundamentals-host1 ip route show
default via 10.1.1.1 dev eth1
10.1.1.0/24 dev eth1 scope link src 10.1.1.2
```

Now any traffic not matching 10.1.1.0/24 goes to 10.1.1.1 (srl1). Since srl1 has 10.1.2.0/24 directly connected, the ping to 10.1.2.1 succeeds.

**Key lesson:** A default route is the "catch-all" -- it tells the host where to send traffic for any network it doesn't know about. Without it, the host can only communicate on its directly connected subnets.

---

## Key Takeaways

1. **Subnet masks determine locality** -- two devices must be on the same subnet to communicate directly at Layer 2
2. **ARP bridges L3 to L2** -- IP addresses are resolved to MAC addresses via ARP for local delivery
3. **Default routes are essential** -- without a gateway, hosts can only reach their local subnet
4. **Admin-state vs oper-state** -- an interface can be operationally down because it's admin-disabled (check admin-state first)
5. **Jinja2 templates separate data from logic** -- one template handles any number of interfaces; only the host_vars change
6. **Cross-subnet communication requires routing** -- routers must know the path to every destination network (covered in Lesson 3)
