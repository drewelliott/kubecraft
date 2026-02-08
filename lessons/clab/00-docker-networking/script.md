# Lesson 0: Container Networking -- Linux Under the Hood - Video Script

## Lesson Information

| Field | Value |
|-------|-------|
| **Lesson Number** | 00 |
| **Title** | Container Networking -- Linux Under the Hood |
| **Duration Target** | 15-18 minutes |
| **Prerequisites** | Basic Docker knowledge, Linux command line |
| **Learning Objectives** | Understand namespaces, veth pairs, bridges; inspect Docker's networking plumbing; manually build a namespace network; configure NAT/masquerade |

---

## Pre-Recording Checklist

- [ ] Docker installed and running
- [ ] No stale containers: `docker rm -f $(docker ps -aq) 2>/dev/null`
- [ ] No stale namespaces: `sudo ip netns del red 2>/dev/null; sudo ip netns del blue 2>/dev/null`
- [ ] No stale bridge: `sudo ip link del br-study 2>/dev/null`
- [ ] Excalidraw open in browser with blank canvas
- [ ] Screen resolution set (1920x1080)
- [ ] Terminal font size increased (14-16pt)
- [ ] Notifications disabled
- [ ] Clean terminal: `clear && history -c`

---

## Script

### Opening Hook (45 seconds)

> **[ON CAMERA or VOICEOVER -- Terminal visible]**
>
> "When you type `docker run`, a container appears with its own IP address, it can talk to other containers, it can reach the internet -- and it all just works. But what actually happens under the hood?
>
> The answer isn't Docker magic. It's standard Linux kernel features -- network namespaces, virtual ethernet pairs, and bridges. These are the same primitives that Kubernetes, containerlab, and every container runtime uses.
>
> In this lesson, we're going to see them in action inside Docker, and then rip Docker away and build the same network by hand."

**Visual:** Terminal with a blank prompt

---

### Section 1: Whiteboard -- The Architecture (2-3 minutes)

> **[VOICEOVER -- Switch to Excalidraw]**
>
> "Before we touch the terminal, let me draw what we're about to explore."

**Excalidraw Drawing Steps:**

1. Draw a large rectangle labeled "Host (default network namespace)"
2. Inside it, draw a smaller rectangle labeled "docker0 (Linux bridge)" -- explain: "This is a virtual network switch that Docker creates at startup."
3. Draw two smaller boxes below/beside the bridge, labeled "Container 1 (namespace)" and "Container 2 (namespace)" -- explain: "Each container runs in its own network namespace. That means it has its own interfaces, its own routes, its own view of the network."
4. Draw lines connecting each container box to the bridge -- label them "veth pair" -- explain: "A veth pair is a virtual ethernet cable. One end lives inside the container as eth0, the other end is plugged into the bridge on the host. Packets go in one end and come out the other."
5. Draw an arrow from the bridge upward to "Internet" -- label it "NAT / masquerade" -- explain: "For containers to reach the outside world, the host rewrites their source IP using iptables. This is the same NAT your home router does."

> "That's the complete picture. A bridge, namespaces, veth pairs, and NAT. Now let's see the real thing."

**Transition:** "Let's fire up some containers and find each of these components."

---

### Section 2: Docker Demo -- Inspect the Plumbing (4-5 minutes)

> **[VOICEOVER -- Switch to terminal]**
>
> "Let's start two containers and then trace every component we just drew."

```bash
docker run -d --name c1 alpine sleep 3600
docker run -d --name c2 alpine sleep 3600
```

> "Two alpine containers running. Now let's find the bridge."

```bash
ip link show docker0
```

**Expected Output:**
```
4: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    link/ether 02:42:xx:xx:xx:xx brd ff:ff:ff:ff:ff:ff
```

> "There's docker0 -- the Linux bridge. Now let's see what's plugged into it."

```bash
ip link show master docker0
```

**Expected Output:**
```
6: vethXXXXXXX@if5: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    master docker0 state UP
8: vethYYYYYYY@if7: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    master docker0 state UP
```

> "Two veth interfaces, both attached to docker0. These are the host-side ends of our veth pairs. The `@if5` and `@if7` tell us the interface index of the other end -- which is inside the container."

**[Whiteboard annotation moment]** -- Switch to Excalidraw briefly and write the real veth names on the diagram next to the veth pair labels.

> "You can also use the `bridge` command to see this."

```bash
bridge link
```

> "Now let's look inside one of the containers."

```bash
docker exec c1 ip addr
```

**Expected Output:**
```
1: lo: <LOOPBACK,UP,LOWER_UP> ...
    inet 127.0.0.1/8 scope host lo
5: eth0@if6: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
    inet 172.17.0.2/16 scope global eth0
```

> "Inside the container, there's `eth0` -- that's the container-side end of the veth pair. Notice the interface index `@if6` -- that matches the host-side veth we saw earlier. And it has an IP on the 172.17.0.0/16 subnet."

```bash
docker exec c1 ip route
```

**Expected Output:**
```
default via 172.17.0.1 dev eth0
172.17.0.0/16 dev eth0 scope link src 172.17.0.2
```

> "The default gateway is 172.17.0.1 -- that's the docker0 bridge itself. So when this container wants to reach anything outside its subnet, packets go to docker0, and the host routes them."

**[Whiteboard annotation moment]** -- Switch to Excalidraw and write the real IPs on the diagram (172.17.0.2 for c1, 172.17.0.3 for c2, 172.17.0.1 for docker0).

> "Let's confirm with Docker's own view."

```bash
docker network inspect bridge --format '{{json .IPAM.Config}}' | python3 -m json.tool
```

**Expected Output:**
```json
[
    {
        "Subnet": "172.17.0.0/16",
        "Gateway": "172.17.0.1"
    }
]
```

> "Everything matches our whiteboard. The bridge, the veth pairs, the IPs -- it's all standard Linux networking. Docker just automates the setup."

```bash
# Cleanup
docker rm -f c1 c2
```

**Transition:** "Now let's prove it by building the same thing ourselves -- no Docker involved."

---

### Section 3: Manual Namespace Lab (5-6 minutes)

> **[VOICEOVER]**
>
> "We're going to recreate what Docker does, step by step, using nothing but Linux commands. We'll create two network namespaces -- think of them as two containers -- connect them through a bridge, and get them talking."

**[Whiteboard moment]** -- Switch to Excalidraw and draw a new diagram:
- Host with bridge "br-study" (10.0.0.254/24)
- Namespace "red" with "veth-r" (10.0.0.1/24) connected via "veth-r-br" to bridge
- Namespace "blue" with "veth-b" (10.0.0.2/24) connected via "veth-b-br" to bridge

> "Here's our target. Two namespaces, one bridge, two veth pairs. Let's build it."

**Step 1: Create the namespaces**

```bash
sudo ip netns add red
sudo ip netns add blue
```

> "We now have two isolated network namespaces. They have nothing in them -- no interfaces, no routes."

```bash
sudo ip netns exec red ip link show
```

**Expected Output:**
```
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
```

> "Just a loopback, and it's DOWN. Completely empty."

**Step 2: Create the bridge**

```bash
sudo ip link add br-study type bridge
sudo ip link set br-study up
sudo ip addr add 10.0.0.254/24 dev br-study
```

> "We created our bridge, brought it up, and gave it an IP. This is the gateway for our namespaces, just like docker0 is the gateway for Docker containers."

**Step 3: Create veth pairs and wire them up**

```bash
# Create veth pair for red namespace
sudo ip link add veth-r type veth peer name veth-r-br

# Put one end in the red namespace, the other on the bridge
sudo ip link set veth-r netns red
sudo ip link set veth-r-br master br-study
sudo ip link set veth-r-br up
```

> "We created a veth pair: `veth-r` and `veth-r-br`. We moved `veth-r` into the red namespace and attached `veth-r-br` to our bridge. Same thing for blue."

```bash
# Create veth pair for blue namespace
sudo ip link add veth-b type veth peer name veth-b-br

sudo ip link set veth-b netns blue
sudo ip link set veth-b-br master br-study
sudo ip link set veth-b-br up
```

**Step 4: Configure IPs inside the namespaces**

```bash
# Red namespace
sudo ip netns exec red ip addr add 10.0.0.1/24 dev veth-r
sudo ip netns exec red ip link set veth-r up
sudo ip netns exec red ip link set lo up

# Blue namespace
sudo ip netns exec blue ip addr add 10.0.0.2/24 dev veth-b
sudo ip netns exec blue ip link set veth-b up
sudo ip netns exec blue ip link set lo up
```

> "We assigned IPs, brought the interfaces up, and brought up loopback. Now let's test."

**Step 5: Test connectivity**

```bash
sudo ip netns exec red ping -c 3 10.0.0.2
```

**Expected Output:**
```
PING 10.0.0.2 (10.0.0.2) 56(84) bytes of data.
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.050 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.040 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=0.038 ms
```

> "Red can reach blue through the bridge. This is exactly what Docker does -- we just did it by hand."

```bash
# Also test blue to red
sudo ip netns exec blue ping -c 2 10.0.0.1
```

> "And we can ping the bridge gateway from either namespace."

```bash
sudo ip netns exec red ping -c 2 10.0.0.254
```

**Key Points to Emphasize:**
- Network namespaces = container network isolation
- veth pairs = the virtual cable connecting container to bridge
- Linux bridge = virtual switch connecting everything
- This is exactly what Docker automates

**Transition:** "Our namespaces can talk to each other, but they can't reach the internet yet. For that, we need NAT."

---

### Section 4: NAT / Masquerade -- Internet Access (2-3 minutes)

> **[VOICEOVER]**
>
> "Right now, if our red namespace tries to ping 8.8.8.8, it won't work. The packet would leave the namespace, reach the bridge, and then... nothing. The host doesn't know to forward it, and even if it did, the return traffic wouldn't know how to get back.
>
> We need two things: IP forwarding and masquerading."

**Step 1: Add default routes in the namespaces**

```bash
sudo ip netns exec red ip route add default via 10.0.0.254
sudo ip netns exec blue ip route add default via 10.0.0.254
```

> "Now the namespaces know to send non-local traffic to the bridge."

**Step 2: Enable IP forwarding**

```bash
sudo sysctl -w net.ipv4.ip_forward=1
```

> "This tells the Linux kernel to forward packets between interfaces. Without this, the host drops any packet that isn't addressed to itself."

**Step 3: Add the masquerade rule**

```bash
# Replace eth0 with your host's outbound interface (check with: ip route show default)
sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
```

> "This NAT rule says: any packet from our 10.0.0.0/24 subnet leaving via the host's outbound interface should have its source IP rewritten to the host's IP. Return traffic gets translated back automatically.
>
> This is exactly what Docker does. If you run `iptables -t nat -L`, you'll see Docker's own masquerade rules for the 172.17.0.0/16 subnet."

**Step 4: Test internet access**

```bash
sudo ip netns exec red ping -c 3 8.8.8.8
```

**Expected Output:**
```
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=117 time=10.2 ms
64 bytes from 8.8.8.8: icmp_seq=2 ttl=117 time=9.8 ms
64 bytes from 8.8.8.8: icmp_seq=3 ttl=117 time=9.9 ms
```

> "Our hand-built namespace can reach the internet -- just like a Docker container."

**[Whiteboard annotation moment]** -- Switch to Excalidraw and add the NAT arrow to the manual namespace diagram, label it "iptables MASQUERADE".

**Key Points:**
- IP forwarding = kernel will route packets between interfaces
- Masquerade = rewrite source IP for outbound traffic (SNAT)
- Docker does both of these automatically

---

### Section 5: Docker Compose Note (1 minute)

> **[VOICEOVER]**
>
> "One quick note on Docker Compose. When you run `docker compose up`, Compose doesn't use the default docker0 bridge. It creates a dedicated bridge network for each project. This gives you DNS resolution by container name and isolation between projects.
>
> There's a bonus exercise where you can explore this, but the important thing to understand is that it's the same primitive underneath -- another Linux bridge with veth pairs."

---

### Cleanup (30 seconds)

> **[VOICEOVER]**
>
> "Let's clean up our manual namespace lab."

```bash
sudo ip netns del red
sudo ip netns del blue
sudo ip link del br-study
sudo iptables -t nat -D POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
```

> "Deleting the namespaces automatically removes the veth pairs that were inside them."

---

### Recap (30 seconds)

> **[VOICEOVER]**
>
> "Let's recap what we learned:
>
> - Every container runs in a **network namespace** -- an isolated network stack
> - **veth pairs** are virtual cables connecting containers to a bridge
> - A **Linux bridge** acts as a virtual switch connecting namespaces together
> - **NAT with iptables** gives containers internet access by masquerading their IPs
> - Docker automates all of this, but the primitives are plain Linux"

---

### Closing (30 seconds)

> **[VOICEOVER]**
>
> "Head to the exercises folder and practice. You'll inspect Docker's plumbing, build the namespace lab yourself, and set up NAT.
>
> In the next lesson, we'll use containerlab -- which uses these same Linux primitives -- to deploy real network operating systems like Nokia SR Linux in containers. See you there."

---

## Post-Recording Checklist

- [ ] All containers removed: `docker rm -f $(docker ps -aq)`
- [ ] Namespaces removed: `sudo ip netns del red; sudo ip netns del blue`
- [ ] Bridge removed: `sudo ip link del br-study`
- [ ] iptables rule removed
- [ ] Timing verified: ~15-18 minutes
- [ ] All commands worked correctly

---

## B-Roll / Supplementary Footage Needed

1. Excalidraw whiteboard drawing -- Docker architecture (docker0, namespaces, veth pairs)
2. Excalidraw whiteboard drawing -- Manual namespace lab architecture (br-study, red, blue)
3. Excalidraw annotation overlays with real device names and IPs
4. Close-up of `ip link show master docker0` output with callouts

---

## Notes for Editing

- **2:00** -- Whiteboard drawing should be clear and deliberate, pause if needed for annotation
- **5:00** -- When showing `ip link show master docker0`, highlight the veth names and @ifN indexes
- **6:00** -- Side-by-side terminal: host `ip link show` vs container `ip addr` to show both ends of veth pair
- **10:00** -- The ping success moment in the namespace lab is the payoff -- let it breathe
- **13:00** -- The internet ping from a hand-built namespace is the second payoff
- **End** -- Preview containerlab with a brief shot of a topology file
