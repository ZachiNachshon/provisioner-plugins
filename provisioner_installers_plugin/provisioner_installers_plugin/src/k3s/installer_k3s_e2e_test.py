#!/usr/bin/env python3

import unittest
import time

import pytest

from provisioner.main import root_menu
from provisioner_shared.test_lib.cli_container import RemoteSSHContainer
from provisioner_shared.test_lib.test_cli_runner import CliTestRunnerConfig, TestCliRunner


# To run these directly from the terminal use:
#  ./run_tests.py plugins/provisioner_installers_plugin/provisioner_installers_plugin/src/k3s/installer_k3s_e2e_test.py --only-e2e n--container
#
@pytest.mark.e2e
class InstallerK3sE2ETestShould(unittest.TestCase):

    NETWORK_NAME = "k3s-test-network"
    
    SERVER_CONTAINER_NAME = "k3s-server-test"
    SERVER_CONTAINER_SSH_PORT = 2222
    SERVER_CONTAINER_IP = "127.0.0.1"
    SERVER_CONTAINER_TOKEN = "some-token"

    AGENT_CONTAINER_NAME = "k3s-agent-test"
    AGENT_CONTAINER_SSH_PORT = 2223

    # Run before each test
    @classmethod
    def setUpClass(cls):
        """Start the container once before any tests in this class."""
        cls.server_container = RemoteSSHContainer(
            network_name=cls.NETWORK_NAME,
            custom_flags=[
                f"--name={cls.SERVER_CONTAINER_NAME}",
            ],
            ports={6443: 6443}
        )
        cls.server_container.start(ssh_port=cls.SERVER_CONTAINER_SSH_PORT)

        cls.agent_container = RemoteSSHContainer(
            network_name=cls.NETWORK_NAME,
            custom_flags=[
                f"--name={cls.AGENT_CONTAINER_NAME}",
            ],
        )
        cls.agent_container.start(ssh_port=cls.AGENT_CONTAINER_SSH_PORT)
        
    # Stop after each test
    @classmethod
    def tearDownClass(cls):
        """Stop the container after all tests in this class have completed."""
        if cls.server_container:
            cls.server_container.stop()
            cls.server_container = None  # Ensure cleanup
        if cls.agent_container:
            cls.agent_container.stop()
            cls.agent_container = None  # Ensure cleanup    

    # K3s cannot be installed on a container running on macOS.
    # This test is validating only the installation step for both server and agent.
    def test_e2e_install_k3s_server_as_binary_on_remote_successfully(self):
        server_ip = self.try_read_k3s_server_container_ip(self.server_container)
        server_url = f"https://{server_ip}:6443"

        create_server_output = self.install_k3s_server_on_remote_container(self.SERVER_CONTAINER_TOKEN, self.SERVER_CONTAINER_SSH_PORT, server_ip)
        self.assertIn("Successfully installed utility", create_server_output)
        self.assertIn("name:    k3s-server", create_server_output)
        self.assertIn("version: v1.32.3+k3s1", create_server_output)
        self.assertIn("binary:  /home/pi/.local/bin/k3s", create_server_output)

        create_agent_output = self.install_k3s_agent_on_remote_container(self.SERVER_CONTAINER_TOKEN, self.AGENT_CONTAINER_SSH_PORT, server_url)
        self.assertIn("Successfully installed utility", create_agent_output)
        self.assertIn("name:    k3s-agent", create_agent_output)
        self.assertIn("version: v1.32.3+k3s1", create_agent_output)
        self.assertIn("binary:  /home/pi/.local/bin/k3s", create_agent_output)

        # # Print k3s server logs
        # k3s_logs = self.server_container.exec_run("cat /var/log/k3s.log")
        # print("K3s Server Logs:")
        # print(k3s_logs.output.decode('utf-8'))

        # nodes_cmd_result = self.server_container.exec_run("k3s kubectl get nodes -o wide")
        # nodes_output = nodes_cmd_result.output.decode('utf-8')
        # print(f"Nodes: {nodes_output}")
        # assert len(nodes_output.strip().split("\n")) > 1, "Agent failed to register with the server"


    @pytest.mark.skip(reason="""
Test temporarily skipped - cannot run systemd service on Linux container runing on macOS.
Systemd requires special privileges and setup, and containers (especially on macOS or Docker Desktop) 
don't support systemd by default.
Failing on:
System has not been booted with systemd as init system (PID 1). Can't operate.Failed to connect to bus: Host is down""")
    def test_e2e_install_k3s_server_as_system_service_on_remote_successfully(self):
        print("TODO: Implement this test")

    def install_k3s_server_on_remote_container(self, k3s_token: str, server_container_ssh_port: int, server_ip: str):
        return TestCliRunner.run(
            root_menu,
            [
                "install",
                "--environment",
                "Remote",
                "--connect-mode",
                "Flags",
                "--node-username",
                "pi",
                "--node-password",
                "raspberry",
                "--ip-address",
                "127.0.0.1",
                "--port",
                server_container_ssh_port,
                "--hostname",
                "test-node",
                "--verbosity",
                "Verbose",
                "k8s",
                "distro",
                "k3s-server",
                "--k3s-token",
                k3s_token,
                "--k3s-args",
                f"--disable traefik --disable kubernetes-dashboard --tls-san={server_ip} --node-ip={server_ip} --snapshotter=native",
                "--install-as-binary",
                "--version",
                "v1.32.3+k3s1",
                "-vy",
            ],
            test_cfg=CliTestRunnerConfig(is_installer_plugin_test=True),
        )
    
    def install_k3s_agent_on_remote_container(self, k3s_token: str, agent_container_ssh_port: int, k3s_server_url: str):
        return TestCliRunner.run(
            root_menu,
            [
                "install",
                "--environment",
                "Remote",
                "--connect-mode",
                "Flags",
                "--node-username",
                "pi",
                "--node-password",
                "raspberry",
                "--ip-address",
                "127.0.0.1",
                "--port",
                agent_container_ssh_port,
                "--hostname",
                "test-node",
                "--verbosity",
                "Verbose",
                "k8s",
                "distro",
                "k3s-agent",
                "--k3s-url",
                k3s_server_url,
                "--k3s-token",
                k3s_token,
                "--install-as-binary",
                "--version",
                "v1.32.3+k3s1",
                "-vy",
            ],
            test_cfg=CliTestRunnerConfig(is_installer_plugin_test=True),
        )
    
    def try_read_k3s_server_container_ip(self, server_container: RemoteSSHContainer):
        server_ip_cmd_result = server_container.exec_run("hostname -i")
        server_ip = server_ip_cmd_result.output.decode('utf-8').strip()
        if not server_ip:
            # Fallback command to get IP address
            server_ip_cmd_result = server_container.exec_run("ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'")
            server_ip = server_ip_cmd_result.output.decode('utf-8').strip()
        
        # Make sure we have a valid IP
        assert server_ip, "Failed to get server IP address"
        print(f"Server IP address: {server_ip}")
        return server_ip

    def try_ping_server_container_or_fail(self, server_ip: str, server_container: RemoteSSHContainer):
        ping_result = server_container.exec_run(f"ping -c 3 {server_ip}")
        print(f"Ping result: {ping_result.output.decode('utf-8')}")
        assert ping_result.exit_code == 0, f"Cannot communicate withserver container at {server_ip}"

    def check_k3s_process_running_on_server_container(self, server_container: RemoteSSHContainer):
        ps_output = server_container.exec_run("ps -ef | grep k3s | grep -v grep")
        print(f"K3s processes: {ps_output.output.decode('utf-8')}")

        # log_output = self.server_container.exec_run("cat /tmp/k3s.log")
        # print(f"K3s logs: {log_output.output.decode('utf-8')}")

    def try_check_agent_connectivity_to_k3s_server(self, server_ip: str, server_container: RemoteSSHContainer, agent_container: RemoteSSHContainer):
        # Ensure the agent can reach the server on port 6443 (will be used later)
        server_container.exec_run("timeout 5 nc -l -p 6443 &")
        time.sleep(1)  # Give the server time to start listening
        nc_test_result = agent_container.exec_run(f"timeout 5 nc -vz {server_ip} 6443")
        print(f"Network connectivity test: {nc_test_result.output.decode('utf-8')}")

    def print_all_k3s_nodes_from_server_container(self, server_container: RemoteSSHContainer):
        server_status = server_container.exec_run("/home/pi/.local/bin/k3s kubectl get nodes --kubeconfig /etc/rancher/k3s/k3s.yaml")
        print(f"K3s server status: {server_status.output.decode('utf-8')}")

    def verify_k3s_server_listening_on_expected_port(self, server_container: RemoteSSHContainer, expected_port: int):
        # Verify the server is listening on port 6443
        server_ports = server_container.exec_run(f"netstat -tuln | grep {expected_port}")
        print(f"Server ports: {server_ports.output.decode('utf-8')}")
        assert server_ports.exit_code == 0, f"Server is not listening on port {expected_port}"  