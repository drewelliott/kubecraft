# Lesson 0 Solutions

Reference solutions for the Container Networking exercises.

## Exercise 1: Inspect Docker's Network Plumbing

**What is the IP of docker0? How does it relate to the default gateway?**

The `docker0` bridge is typically `172.17.0.1`. Inside each container, `ip route` shows this as the default gateway:

```
default via 172.17.0.1 dev eth0
172.17.0.0/16 dev eth0 scope link src 172.17.0.2
```

The bridge IS the gateway -- packets from containers destined outside the subnet go to `docker0`, and the host routes them.

**How to match a host-side veth to its container-side eth0:**

Start from **inside the container** -- this is the reliable direction. Each container namespace has its own interface index numbering, so `eth0` is always index 2 in every container. That means the host-side `@if2` is the same for all containers and doesn't help you distinguish them.

But the container's `@ifN` references the **host-side** index, which is globally unique:

```bash
# Inside c1
docker exec c1 ip addr
```

```
2: eth0@if13: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    inet 172.17.0.2/16 scope global eth0
```

The `@if13` tells you the host-side peer is interface index 13.

```bash
# On the host
ip link show master docker0
```

```
13: veth91835c2@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    master docker0 state UP ... link-netnsid 0
14: veth6ea59a4@if2: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    master docker0 state UP ... link-netnsid 1
```

Index 13 is `veth91835c2` -- that's c1's veth pair. Both host-side veths show `@if2` because each namespace numbers `eth0` as index 2 independently. The `link-netnsid` (0 vs 1) identifies which namespace each belongs to, but reading `@ifN` from inside the container is the simplest way to trace the pair.

**Default bridge subnet:** Typically `172.17.0.0/16`.

---

## Exercise 2: Build a Container Network from Scratch

### Complete command sequence

```bash
# 1. Create namespaces
sudo ip netns add red
sudo ip netns add blue

# 2. Verify
sudo ip netns list
```

**Expected output:**
```
blue
red
```

```bash
# 3. Create bridge
sudo ip link add br-study type bridge
sudo ip link set br-study up
sudo ip addr add 10.0.0.254/24 dev br-study

# 4. Wire up red namespace
sudo ip link add veth-r type veth peer name veth-r-br
sudo ip link set veth-r netns red
sudo ip link set veth-r-br master br-study
sudo ip link set veth-r-br up

# 5. Wire up blue namespace
sudo ip link add veth-b type veth peer name veth-b-br
sudo ip link set veth-b netns blue
sudo ip link set veth-b-br master br-study
sudo ip link set veth-b-br up

# 6. Configure IPs (but NOT loopback yet)
sudo ip netns exec red ip addr add 10.0.0.1/24 dev veth-r
sudo ip netns exec red ip link set veth-r up

sudo ip netns exec blue ip addr add 10.0.0.2/24 dev veth-b
sudo ip netns exec blue ip link set veth-b up
```

```bash
# 7. Test connectivity between namespaces
sudo ip netns exec red ping -c 3 10.0.0.2
```

**Expected output:**
```
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.050 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.040 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=0.038 ms

--- 10.0.0.2 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2003ms
```

```bash
sudo ip netns exec red ping -c 2 10.0.0.254
```

**Expected output:**
```
PING 10.0.0.254 (10.0.0.254) 56(84) bytes of data.
64 bytes from 10.0.0.254: icmp_seq=1 ttl=64 time=0.030 ms
64 bytes from 10.0.0.254: icmp_seq=2 ttl=64 time=0.028 ms
```

```bash
# 8. Try pinging loopback (fails -- lo is DOWN)
sudo ip netns exec red ping -c 2 127.0.0.1
```

**Expected output:**
```
ping: connect: Network is unreachable
```

```bash
# 9. Bring up loopback and verify
sudo ip netns exec red ip link set lo up
sudo ip netns exec blue ip link set lo up
sudo ip netns exec red ping -c 2 127.0.0.1
```

**Expected output:**
```
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.020 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.018 ms
```

### Answers to questions

**Why did 127.0.0.1 fail before bringing up `lo`, even though pinging the other namespace worked?**

Pinging 10.0.0.2 works because that traffic goes out through `veth-r`, across the bridge, and into the blue namespace -- all of those interfaces are UP. But `127.0.0.1` is handled by the loopback interface (`lo`), which starts DOWN in new namespaces. The kernel won't route to an address on a down interface. Loopback is a separate interface from the bridge-connected veths -- bringing up `veth-r` doesn't help loopback traffic.

**What does `ip link show master br-study` show?**

```
3: veth-r-br: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    master br-study state UP
4: veth-b-br: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    master br-study state UP
```

The two host-side veth interfaces attached to the bridge -- exactly like `ip link show master docker0` shows Docker's veth pairs.

**How is this different from Docker?**

It's the same primitives. Docker automates:
- Namespace creation (one per container)
- Bridge creation (`docker0`)
- veth pair creation and attachment
- IP assignment (via IPAM)
- Route configuration
- iptables rules for NAT

We did all of these steps manually.

---

## Exercise 3: Enable Internet Access (NAT)

### Complete command sequence

```bash
# 1. Find outbound interface
ip route show default
```

**Expected output (varies by system):**
```
default via 192.168.1.1 dev enp6s0 proto dhcp metric 100
```

The interface is `enp6s0` (use whatever your system shows -- on modern Linux this is usually **not** `eth0`).

```bash
# 2. Add default routes
sudo ip netns exec red ip route add default via 10.0.0.254
sudo ip netns exec blue ip route add default via 10.0.0.254

# 3. Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1
```

**Expected output:**
```
net.ipv4.ip_forward = 1
```

```bash
# 4. Allow forwarding for br-study
sudo iptables -A FORWARD -i br-study -j ACCEPT
sudo iptables -A FORWARD -o br-study -j ACCEPT
```

```bash
# 5. Add masquerade rule (replace enp6s0 with your interface)
sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o enp6s0 -j MASQUERADE
```

```bash
# 6. Test internet access
sudo ip netns exec red ping -c 3 8.8.8.8
```

**Expected output:**
```
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=112 time=20.5 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=112 time=17.8 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=112 time=16.3 ms
```

```bash
# 7. Compare with Docker's rules
sudo iptables -t nat -L POSTROUTING -v
```

**Expected output (relevant lines):**
```
Chain POSTROUTING (policy ACCEPT)
 pkts bytes target     prot opt in     out     source               destination
    3   252 MASQUERADE  all  --  any    enp6s0  10.0.0.0/24          anywhere
    0     0 MASQUERADE  all  --  any    !docker0  172.17.0.0/16        anywhere
```

Docker's rule looks almost identical to ours -- masquerade traffic from its subnet going out any interface except docker0.

### Answers to questions

**What does the masquerade rule do?**

It rewrites the source IP address of outbound packets from 10.0.0.x to the host's IP on the outbound interface. When the reply comes back, the kernel automatically translates the destination IP back to the original namespace IP. This is Source NAT (SNAT) -- the same thing your home router does.

**Why do we need IP forwarding?**

Without `net.ipv4.ip_forward=1`, the Linux kernel drops any packet that arrives on one interface but is destined for another. It only processes packets addressed to its own IPs. IP forwarding tells the kernel to act as a router and forward packets between interfaces.

**Why does Docker's FORWARD policy block our traffic?**

Docker sets the FORWARD chain policy to DROP for security -- it only allows forwarding for traffic on its own networks (docker0 and any custom Docker networks). You can see this with:

```bash
sudo iptables -L FORWARD -v
```

```
Chain FORWARD (policy DROP)
 pkts bytes target     prot opt in     out     source               destination
    0     0 DOCKER-USER  all  --  any    any     anywhere             anywhere
    0     0 DOCKER-FORWARD  all  --  any    any     anywhere             anywhere
```

Our br-study traffic doesn't match any of Docker's FORWARD rules, so it hits the DROP policy. Adding explicit ACCEPT rules for br-study tells the kernel to allow forwarding for our bridge. Docker does this automatically for its own bridges -- we have to do it manually for ours.

**Docker's masquerade rule:**

Docker creates a rule like:
```
MASQUERADE  all  --  anywhere  anywhere  source: 172.17.0.0/16  ! out: docker0
```

This masquerades traffic from containers (172.17.0.0/16) going out any interface except docker0 itself. Traffic between containers stays on the bridge and doesn't need NAT.

---

## Exercise 4: Break/Fix -- Bridge Down

**Diagnosis:**

```bash
ip link show br-study
```

```
5: br-study: <BROADCAST,MULTICAST> mtu 1500 ...
    link/ether 42:65:a1:xx:xx:xx brd ff:ff:ff:ff:ff:ff
```

Notice the flags: `<BROADCAST,MULTICAST>` without `UP`. When the bridge is up, it shows `<BROADCAST,MULTICAST,UP,LOWER_UP>`. A down bridge cannot forward frames between its ports -- it's like unplugging a switch.

The veth pairs are still attached (`ip link show master br-study` still lists them), but traffic can't flow through the bridge.

**Fix:**

```bash
sudo ip link set br-study up
```

**Verification:**

```bash
sudo ip netns exec red ping -c 2 10.0.0.2
```

**Key lesson:** A Linux bridge must be UP to forward traffic. Even if all veth pairs are correctly attached and all interfaces inside namespaces have IPs, a downed bridge stops all communication. This is the virtual equivalent of a switch losing power.

---

## Exercise 5: Break/Fix -- Missing Masquerade

**Diagnosis:**

```bash
sudo iptables -t nat -L POSTROUTING -v -n
```

```
Chain POSTROUTING (policy ACCEPT)
 pkts bytes target     prot opt in     out     source               destination
    0     0 MASQUERADE  all  --  *      !docker0  172.17.0.0/16        0.0.0.0/0
```

Only Docker's masquerade rule is present. Our rule for 10.0.0.0/24 is gone.

**Why local works but internet doesn't:**

Local traffic (red to blue, red to bridge) stays on the br-study bridge. It never leaves the host, so it never needs NAT. The bridge forwards frames based on MAC addresses -- this is pure Layer 2 switching.

Internet traffic must leave the host via the outbound interface (e.g., enp6s0). Without masquerade, the source IP is 10.0.0.1 -- a private, non-routable address. The ISP's routers don't know how to send replies back to 10.0.0.1, so the traffic is silently dropped. Masquerade rewrites the source IP to the host's public IP, and the kernel tracks the mapping so return traffic gets translated back.

**Fix:**

```bash
sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o enp6s0 -j MASQUERADE
```

**Verification:**

```bash
sudo ip netns exec red ping -c 3 8.8.8.8
```

**Key lesson:** Masquerade (SNAT) is only needed when traffic crosses a network boundary -- from private addresses to the internet. Local bridge traffic doesn't need NAT because both endpoints are directly reachable at Layer 2.

---

## Key Takeaways

1. **Network namespaces** are what isolate container networking -- each container gets its own
2. **veth pairs** are virtual cables connecting namespaces to bridges
3. **Linux bridges** are virtual switches that connect multiple veth pairs
4. **NAT/masquerade** rewrites source IPs so namespace traffic can reach the internet
5. Docker automates all of this -- understanding the primitives helps you debug and build beyond Docker
