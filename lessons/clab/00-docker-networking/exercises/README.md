# Lesson 0 Exercises: Container Networking -- Linux Under the Hood

Complete these exercises to reinforce your understanding of the Linux primitives under container networking.

## Exercise 1: Inspect Docker's Network Plumbing

**Objective:** Trace the Linux components Docker creates when you run containers.

### Steps

1. Start two containers on the default bridge:
   ```bash
   docker run -d --name c1 alpine sleep 3600
   docker run -d --name c2 alpine sleep 3600
   ```

2. Find the `docker0` bridge on the host:
   ```bash
   ip link show docker0
   ```

3. List all interfaces attached to `docker0`:
   ```bash
   ip link show master docker0
   ```
   Note the veth names and the `@ifN` index numbers.

4. Look inside container `c1` and find the other end of the veth pair:
   ```bash
   docker exec c1 ip addr
   ```
   Compare the `@ifN` index to what you saw on the host.

5. Check the container's routing table:
   ```bash
   docker exec c1 ip route
   ```

6. Verify with Docker's own view:
   ```bash
   docker network inspect bridge
   ```

### Questions

- What is the IP of the `docker0` bridge? How does it relate to the container's default gateway?
- How can you match a host-side veth to its container-side eth0? (Hint: look at the `@ifN` indexes)
- What subnet does Docker use for the default bridge?

### Cleanup

```bash
docker rm -f c1 c2
```

---

## Exercise 2: Build a Container Network from Scratch

**Objective:** Manually create a namespace-based network using bridges and veth pairs -- the same primitives Docker uses.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Host                                               │
│                                                     │
│  ┌─────────────────────────────────┐                │
│  │         br-study                │                │
│  │       10.0.0.254/24            │                │
│  └──────┬──────────────┬───────────┘                │
│     veth-r-br       veth-b-br                       │
│         │              │                            │
│ ┌───────┴──────┐ ┌─────┴────────┐                   │
│ │   red        │ │   blue       │                   │
│ │   veth-r     │ │   veth-b     │                   │
│ │ 10.0.0.1/24  │ │ 10.0.0.2/24 │                   │
│ └──────────────┘ └──────────────┘                   │
└─────────────────────────────────────────────────────┘
```

### Steps

1. Create two network namespaces:
   ```bash
   sudo ip netns add red
   sudo ip netns add blue
   ```

2. Verify they exist:
   ```bash
   sudo ip netns list
   ```

3. Create a Linux bridge and assign it an IP:
   ```bash
   sudo ip link add br-study type bridge
   sudo ip link set br-study up
   sudo ip addr add 10.0.0.254/24 dev br-study
   ```

4. Create veth pairs and wire up the **red** namespace:
   ```bash
   sudo ip link add veth-r type veth peer name veth-r-br
   sudo ip link set veth-r netns red
   sudo ip link set veth-r-br master br-study
   sudo ip link set veth-r-br up
   ```

5. Create veth pairs and wire up the **blue** namespace:
   ```bash
   sudo ip link add veth-b type veth peer name veth-b-br
   sudo ip link set veth-b netns blue
   sudo ip link set veth-b-br master br-study
   sudo ip link set veth-b-br up
   ```

6. Configure IPs and bring interfaces up inside each namespace:
   ```bash
   # Red
   sudo ip netns exec red ip addr add 10.0.0.1/24 dev veth-r
   sudo ip netns exec red ip link set veth-r up
   sudo ip netns exec red ip link set lo up

   # Blue
   sudo ip netns exec blue ip addr add 10.0.0.2/24 dev veth-b
   sudo ip netns exec blue ip link set veth-b up
   sudo ip netns exec blue ip link set lo up
   ```

7. Test connectivity:
   ```bash
   # Red to blue
   sudo ip netns exec red ping -c 3 10.0.0.2

   # Blue to red
   sudo ip netns exec blue ping -c 3 10.0.0.1

   # Either namespace to the bridge gateway
   sudo ip netns exec red ping -c 2 10.0.0.254
   ```

### Questions

- What happens if you skip bringing up the loopback (`lo`)? Try it and see.
- What do you see when you run `ip link show master br-study` on the host?
- How is this different from what Docker does with `docker0`?

### Cleanup

```bash
sudo ip netns del red
sudo ip netns del blue
sudo ip link del br-study
```

---

## Exercise 3: Enable Internet Access (NAT)

**Objective:** Add NAT/masquerade rules so your manual namespaces can reach the internet, just like Docker containers.

### Prerequisites

Complete Exercise 2 first (namespaces, bridge, and veth pairs must be in place). If you already cleaned up, re-run the Exercise 2 steps before continuing.

### Steps

1. First, find your host's outbound interface:
   ```bash
   ip route show default
   ```
   Note the interface name after `dev` (e.g., `eth0`, `enp0s3`, `wlan0`).

2. Add default routes in each namespace so they send non-local traffic to the bridge:
   ```bash
   sudo ip netns exec red ip route add default via 10.0.0.254
   sudo ip netns exec blue ip route add default via 10.0.0.254
   ```

3. Enable IP forwarding on the host:
   ```bash
   sudo sysctl -w net.ipv4.ip_forward=1
   ```

4. Add a masquerade rule (replace `eth0` with your actual interface from step 1):
   ```bash
   sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
   ```

5. Test internet access from the namespaces:
   ```bash
   sudo ip netns exec red ping -c 3 8.8.8.8
   sudo ip netns exec blue ping -c 3 1.1.1.1
   ```

6. Inspect Docker's own NAT rules for comparison:
   ```bash
   sudo iptables -t nat -L POSTROUTING -v
   ```

### Questions

- What does the masquerade rule actually do to each packet?
- Why do we need IP forwarding enabled?
- Can you find Docker's masquerade rule for the 172.17.0.0/16 subnet?

### Cleanup

```bash
sudo ip netns del red
sudo ip netns del blue
sudo ip link del br-study
sudo iptables -t nat -D POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
```

---

## Bonus Exercise: Docker Compose Networking

**Objective:** See how Docker Compose creates its own bridge network (separate from docker0).

### Steps

1. Look at the provided `compose.yaml` in this directory.

2. Start the stack:
   ```bash
   docker compose up -d
   ```

3. List Docker networks and find the one Compose created:
   ```bash
   docker network ls
   ```

4. Inspect the Compose network:
   ```bash
   docker network inspect exercises_default
   ```

5. Find the Linux bridge backing the Compose network:
   ```bash
   ip link show type bridge
   ```
   You should see a new bridge in addition to `docker0`.

6. Test that containers can reach each other by name:
   ```bash
   docker compose exec client ping -c 2 web
   ```

7. Verify with `ip link show master <bridge-name>` to see the veth pairs -- same primitives as docker0.

### Cleanup

```bash
docker compose down
```

---

## Validation

Run the automated tests to verify your work:

```bash
cd lessons/clab/00-docker-networking
pytest tests/ -v
```

## Completion Checklist

- [ ] Exercise 1: Inspected Docker's bridge, veth pairs, and container networking
- [ ] Exercise 2: Built a namespace network from scratch with ping working
- [ ] Exercise 3: Enabled NAT and reached the internet from a namespace
- [ ] Bonus: Explored Docker Compose's bridge network

## Next Steps

Once complete, proceed to [Lesson 1: Containerlab Primer](../01-containerlab-primer/).
