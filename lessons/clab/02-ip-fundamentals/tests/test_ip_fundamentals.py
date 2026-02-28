"""
Lesson 2: IP Fundamentals -- Validation Tests

Run with: pytest tests/test_ip_fundamentals.py -v

These tests verify:
1. Required tools are installed (containerlab, Docker, Ansible)
2. Topology file is valid with correct structure
3. Ansible configuration files are valid
4. Lab deploys successfully with all 4 containers
5. Adjacent connectivity works after Ansible config is applied
"""

import subprocess
import os
import pytest
import time
from pathlib import Path


LESSON_DIR = Path(__file__).parent.parent
TOPOLOGY_FILE = LESSON_DIR / "topology" / "lab.clab.yml"
ANSIBLE_DIR = LESSON_DIR / "ansible"


def run_command(cmd: str, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )


class TestEnvironment:
    """Verify the lab environment is correctly set up."""

    def test_containerlab_installed(self):
        """Containerlab CLI should be available."""
        result = run_command("containerlab version")
        assert result.returncode == 0

    def test_docker_available(self):
        """Docker should be running and accessible."""
        result = run_command("docker version")
        assert result.returncode == 0

    def test_ansible_installed(self):
        """Ansible should be installed."""
        result = run_command("ansible --version")
        assert result.returncode == 0

    def test_topology_file_exists(self):
        """Main topology file should exist."""
        assert TOPOLOGY_FILE.exists(), f"Topology file not found: {TOPOLOGY_FILE}"

    def test_topology_file_valid_yaml(self):
        """Topology file should be valid YAML."""
        import yaml
        with open(TOPOLOGY_FILE) as f:
            data = yaml.safe_load(f)
            assert data is not None
            assert "topology" in data
            assert "nodes" in data["topology"]


class TestTopologyStructure:
    """Verify topology file has correct structure for a 4-node linear topology."""

    @pytest.fixture
    def topology(self):
        """Load topology file."""
        import yaml
        with open(TOPOLOGY_FILE) as f:
            return yaml.safe_load(f)

    def test_has_name(self, topology):
        """Topology should have a name."""
        assert "name" in topology
        assert topology["name"] == "ip-fundamentals"

    def test_has_four_nodes(self, topology):
        """Topology should define exactly 4 nodes."""
        nodes = topology["topology"]["nodes"]
        assert len(nodes) == 4, f"Expected 4 nodes, got {len(nodes)}"

    def test_has_srl_routers(self, topology):
        """Should have two SR Linux router nodes."""
        nodes = topology["topology"]["nodes"]
        assert "srl1" in nodes and "srl2" in nodes
        assert nodes["srl1"]["kind"] == "srl"
        assert nodes["srl2"]["kind"] == "srl"

    def test_has_linux_hosts(self, topology):
        """Should have two Linux host nodes."""
        nodes = topology["topology"]["nodes"]
        assert "host1" in nodes and "host2" in nodes
        assert nodes["host1"]["kind"] == "linux"
        assert nodes["host2"]["kind"] == "linux"

    def test_has_three_links(self, topology):
        """Topology should define exactly 3 links."""
        links = topology["topology"]["links"]
        assert len(links) == 3, f"Expected 3 links, got {len(links)}"

    def test_no_latest_tags(self, topology):
        """No node should use 'latest' image tag."""
        nodes = topology["topology"]["nodes"]
        for name, config in nodes.items():
            image = config.get("image", "")
            assert "latest" not in image, f"Node {name} uses 'latest' tag"

    def test_hosts_have_exec(self, topology):
        """Linux hosts should have exec commands for IP configuration."""
        nodes = topology["topology"]["nodes"]
        for host in ["host1", "host2"]:
            assert "exec" in nodes[host], f"{host} missing exec commands"
            assert len(nodes[host]["exec"]) >= 2, f"{host} needs at least IP and route commands"

    def test_routers_have_mgmt_ips(self, topology):
        """SR Linux routers should have pinned management IPs."""
        nodes = topology["topology"]["nodes"]
        assert "mgmt-ipv4" in nodes["srl1"]
        assert "mgmt-ipv4" in nodes["srl2"]


class TestAnsibleStructure:
    """Verify Ansible configuration files exist and are valid."""

    def test_inventory_exists(self):
        """Ansible inventory should exist."""
        assert (ANSIBLE_DIR / "inventory.yml").exists()

    def test_playbook_exists(self):
        """Ansible playbook should exist."""
        assert (ANSIBLE_DIR / "playbook.yml").exists()

    def test_template_exists(self):
        """Jinja2 template should exist."""
        assert (ANSIBLE_DIR / "templates" / "srl_interfaces.json.j2").exists()

    def test_host_vars_exist(self):
        """Host vars for both routers should exist."""
        assert (ANSIBLE_DIR / "host_vars" / "srl1.yml").exists()
        assert (ANSIBLE_DIR / "host_vars" / "srl2.yml").exists()

    def test_inventory_valid_yaml(self):
        """Inventory should be valid YAML with expected structure."""
        import yaml
        with open(ANSIBLE_DIR / "inventory.yml") as f:
            data = yaml.safe_load(f)
            assert "all" in data

    def test_host_vars_have_interfaces(self):
        """Each router's host_vars should define interfaces."""
        import yaml
        for host in ["srl1", "srl2"]:
            with open(ANSIBLE_DIR / "host_vars" / f"{host}.yml") as f:
                data = yaml.safe_load(f)
                assert "interfaces" in data
                assert len(data["interfaces"]) >= 2
                for iface in data["interfaces"]:
                    assert "name" in iface
                    assert "ipv4_address" in iface

    def test_template_has_jinja2_syntax(self):
        """Template should contain Jinja2 loop and variable syntax."""
        template = (ANSIBLE_DIR / "templates" / "srl_interfaces.json.j2").read_text()
        assert "{% for" in template
        assert "{{ iface" in template
        assert "commit now" in template


class TestLabDeployment:
    """Test that the lab can be deployed. Requires containerlab + Docker."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Ensure lab is destroyed after test."""
        yield
        run_command(f"containerlab destroy -t {TOPOLOGY_FILE} --cleanup 2>/dev/null || true")
        time.sleep(2)

    def test_lab_deploys_successfully(self):
        """Lab should deploy without errors."""
        run_command(f"containerlab destroy -t {TOPOLOGY_FILE} --cleanup 2>/dev/null || true")
        time.sleep(2)
        result = run_command(f"containerlab deploy -t {TOPOLOGY_FILE}", timeout=180)
        assert result.returncode == 0, f"Deploy failed: {result.stderr}"

    def test_all_containers_running(self):
        """All 4 containers should be running after deployment."""
        run_command(f"containerlab destroy -t {TOPOLOGY_FILE} --cleanup 2>/dev/null || true")
        time.sleep(2)
        run_command(f"containerlab deploy -t {TOPOLOGY_FILE}", timeout=180)
        time.sleep(5)
        result = run_command("docker ps --filter 'name=clab-ip-fundamentals' --format '{{.Names}}'")
        containers = [c for c in result.stdout.strip().split('\n') if c]
        assert len(containers) == 4, f"Expected 4 containers, got: {containers}"


class TestConnectivity:
    """Test connectivity after Ansible config is applied. Requires running lab."""

    @pytest.fixture(autouse=True)
    def deploy_and_configure(self):
        """Deploy lab and apply Ansible configuration."""
        run_command(f"containerlab destroy -t {TOPOLOGY_FILE} --cleanup 2>/dev/null || true")
        time.sleep(2)
        run_command(f"containerlab deploy -t {TOPOLOGY_FILE}", timeout=180)
        time.sleep(10)
        run_command(
            f"cd {ANSIBLE_DIR} && ansible-playbook -i inventory.yml playbook.yml",
            timeout=120
        )
        time.sleep(5)
        yield
        run_command(f"containerlab destroy -t {TOPOLOGY_FILE} --cleanup 2>/dev/null || true")

    def test_host1_pings_srl1(self):
        """host1 should reach srl1 on the directly connected subnet."""
        result = run_command("docker exec clab-ip-fundamentals-host1 ping -c 2 -W 3 10.1.1.1")
        assert result.returncode == 0, f"host1 -> srl1 ping failed: {result.stdout}"

    def test_host2_pings_srl2(self):
        """host2 should reach srl2 on the directly connected subnet."""
        result = run_command("docker exec clab-ip-fundamentals-host2 ping -c 2 -W 3 10.1.3.1")
        assert result.returncode == 0, f"host2 -> srl2 ping failed: {result.stdout}"

    def test_srl1_pings_srl2(self):
        """srl1 should reach srl2 on the transit subnet."""
        result = run_command(
            "docker exec clab-ip-fundamentals-srl1 sr_cli -c 'ping -c 2 10.1.2.2 network-instance default'"
        )
        assert "2 received" in result.stdout or result.returncode == 0, \
            f"srl1 -> srl2 ping failed: {result.stdout}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
