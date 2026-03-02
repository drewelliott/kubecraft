# Lesson 0: Container Networking -- Linux Under the Hood

Understand the Linux primitives that make container networking work.

## Objectives

By the end of this lesson, you will be able to:

- [ ] Explain what happens at the Linux level when you run `docker run`
- [ ] Identify network namespaces, veth pairs, and bridges on a Docker host
- [ ] Manually create a container-style network using `ip netns`, bridges, and veth pairs
- [ ] Configure NAT/masquerade to give namespaces internet access
- [ ] Trace a packet's path from container to host and beyond

## Prerequisites

- Docker installed and running
- Basic Docker command experience (run, ps, exec)
- Linux command line familiarity
- Root/sudo access (required for namespace lab)

## Video Outline

### 1. Opening -- What Happens When You Run `docker run`? (1 min)

- Containers are not magic -- they use standard Linux kernel features
- Every container gets its own network namespace
- Docker creates veth pairs and a bridge to connect them

### 2. Whiteboard -- The Architecture (2 min)

Draw in Excalidraw:
- Host network namespace with `docker0` bridge
- Container namespaces connected via veth pairs
- Each veth pair: one end in the container, one end on the bridge

### 3. Docker Demo -- Inspect the Plumbing (4 min)

```bash
# Run two containers and inspect the components
docker run -d --name c1 alpine sleep 3600
docker run -d --name c2 alpine sleep 3600

# On the host: find veth pairs and the bridge
ip link show
ip link show master docker0
bridge link

# Inside the container: see the other end
docker exec c1 ip addr
docker exec c1 ip route

# Docker's view
docker network inspect bridge
```

### 4. Manual Namespace Lab -- Build It from Scratch (5 min)

```bash
# Create namespaces, a bridge, and veth pairs
# Wire them together and test connectivity
ip netns add red
ip netns add blue
ip link add br-study type bridge
# ... (full commands in script.md)
```

### 5. NAT/Masquerade -- Internet Access (2 min)

```bash
# Enable forwarding and add masquerade rule
sysctl -w net.ipv4.ip_forward=1
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o <host-iface> -j MASQUERADE
```

### 6. Brief Note -- Docker Compose Creates Its Own Bridges (1 min)

- Each Compose project gets a dedicated bridge network
- Bonus exercise covers this

### 7. Closing -- Bridge to Containerlab (1 min)

- Containerlab uses these same Linux primitives
- Next lesson: deploy real network operating systems

## Lab Architecture

```mermaid
graph TD
    subgraph Host["Host Network Namespace"]
        BR["docker0 / br-study<br/>(Linux bridge)"]
        subgraph red [red namespace]
            VR["veth-r<br/>10.0.0.1/24"]
        end
        subgraph blue [blue namespace]
            VB["veth-b<br/>10.0.0.2/24"]
        end
        VR --- |veth-r-br| BR
        VB --- |veth-b-br| BR
    end
```

## Key Concepts

### Network Namespaces

A network namespace is an isolated copy of the network stack -- its own interfaces, routes, and iptables rules. Every Docker container runs inside one. You can create them manually with `ip netns add`.

### Virtual Ethernet (veth) Pairs

A veth pair is a virtual cable: packets sent into one end come out the other. Docker uses them to connect a container's namespace to the host bridge. One end lives inside the container (as `eth0`), the other end is attached to the bridge on the host.

### Linux Bridges

A Linux bridge works like a virtual network switch. Docker's `docker0` bridge connects all default-network containers so they can reach each other and the host. You can create bridges manually with `ip link add <name> type bridge`.

### NAT / Masquerade

For containers (or namespaces) to reach the internet, the host must forward packets and masquerade the source IP. Docker sets this up automatically with iptables rules. You can do the same manually with `iptables -t nat -A POSTROUTING ... -j MASQUERADE`.

## Common Issues

**Ping between namespaces fails:**

Check each layer bottom-up:
```bash
# Are the interfaces UP?
sudo ip netns exec red ip link show veth-r

# Is the bridge UP?
ip link show br-study

# Are IPs assigned?
sudo ip netns exec red ip addr show veth-r

# Are veth pairs attached to the bridge?
ip link show master br-study
```

**Internet access from namespaces fails but local ping works:**

This is almost always a missing FORWARD rule or masquerade rule:
```bash
# Check FORWARD chain (Docker sets policy to DROP)
sudo iptables -L FORWARD -v -n

# Check masquerade rule exists
sudo iptables -t nat -L POSTROUTING -v -n
```

**"Operation not permitted" errors:**

Namespace operations require root. Use `sudo` for all `ip netns exec` commands:
```bash
# Wrong
ip netns exec red ping 10.0.0.2

# Correct
sudo ip netns exec red ping 10.0.0.2
```

## Exercises

Complete the exercises in [exercises/README.md](exercises/README.md).

## Navigation

[Course Index](../README.md) | Next: [Lesson 1: Containerlab Primer](../01-containerlab-primer/)

## Additional Resources

- [Network Namespaces man page](https://man7.org/linux/man-pages/man7/network_namespaces.7.html)
- [veth man page](https://man7.org/linux/man-pages/man4/veth.4.html)
- [ip-netns man page](https://man7.org/linux/man-pages/man8/ip-netns.8.html)
- [Docker Networking Overview](https://docs.docker.com/network/)
