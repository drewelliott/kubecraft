"""
Lesson 0: Container Networking -- Linux Under the Hood - Validation Tests

Run with: pytest tests/test_docker_networking.py -v

These tests validate the exercises:
- Exercise 1: Docker's bridge, veth pairs, container networking
- Exercise 2: Manual namespace lab (red/blue with br-study)
- Exercise 3: NAT/masquerade for internet access
"""

import subprocess
import pytest


def run_cmd(cmd: str) -> subprocess.CompletedProcess:
    """Run a shell command and return the CompletedProcess."""
    return subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )


def run_docker(cmd: str) -> str:
    """Run a docker command and return stdout."""
    result = run_cmd(f"docker {cmd}")
    return result.stdout.strip()


def network_exists(name: str) -> bool:
    """Check if a Docker network exists."""
    result = run_docker(f"network ls --filter name=^{name}$ --format '{{{{.Name}}}}'")
    return name in result


def netns_exists(name: str) -> bool:
    """Check if a network namespace exists."""
    result = run_cmd(f"sudo ip netns list")
    return name in result.stdout


def link_exists(name: str) -> bool:
    """Check if a network interface exists on the host."""
    result = run_cmd(f"ip link show {name}")
    return result.returncode == 0


class TestDockerBasics:
    """Verify Docker is working correctly."""

    def test_docker_available(self):
        """Docker CLI should be available."""
        result = run_cmd("docker --version")
        assert result.returncode == 0
        assert "Docker version" in result.stdout

    def test_docker_running(self):
        """Docker daemon should be running."""
        result = run_cmd("docker info")
        assert result.returncode == 0


class TestDefaultBridge:
    """Test understanding of default bridge network (Exercise 1)."""

    def test_default_bridge_exists(self):
        """Default bridge network should exist."""
        assert network_exists("bridge")

    def test_default_bridge_subnet(self):
        """Default bridge should have a 172.x subnet."""
        result = run_docker("network inspect bridge --format '{{.IPAM.Config}}'")
        assert "172." in result

    def test_docker0_interface_exists(self):
        """docker0 bridge interface should exist on the host."""
        assert link_exists("docker0")

    def test_docker0_is_bridge(self):
        """docker0 should be a bridge type interface."""
        result = run_cmd("ip -d link show docker0")
        assert "bridge" in result.stdout


class TestNamespaceLab:
    """Test manual namespace lab setup (Exercise 2).

    These tests verify that students have created the red/blue namespaces
    with br-study bridge and veth pairs, as described in the exercise.
    """

    def test_red_namespace_exists(self):
        """Red network namespace should exist."""
        assert netns_exists("red"), (
            "Namespace 'red' not found. "
            "Create it with: sudo ip netns add red"
        )

    def test_blue_namespace_exists(self):
        """Blue network namespace should exist."""
        assert netns_exists("blue"), (
            "Namespace 'blue' not found. "
            "Create it with: sudo ip netns add blue"
        )

    def test_bridge_exists(self):
        """br-study bridge should exist."""
        assert link_exists("br-study"), (
            "Bridge 'br-study' not found. "
            "Create it with: sudo ip link add br-study type bridge"
        )

    def test_bridge_has_ip(self):
        """br-study should have IP 10.0.0.254/24."""
        result = run_cmd("ip addr show br-study")
        assert "10.0.0.254/24" in result.stdout, (
            "br-study does not have IP 10.0.0.254/24. "
            "Set it with: sudo ip addr add 10.0.0.254/24 dev br-study"
        )

    def test_veth_pairs_on_bridge(self):
        """veth-r-br and veth-b-br should be attached to br-study."""
        result = run_cmd("ip link show master br-study")
        assert "veth-r-br" in result.stdout, (
            "veth-r-br not found on br-study"
        )
        assert "veth-b-br" in result.stdout, (
            "veth-b-br not found on br-study"
        )

    def test_red_namespace_has_ip(self):
        """Red namespace veth-r should have IP 10.0.0.1/24."""
        result = run_cmd("sudo ip netns exec red ip addr show veth-r")
        assert "10.0.0.1/24" in result.stdout, (
            "veth-r in red namespace does not have IP 10.0.0.1/24"
        )

    def test_blue_namespace_has_ip(self):
        """Blue namespace veth-b should have IP 10.0.0.2/24."""
        result = run_cmd("sudo ip netns exec blue ip addr show veth-b")
        assert "10.0.0.2/24" in result.stdout, (
            "veth-b in blue namespace does not have IP 10.0.0.2/24"
        )

    def test_red_can_ping_blue(self):
        """Red namespace should be able to ping blue (10.0.0.2)."""
        result = run_cmd("sudo ip netns exec red ping -c 1 -W 3 10.0.0.2")
        assert result.returncode == 0, (
            "Red cannot ping blue (10.0.0.2). "
            "Check that all interfaces are UP and IPs are assigned."
        )

    def test_blue_can_ping_red(self):
        """Blue namespace should be able to ping red (10.0.0.1)."""
        result = run_cmd("sudo ip netns exec blue ping -c 1 -W 3 10.0.0.1")
        assert result.returncode == 0, (
            "Blue cannot ping red (10.0.0.1). "
            "Check that all interfaces are UP and IPs are assigned."
        )

    def test_namespace_can_ping_bridge(self):
        """Red namespace should be able to ping the bridge gateway."""
        result = run_cmd(
            "sudo ip netns exec red ping -c 1 -W 3 10.0.0.254"
        )
        assert result.returncode == 0, (
            "Red cannot ping bridge (10.0.0.254). "
            "Check that br-study is UP and has the correct IP."
        )


class TestNAT:
    """Test NAT/masquerade configuration (Exercise 3).

    These tests verify that students have configured IP forwarding
    and masquerade rules for the namespace lab.
    """

    def test_ip_forwarding_enabled(self):
        """IP forwarding should be enabled."""
        result = run_cmd("sysctl net.ipv4.ip_forward")
        assert "= 1" in result.stdout, (
            "IP forwarding is not enabled. "
            "Enable with: sudo sysctl -w net.ipv4.ip_forward=1"
        )

    def test_masquerade_rule_exists(self):
        """An iptables masquerade rule for 10.0.0.0/24 should exist."""
        result = run_cmd("sudo iptables -t nat -L POSTROUTING -n")
        assert "10.0.0.0/24" in result.stdout and "MASQUERADE" in result.stdout, (
            "No masquerade rule found for 10.0.0.0/24. "
            "Add with: sudo iptables -t nat -A POSTROUTING "
            "-s 10.0.0.0/24 -o <interface> -j MASQUERADE"
        )

    def test_namespace_has_default_route(self):
        """Red namespace should have a default route via 10.0.0.254."""
        result = run_cmd("sudo ip netns exec red ip route show default")
        assert "10.0.0.254" in result.stdout, (
            "Red namespace has no default route. "
            "Add with: sudo ip netns exec red ip route add default via 10.0.0.254"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
