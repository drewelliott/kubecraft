"""Lesson 04: Dynamic Routing with BGP -- Automated Validation"""

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
    return docker_exec(f"clab-dynamic-routing-bgp-{node}", f'sr_cli -c "{cmd}"')


LAB_NAME = "dynamic-routing-bgp"
ROUTERS = ["srl1", "srl2", "srl3"]
HOSTS = ["host1", "host2", "host3"]


class TestEnvironment:
    """Verify lab environment is correctly set up."""

    def test_gnmic_installed(self):
        """gNMIc CLI tool is available."""
        result = run_cmd("gnmic version")
        assert result.returncode == 0, "gNMIc is not installed. Run: brew install gnmic"

    def test_containers_running(self):
        """All 6 lab containers are running."""
        result = run_cmd("docker ps --format '{{.Names}}'")
        for node in ROUTERS + HOSTS:
            assert f"clab-{LAB_NAME}-{node}" in result.stdout, f"{node} not running"


class TestTopologyStructure:
    """Verify topology file and config files have correct structure."""

    def test_topology_file_exists(self):
        """Topology file exists."""
        result = run_cmd("test -f topology/lab.clab.yml")
        assert result.returncode == 0

    def test_startup_configs_exist(self):
        """Startup config files exist for all routers."""
        for router in ROUTERS:
            result = run_cmd(f"test -f topology/configs/{router}-base.cli")
            assert result.returncode == 0, f"Missing startup config for {router}"

    def test_gnmic_config_exists(self):
        """gNMIc configuration files exist."""
        result = run_cmd("test -f gnmic/.gnmic.yml")
        assert result.returncode == 0, "Missing .gnmic.yml"
        for router in ROUTERS:
            result = run_cmd(f"test -f gnmic/configs/{router}-bgp.json")
            assert result.returncode == 0, f"Missing BGP config for {router}"


class TestBGPSessions:
    """Verify BGP sessions are established (run after exercise 2)."""

    @pytest.mark.parametrize("router", ROUTERS)
    def test_bgp_sessions_established(self, router):
        """BGP sessions on {router} are established."""
        result = srl_cli(router, "show network-instance default protocols bgp neighbor")
        assert "established" in result.stdout.lower(), (
            f"{router} has no established BGP sessions"
        )


class TestConnectivity:
    """Verify end-to-end connectivity via BGP-learned routes."""

    @pytest.mark.parametrize(
        "src,dst_ip",
        [
            ("host1", "10.1.4.2"),
            ("host1", "10.1.5.2"),
            ("host2", "10.1.5.2"),
        ],
    )
    def test_cross_subnet_ping(self, src, dst_ip):
        """Cross-subnet ping from {src} to {dst_ip} succeeds."""
        result = docker_exec(f"clab-{LAB_NAME}-{src}", f"ping -c 3 -W 5 {dst_ip}")
        assert "0% packet loss" in result.stdout, f"{src} -> {dst_ip} failed"

    def test_routes_are_bgp_not_static(self):
        """Routing table shows BGP routes, not static."""
        result = srl_cli(
            "srl1",
            "show network-instance default route-table ipv4-unicast summary",
        )
        assert "bgp" in result.stdout.lower(), "No BGP routes in srl1 routing table"
