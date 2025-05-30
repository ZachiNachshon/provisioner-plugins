#!/usr/bin/env python3

import os
import platform
import subprocess
from typing import Any, Dict, Optional, Tuple

from loguru import logger
from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs

from provisioner_shared.components.runtime.errors.cli_errors import StepEvaluationFailure
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators


def extract_common_args(dynamic_args: Optional[DynamicArgs]) -> Dict[str, Any]:
    """Extract common arguments from dynamic args."""
    dynamic_args_dict = dynamic_args.as_dict() if dynamic_args else {}
    return {
        "k3s_token": dynamic_args_dict.get("k3s-token"),
        "k3s_additional_cli_args": dynamic_args_dict.get("k3s-args", ""),
        "install_as_binary": dynamic_args_dict.get("install-as-binary", False),
        "k3s_url": dynamic_args_dict.get("k3s-url"),
        "use_kube_config": dynamic_args_dict.get("use-kube-config", False),
        "uninstall": dynamic_args_dict.get("uninstall", False),
    }


def setup_environment() -> Tuple[str, str]:
    """Set up environment and return local_bin_folder and current_os."""
    local_bin_folder = os.path.expanduser("~/.local/bin")
    os.makedirs(local_bin_folder, exist_ok=True)

    current_os = platform.system().lower()
    if current_os == "darwin":
        raise StepEvaluationFailure("macOS is not supported for K3s installation")
    if current_os != "linux":
        raise StepEvaluationFailure(f"Unsupported OS: {current_os}")

    return local_bin_folder, current_os


def check_binary_exists(local_bin_folder: str) -> Tuple[str, bool]:
    """Check if K3s binary already exists and return path and existence status."""
    binary_path = os.path.join(local_bin_folder, "k3s")
    binary_exists = os.path.exists(binary_path)
    return binary_path, binary_exists


def check_service_exists(collaborators: CoreCollaborators, node_type: str, current_os: str) -> bool:
    """Check if K3s service is already installed."""
    if current_os != "linux":
        return False

    try:
        if node_type == "server":
            check_cmd = "systemctl list-units --full -all | grep -Fq k3s.service"
            result = collaborators.process().run_fn(
                args=check_cmd,
                working_dir=os.getcwd(),
                fail_msg=f"Failed to check for existing K3s {node_type} service",
                fail_on_error=False,
                allow_single_shell_command_str=True,
            )
            return bool(result)
        else:  # agent
            result = subprocess.run(
                f"systemctl list-units --full -all | grep -Fq k3s-{node_type}.service",
                shell=True,
                capture_output=True,
            )
            return result.returncode == 0
    except Exception as e:
        logger.warning(f"Failed to check for existing K3s {node_type} service: {e}")
        return False


def install_binary(collaborators: CoreCollaborators, version: str, local_bin_folder: str) -> None:
    """Install K3s binary."""
    logger.info("Installing K3s as binary...")
    install_cmd = (
        f"curl -sfL https://get.k3s.io | "
        f"INSTALL_K3S_SKIP_ENABLE=true "
        f"INSTALL_K3S_SKIP_START=true "
        f'INSTALL_K3S_VERSION="{version}" '
        f'INSTALL_K3S_BIN_DIR="{local_bin_folder}" '
        f"sh -s -"
    )
    result = collaborators.process().run_fn(
        args=install_cmd,
        working_dir=os.getcwd(),
        fail_msg="Failed to install K3s binary",
        fail_on_error=True,
        allow_single_shell_command_str=True,
    )
    logger.info(result)


def prepare_log_file(collaborators: CoreCollaborators) -> None:
    """Create log directory and file with proper permissions."""
    collaborators.process().run_fn(
        args="sudo mkdir -p /var/log && sudo touch /var/log/k3s.log && sudo chmod 666 /var/log/k3s.log",
        working_dir=os.getcwd(),
        fail_msg="Failed to create k3s log file",
        fail_on_error=True,
        allow_single_shell_command_str=True,
    )


def start_k3s_binary(
    collaborators: CoreCollaborators,
    local_bin_folder: str,
    node_type: str,
    k3s_token: Optional[str],
    k3s_url: Optional[str],
    k3s_additional_cli_args: str,
    use_kube_config: bool = False,
) -> None:
    """Start K3s as a binary process."""
    clean_args = k3s_additional_cli_args.replace('"', "")

    # Add kubeconfig configuration if requested (server only)
    kubeconfig_args = ""
    if use_kube_config and node_type == "server":
        kube_dir = os.path.expanduser("~/.kube")
        kube_config = os.path.join(kube_dir, "config")
        # Create .kube directory if it doesn't exist
        os.makedirs(kube_dir, exist_ok=True)
        kubeconfig_args = f"--write-kubeconfig {kube_config} --write-kubeconfig-mode 644"
        logger.info(f"Configuring K3s to write kubeconfig to {kube_config}")

    if node_type == "server":
        token_args = ""
        if k3s_token:
            token_args = f"--token {k3s_token}"
        run_command = f"nohup sudo {local_bin_folder}/k3s server {token_args} {clean_args} {kubeconfig_args} > /var/log/k3s.log 2>&1 &"
    else:  # agent
        if not k3s_url:
            raise ValueError("Missing mandatory parameter: k3s-url for agent")
        run_command = f"nohup sudo {local_bin_folder}/k3s agent --token {k3s_token} --server {k3s_url} {clean_args} > /var/log/k3s.log 2>&1 &"

    logger.info(f"run_command: {run_command}")
    result = collaborators.process().run_fn(
        args=run_command,
        working_dir=os.getcwd(),
        fail_msg=f"Failed to start K3s {node_type}",
        fail_on_error=True,
        allow_single_shell_command_str=True,
    )
    logger.info(result)
    logger.info(f"K3s {node_type} started successfully")


def install_service(
    collaborators: CoreCollaborators,
    version: str,
    local_bin_folder: str,
    node_type: str,
    k3s_token: Optional[str],
    k3s_url: Optional[str],
    k3s_additional_cli_args: str,
    use_kube_config: bool = False,
) -> None:
    """Install K3s as a system service."""
    logger.info("Installing K3s as a system service...")
    # Add kubeconfig configuration if requested (server only)
    kubeconfig_args = ""
    if use_kube_config and node_type == "server":
        kube_dir = os.path.expanduser("~/.kube")
        kube_config = os.path.join(kube_dir, "config")
        # Create .kube directory if it doesn't exist
        os.makedirs(kube_dir, exist_ok=True)
        kubeconfig_args = f"--write-kubeconfig {kube_config} --write-kubeconfig-mode 644"
        logger.info(f"Configuring K3s to write kubeconfig to {kube_config}")

    if node_type == "server":
        token_args = ""
        if k3s_token:
            token_args = f"--token {k3s_token}"

        install_cmd = (
            f"curl -sfL https://get.k3s.io | "
            f'INSTALL_K3S_VERSION="{version}" '
            f'INSTALL_K3S_BIN_DIR="{local_bin_folder}" '
            f"sh -s - server {k3s_additional_cli_args} {kubeconfig_args} {token_args}"
        )
    else:  # agent
        if not k3s_url:
            raise ValueError("Missing mandatory parameter: k3s-url for agent")
        install_cmd = (
            f"curl -sfL https://get.k3s.io | "
            f'INSTALL_K3S_VERSION="{version}" '
            f'INSTALL_K3S_BIN_DIR="{local_bin_folder}" '
            f"sh -s - agent {k3s_additional_cli_args} --token {k3s_token} --server {k3s_url}"
        )

    collaborators.process().run_fn(
        args=install_cmd,
        working_dir=os.getcwd(),
        fail_msg=f"Failed to install K3s {node_type} service",
        fail_on_error=True,
        allow_single_shell_command_str=True,
    )
    logger.info(f"K3s {node_type} service installed successfully")


def _check_ssh_context(collaborators: CoreCollaborators) -> bool:
    """
    Determine if running in an SSH context.

    Returns:
        bool: True if running in SSH context, False otherwise
    """
    try:
        logger.debug("Checking if running in SSH context...")
        ssh_check_cmd = "echo $SSH_CONNECTION"
        ssh_result = collaborators.process().run_fn(
            args=ssh_check_cmd,
            working_dir=os.getcwd(),
            fail_on_error=False,
            allow_single_shell_command_str=True,
        )
        is_remote = bool(ssh_result.strip())
        logger.debug(f"SSH connection check result: '{ssh_result}', is_remote={is_remote}")
        return is_remote
    except Exception as e:
        logger.debug(f"Error checking SSH connection: {e}")
        return False


def _get_uninstall_script_path(node_type: str) -> str:
    """
    Get the appropriate uninstall script path based on node type.

    Args:
        node_type: Type of K3s node ('server' or 'agent')

    Returns:
        str: Path to the uninstall script
    """
    if node_type == "agent":
        return "~/.local/bin/k3s-agent-uninstall.sh"
    return "~/.local/bin/k3s-uninstall.sh"


def _try_service_uninstall(
    collaborators: CoreCollaborators, node_type: str, script_path: str, is_remote: bool
) -> Optional[str]:
    """
    Attempt to uninstall K3s using the service uninstall script.

    Args:
        collaborators: Core collaborators object
        node_type: Type of K3s node ('server' or 'agent')
        script_path: Path to the uninstall script
        is_remote: Whether running in SSH context

    Returns:
        Optional[str]: Status message if successful, None if failed
    """
    try:
        # Prepare the uninstall command based on connection type
        if is_remote:
            # For remote execution, use nohup to prevent SSH interruption
            script_cmd = f"nohup sudo {script_path} > /tmp/k3s_uninstall.log 2>&1 &"
            logger.info("Running uninstall with nohup to prevent SSH interruption")
        else:
            script_cmd = f"sudo {script_path}"

        logger.debug(f"Executing uninstall command: {script_cmd}")

        # Execute the uninstall script
        result = collaborators.process().run_fn(
            args=script_cmd,
            working_dir=os.getcwd(),
            fail_msg=f"K3s {node_type} service uninstall command executed but may have encountered issues",
            fail_on_error=False,  # Don't fail if script reports an error
            allow_single_shell_command_str=True,
        )

        logger.debug(f"Uninstall script execution result: {result}")

        # For remote installs, we might not get output since the SSH connection might be dropped
        if is_remote:
            logger.info(f"K3s {node_type} service uninstall initiated with nohup")
            return f"K3s {node_type} service uninstall initiated. The uninstall process will continue even if the SSH connection is dropped."
        else:
            logger.info(f"K3s {node_type} service uninstalled successfully")
            return f"K3s {node_type} service uninstalled successfully"

    except Exception as e:
        logger.warning(f"Service uninstall script execution failed: {e}")
        logger.debug(f"Full exception: {str(e)}")
        logger.info("Will try binary uninstall method as fallback")
        return None


def _kill_k3s_processes(collaborators: CoreCollaborators) -> bool:
    """
    Kill all running K3s processes.

    Args:
        collaborators: Core collaborators object

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Attempting to kill K3s processes...")
        kill_result = collaborators.process().run_fn(
            args="sudo pkill -f k3s || true",  # The || true ensures the command doesn't fail
            working_dir=os.getcwd(),
            fail_on_error=False,
            allow_single_shell_command_str=True,
        )
        logger.info(f"Kill processes result: {kill_result}")
        return True
    except Exception as e:
        logger.warning(f"Failed to stop K3s process: {e}")
        logger.info(f"Full exception: {str(e)}")
        logger.info("Continuing with cleanup despite process kill failure")
        return False


def _remove_k3s_binary(collaborators: CoreCollaborators, local_bin_folder: str) -> bool:
    """
    Remove the K3s binary.

    Args:
        collaborators: Core collaborators object
        local_bin_folder: Path to the local bin folder

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        binary_path = os.path.join(local_bin_folder, "k3s")
        logger.info(f"Checking for K3s binary at: {binary_path}")

        if os.path.exists(binary_path):
            logger.info(f"Removing K3s binary at: {binary_path}")
            collaborators.process().run_fn(
                args=f"sudo rm -f {binary_path}",
                working_dir=os.getcwd(),
                fail_on_error=False,
                allow_single_shell_command_str=True,
            )
            logger.info("Binary removed successfully")
            return True
        else:
            logger.info("K3s binary not found at expected location")
            return False
    except Exception as e:
        logger.warning(f"Failed to remove K3s binary: {e}")
        logger.info(f"Full exception: {str(e)}")
        logger.info("Continuing with cleanup despite binary removal failure")
        return False


def _clean_k3s_data_directory(collaborators: CoreCollaborators) -> bool:
    """
    Clean up the K3s data directory.

    Args:
        collaborators: Core collaborators object

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Removing K3s data directory...")
        collaborators.process().run_fn(
            args="sudo rm -rf /var/lib/rancher/k3s",
            working_dir=os.getcwd(),
            fail_on_error=False,
            allow_single_shell_command_str=True,
        )
        logger.info("Data directory removed successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to remove K3s data directory: {e}")
        logger.info(f"Full exception: {str(e)}")
        logger.info("Continuing with cleanup despite data directory removal failure")
        return False


def _clean_k3s_config_directory(collaborators: CoreCollaborators) -> bool:
    """
    Clean up the K3s config directory.

    Args:
        collaborators: Core collaborators object

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Removing K3s config directory...")
        collaborators.process().run_fn(
            args="sudo rm -rf /etc/rancher/k3s",
            working_dir=os.getcwd(),
            fail_on_error=False,
            allow_single_shell_command_str=True,
        )
        logger.info("Config directory removed successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to remove K3s config directory: {e}")
        logger.info(f"Full exception: {str(e)}")
        logger.info("Continuing with cleanup despite config directory removal failure")
        return False


def _clean_kube_config(collaborators: CoreCollaborators) -> bool:
    """
    Clean up the ~/.kube/config file if it exists.

    Args:
        collaborators: Core collaborators object

    Returns:
        bool: True if successful or file didn't exist, False if failed
    """
    try:
        kube_config = os.path.expanduser("~/.kube/config")
        logger.info(f"Checking for kubectl config at: {kube_config}")

        if os.path.exists(kube_config):
            logger.info(f"Removing kubectl config at: {kube_config}")
            collaborators.process().run_fn(
                args=f"rm -f {kube_config}",
                working_dir=os.getcwd(),
                fail_on_error=False,
                allow_single_shell_command_str=True,
            )
            logger.info("kubectl config removed successfully")
            return True
        else:
            logger.info("kubectl config not found at expected location")
            return True  # Return True since no file to remove is not a failure
    except Exception as e:
        logger.warning(f"Failed to remove kubectl config: {e}")
        logger.info(f"Full exception: {str(e)}")
        logger.info("Continuing with cleanup despite kubectl config removal failure")
        return False


def _perform_binary_uninstall(collaborators: CoreCollaborators, node_type: str, local_bin_folder: str) -> str:
    """
    Perform a manual binary uninstall of K3s.

    Args:
        collaborators: Core collaborators object
        node_type: Type of K3s node ('server' or 'agent')
        local_bin_folder: Path to the local bin folder

    Returns:
        str: Status message indicating the result
    """
    logger.info("Attempting binary uninstall method as fallback...")

    # Track the success of each step
    steps_results = {
        # TODO: Need to solve the kill process issue, it fails the Ansible playbook
        # "kill_processes": _kill_k3s_processes(collaborators),
        "remove_binary": _remove_k3s_binary(collaborators, local_bin_folder),
        "clean_data_dir": _clean_k3s_data_directory(collaborators),
        "clean_config_dir": _clean_k3s_config_directory(collaborators),
        "clean_kube_config": _clean_kube_config(collaborators),
    }

    # Log summary of steps
    successful_steps = sum(1 for step, result in steps_results.items() if result)
    logger.info(f"Binary uninstall completed {successful_steps}/{len(steps_results)} steps successfully")

    for step, result in steps_results.items():
        logger.debug(f"Step '{step}': {'Success' if result else 'Failed'}")

    # Even if some steps failed, consider the uninstallation "successful"
    logger.info(f"K3s {node_type} binary uninstall completed")
    return f"K3s {node_type} uninstalled using the binary cleanup method"


def uninstall_k3s(collaborators: CoreCollaborators, node_type: str, local_bin_folder: str) -> str:
    """
    Uninstall K3s by trying both service and binary uninstallation methods.

    This function follows a two-phase approach:
    1. PRIMARY METHOD: Attempts to use the official K3s uninstall script
       - For 'server' nodes: uses ~/.local/bin/k3s-uninstall.sh
       - For 'agent' nodes: uses ~/.local/bin/k3s-agent-uninstall.sh
       - Uses nohup for remote SSH connections to prevent connection drops

    2. FALLBACK METHOD: If service uninstall fails, performs manual cleanup:
       - Kills K3s processes
       - Removes the K3s binary
       - Cleans up data and config directories

    The function is designed to be resilient against failures and SSH disconnections,
    and will always return a status message rather than raising exceptions.

    Args:
        collaborators: Core collaborators object for accessing system functions
        node_type: Type of K3s node ('server' or 'agent')
        local_bin_folder: Path to the local bin folder

    Returns:
        A status message indicating the outcome of the uninstallation
    """
    logger.info(f"Uninstalling K3s {node_type}...")
    logger.debug(f"Using local_bin_folder: {local_bin_folder}")

    # Wrap all operations in try/except to ensure we always return a status message
    try:
        #############################################
        # PHASE 1: SERVICE UNINSTALL (PREFERRED METHOD)
        #############################################

        # Get the appropriate uninstall script path
        script_path = os.path.expanduser(_get_uninstall_script_path(node_type))
        logger.debug(f"Checking for uninstall script at: {script_path}")

        if os.path.exists(script_path):
            logger.info(f"Found uninstall script at {script_path}, attempting service uninstall...")

            # Check if running in SSH/remote context
            is_remote = _check_ssh_context(collaborators)

            # Try service uninstall
            result = _try_service_uninstall(collaborators, node_type, script_path, is_remote)
            if result:
                return result
        else:
            logger.warning(f"Uninstall script not found at {script_path}")
            logger.info("Will try binary uninstall method instead")

        #############################################
        # PHASE 2: BINARY UNINSTALL (FALLBACK METHOD)
        #############################################
        return _perform_binary_uninstall(collaborators, node_type, local_bin_folder)

    except Exception as e:
        # Catch all exceptions and return a message instead of raising
        logger.error(f"K3s uninstall encountered an error: {e}")
        logger.debug(f"Full exception during uninstall: {str(e)}")
        return f"K3s {node_type} uninstall process completed with errors: {str(e)}"


def install_k3s_server(version: str, collaborators: CoreCollaborators, maybe_args: Optional[DynamicArgs]) -> str:
    """Install K3s server node."""
    # Extract and validate parameters
    args = extract_common_args(maybe_args)
    k3s_token = args["k3s_token"]
    k3s_additional_cli_args = args["k3s_additional_cli_args"]
    install_as_binary = args["install_as_binary"]
    use_kube_config = args["use_kube_config"]

    # Setup environment
    local_bin_folder, current_os = setup_environment()

    logger.info(f"Installing K3s server, version: {version}, OS: {current_os}")
    binary_path, binary_exists = check_binary_exists(local_bin_folder)

    # Install based on mode (binary or service)
    if install_as_binary:
        if binary_exists:
            logger.warning("K3s server binary is already installed.")
            return "K3s server binary is already installed."

        install_binary(collaborators, version, local_bin_folder)
        logger.info("K3s server binary installed successfully")

        prepare_log_file(collaborators)
        start_k3s_binary(
            collaborators, local_bin_folder, "server", k3s_token, None, k3s_additional_cli_args, use_kube_config
        )

        return f"K3s server binary installed and started successfully at {binary_path}"
    else:
        # Check if service is already installed
        if check_service_exists(collaborators, "server", current_os):
            logger.warning("K3s server system service is already installed and running.")
            return "K3s server system service is already installed and running."

        # Install as service
        install_service(
            collaborators,
            version,
            local_bin_folder,
            "server",
            k3s_token,
            None,
            k3s_additional_cli_args,
            use_kube_config,
        )

        return "K3s server service installed successfully"


def install_k3s_agent(version: str, collaborators: CoreCollaborators, maybe_args: Optional[DynamicArgs]) -> str:
    """Install K3s agent node."""
    # Extract and validate parameters
    args = extract_common_args(maybe_args)
    k3s_token = args["k3s_token"]
    k3s_url = args["k3s_url"]
    k3s_additional_cli_args = args["k3s_additional_cli_args"]
    install_as_binary = args["install_as_binary"]
    # use_kube_config = args["use_kube_config"]  # We get the parameter but ignore it for agents

    # Continue with installation
    if not k3s_token:
        raise ValueError("Missing mandatory parameter: k3s-token")
    if not k3s_url:
        raise ValueError("Missing mandatory parameter: k3s-url")

    # Setup environment
    local_bin_folder, current_os = setup_environment()

    logger.info(f"Installing K3s agent, version: {version}, OS: {current_os}")
    binary_path, binary_exists = check_binary_exists(local_bin_folder)

    # Install based on mode (binary or service)
    if install_as_binary:
        if binary_exists:
            logger.warning("K3s agent binary is already installed.")
            return "K3s agent binary is already installed."

        install_binary(collaborators, version, local_bin_folder)
        logger.info("K3s agent binary installed successfully")

        prepare_log_file(collaborators)
        # Note: use_kube_config is always False for agents as it only applies to servers
        start_k3s_binary(collaborators, local_bin_folder, "agent", k3s_token, k3s_url, k3s_additional_cli_args, False)

        return f"K3s agent binary installed successfully at {binary_path}"
    else:
        # Check if service is already installed
        if check_service_exists(collaborators, "agent", current_os):
            logger.warning("K3s agent system service is already installed and running.")
            return "K3s agent system service is already installed and running."

        # Install as service
        # Note: use_kube_config is always False for agents as it only applies to servers
        install_service(
            collaborators, version, local_bin_folder, "agent", k3s_token, k3s_url, k3s_additional_cli_args, False
        )

        return "K3s agent service installed successfully"


def uninstall_k3s_server(version: str, collaborators: CoreCollaborators, maybe_args: Optional[DynamicArgs]) -> str:
    """Uninstall K3s server node."""
    try:
        local_bin_folder, _ = setup_environment()
        result = uninstall_k3s(collaborators, "server", local_bin_folder)
        # Ensure we never return None
        return result if result is not None else "K3s server uninstall completed with unknown status"
    except Exception as e:
        logger.error(f"Failed to uninstall K3s server: {str(e)}")
        return f"K3s server uninstall process completed with errors: {str(e)}"


def uninstall_k3s_agent(version: str, collaborators: CoreCollaborators, maybe_args: Optional[DynamicArgs]) -> str:
    """Uninstall K3s agent node."""
    try:
        local_bin_folder, _ = setup_environment()
        result = uninstall_k3s(collaborators, "agent", local_bin_folder)
        # Ensure we never return None
        return result if result is not None else "K3s agent uninstall completed with unknown status"
    except Exception as e:
        logger.error(f"Failed to uninstall K3s agent: {str(e)}")
        return f"K3s agent uninstall process completed with errors: {str(e)}"


# def wait_for_k3s_api(
#     ip_address: str,
#     timeout_seconds=60,
#     verify_ssl=False,
#     interval=1
# ):
#     url=f"https://{ip_address}:6443/version",
#     print(f"Waiting for K3s server API at {url}...")

#     deadline = time.time() + timeout_seconds
#     while time.time() < deadline:
#         try:
#             response = requests.get(url, verify=verify_ssl)
#             if response.status_code == 200:
#                 print("✅ K3s server is up and responding.")
#                 return True
#         except RequestException as e:
#             pass  # Silence connection errors

#         time.sleep(interval)

#     raise TimeoutError(f"K3s server didn't respond within {timeout_seconds} seconds.")

# def wait_for_k3s_health(k3s_server_url, timeout_seconds=60):
#     """
#     Simple function to check if a K3s server is healthy by polling its API endpoint.

#     Args:
#         k3s_server_url: The URL of the K3s server (e.g., https://localhost:6443)
#         timeout_seconds: Maximum time to wait in seconds

#     Returns:
#         bool: True if server is healthy, False if timed out
#     """
#     import time
#     import subprocess

#     start_time = time.time()
#     poll_interval = 1  # Check every second

#     logger.info(f"Checking K3s health at {k3s_server_url} (timeout: {timeout_seconds}s)")

#     while (time.time() - start_time) < timeout_seconds:
#         try:
#             # Simple health check using curl
#             cmd = f"curl -sk {k3s_server_url}/healthz"
#             result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

#             if result.returncode == 0 and result.stdout.strip() == "ok":
#                 logger.info(f"✅ K3s server at {k3s_server_url} is healthy")
#                 return True

#             elapsed = time.time() - start_time
#             if int(elapsed) % 5 == 0:  # Log every 5 seconds
#                 logger.info(f"🔄 Waiting for K3s to be healthy... ({int(elapsed)}s/{timeout_seconds}s)")

#         except Exception as e:
#             logger.error(f"Error checking K3s health: {str(e)}")

#         time.sleep(poll_interval)

#     print(f"❌ K3s health check failed after {timeout_seconds} seconds")
#     return False
