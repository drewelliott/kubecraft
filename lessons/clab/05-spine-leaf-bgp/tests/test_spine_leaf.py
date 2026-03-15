"""Lesson 05: Spine-Leaf Networking with BGP -- Automated Validation"""

import subprocess
import pytest


def run_cmd(cmd: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )


def docker_exec(container: str, cmd: str) -> subprocess.CompletedProcess:
    """Execute a command in a container."""
    return run_cmd(f"docker exec {container} {cmd}")


def srl_cli(node: str, cmd: str) -> subprocess.CompletedProcess:
    """Execute an SR Linux CLI command."""
    return docker_exec(f"clab-spine-leaf-bgp-{node}", f'sr_cli -c "{cmd}"')


LAB_NAME = "spine-leaf-bgp"
SPINES = ["spine1", "spine2"]
LEAVES = ["leaf1", "leaf2", "leaf3", "leaf4"]
HOSTS = ["host1", "host2", "host3", "host4"]
ALL_ROUTERS = SPINES + LEAVES


class TestEnvironment:
    """Verify lab environment is correctly set up."""

    def test_gnmic_installed(self):
        """gNMIc CLI tool is available."""
        result = run_cmd("gnmic version")
        assert result.returncode == 0, "gNMIc is not installed. Run: brew install gnmic"

    def test_containers_running(self):
        """All 10 lab containers are running."""
        result = run_cmd("docker ps --format '{{.Names}}'")
        for node in ALL_ROUTERS + HOSTS:
            assert f"clab-{LAB_NAME}-{node}" in result.stdout, f"{node} not running"


class TestTopologyStructure:
    """Verify topology file and config files have correct structure."""

    def test_topology_file_exists(self):
        """Topology file exists."""
        result = run_cmd("test -f topology/lab.clab.yml")
        assert result.returncode == 0

    @pytest.mark.parametrize("router", ALL_ROUTERS)
    def test_startup_configs_exist(self, router):
        """Startup config exists for {router}."""
        result = run_cmd(f"test -f topology/configs/{router}-base.cli")
        assert result.returncode == 0, f"Missing startup config for {router}"

    @pytest.mark.parametrize("router", ALL_ROUTERS)
    def test_gnmic_configs_exist(self, router):
        """gNMIc BGP config exists for {router}."""
        result = run_cmd(f"test -f gnmic/configs/{router}-bgp.json")
        assert result.returncode == 0, f"Missing BGP config for {router}"


class TestBGPSessions:
    """Verify BGP sessions are established."""

    @pytest.mark.parametrize("spine", SPINES)
    def test_spine_has_four_sessions(self, spine):
        """Spine {spine} has 4 established BGP sessions (one per leaf)."""
        result = srl_cli(
            spine, "show network-instance default protocols bgp neighbor"
        )
        count = result.stdout.lower().count("established")
        assert count >= 4, (
            f"{spine} has {count} established sessions, expected 4"
        )

    @pytest.mark.parametrize("leaf", LEAVES)
    def test_leaf_has_two_sessions(self, leaf):
        """Leaf {leaf} has 2 established BGP sessions (one per spine)."""
        result = srl_cli(
            leaf, "show network-instance default protocols bgp neighbor"
        )
        count = result.stdout.lower().count("established")
        assert count >= 2, (
            f"{leaf} has {count} established sessions, expected 2"
        )


class TestConnectivity:
    """Verify end-to-end cross-leaf connectivity."""

    @pytest.mark.parametrize(
        "src,dst_ip",
        [
            ("host1", "10.20.2.2"),
            ("host1", "10.20.3.2"),
            ("host1", "10.20.4.2"),
            ("host2", "10.20.4.2"),
        ],
    )
    def test_cross_leaf_ping(self, src, dst_ip):
        """Cross-leaf ping from {src} to {dst_ip} succeeds."""
        result = docker_exec(f"clab-{LAB_NAME}-{src}", f"ping -c 3 -W 5 {dst_ip}")
        assert "0% packet loss" in result.stdout, f"{src} -> {dst_ip} failed"

    def test_routes_are_bgp(self):
        """Routing table shows BGP routes on leaf1."""
        result = srl_cli(
            "leaf1",
            "show network-instance default route-table ipv4-unicast summary",
        )
        assert "bgp" in result.stdout.lower(), "No BGP routes in leaf1 routing table"
