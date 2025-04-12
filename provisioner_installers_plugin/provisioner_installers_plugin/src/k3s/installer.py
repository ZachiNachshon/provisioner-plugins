#!/usr/bin/env python3

import os
import platform
import subprocess
from loguru import logger
from typing import Optional, Dict, Tuple, Any

from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs
from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators


def extract_common_args(dynamic_args: Optional[DynamicArgs]) -> Dict[str, Any]:
    """Extract common arguments from dynamic args."""
    dynamic_args_dict = dynamic_args.as_dict() if dynamic_args else {}
    return {
        "k3s_token": dynamic_args_dict.get("k3s-token"),
        "k3s_additional_cli_args": dynamic_args_dict.get("k3s-args", ""),
        "install_as_binary": dynamic_args_dict.get("install-as-binary", False),
        "k3s_url": dynamic_args_dict.get("k3s-url")
    }


def setup_environment() -> Tuple[str, str]:
    """Set up environment and return local_bin_folder and current_os."""
    local_bin_folder = os.path.expanduser("~/.local/bin")
    os.makedirs(local_bin_folder, exist_ok=True)
    
    current_os = platform.system().lower()
    if current_os == "darwin":
        raise ValueError("macOS is not supported for K3s installation")
    if current_os != "linux":
        raise ValueError(f"Unsupported OS: {current_os}")
        
    return local_bin_folder, current_os


def check_binary_exists(local_bin_folder: str) -> Tuple[str, bool]:
    """Check if K3s binary already exists and return path and existence status."""
    binary_path = os.path.join(local_bin_folder, "k3s")
    binary_exists = os.path.exists(binary_path)
    return binary_path, binary_exists


def check_service_exists(collaborators: CoreCollaborators, service_name: str, current_os: str) -> bool:
    """Check if K3s service is already installed."""
    if current_os != "linux":
        return False
        
    try:
        if service_name == "server":
            check_cmd = "systemctl list-units --full -all | grep -Fq k3s.service"
            result = collaborators.process().run_fn(
                args=check_cmd,
                working_dir=os.getcwd(),
                fail_msg=f"Failed to check for existing K3s {service_name} service",
                fail_on_error=True,
                allow_single_shell_command_str=True
            )
            return bool(result)
        else:  # agent
            result = subprocess.run(
                f"systemctl list-units --full -all | grep -Fq k3s-{service_name}.service", 
                shell=True, 
                capture_output=True
            )
            return result.returncode == 0
    except Exception as e:
        logger.warning(f"Failed to check for existing K3s {service_name} service: {e}")
        return False


def install_binary(
    collaborators: CoreCollaborators, 
    version: str, 
    local_bin_folder: str
) -> None:
    """Install K3s binary."""
    install_cmd = (
        f"curl -sfL https://get.k3s.io | "
        f"INSTALL_K3S_SKIP_ENABLE=true "
        f"INSTALL_K3S_SKIP_START=true "
        f"INSTALL_K3S_VERSION=\"{version}\" "
        f"INSTALL_K3S_BIN_DIR=\"{local_bin_folder}\" "
        f"sh -s -"
    )
    result = collaborators.process().run_fn(
        args=install_cmd,
        working_dir=os.getcwd(),
        fail_msg="Failed to install K3s binary",
        fail_on_error=True,
        allow_single_shell_command_str=True
    )
    logger.info(result)


def prepare_log_file(collaborators: CoreCollaborators) -> None:
    """Create log directory and file with proper permissions."""
    collaborators.process().run_fn(
        args="sudo mkdir -p /var/log && sudo touch /var/log/k3s.log && sudo chmod 666 /var/log/k3s.log",
        working_dir=os.getcwd(),
        fail_msg="Failed to create k3s log file",
        fail_on_error=True,
        allow_single_shell_command_str=True
    )


def start_k3s_binary(
    collaborators: CoreCollaborators,
    local_bin_folder: str, 
    node_type: str,
    k3s_token: str,
    k3s_url: Optional[str],
    k3s_additional_cli_args: str
) -> None:
    """Start K3s as a binary process."""
    clean_args = k3s_additional_cli_args.replace("\"", "")
    
    if node_type == "server":
        run_command = f"nohup sudo {local_bin_folder}/k3s server --token {k3s_token} {clean_args} > /var/log/k3s.log 2>&1 &"
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
        allow_single_shell_command_str=True
    )
    logger.info(result)
    logger.info(f"K3s {node_type} started successfully")


def install_service(
    collaborators: CoreCollaborators,
    version: str,
    local_bin_folder: str,
    node_type: str,
    k3s_token: str,
    k3s_url: Optional[str],
    k3s_additional_cli_args: str
) -> None:
    """Install K3s as a system service."""
    if node_type == "server":
        install_cmd = (
            f"curl -sfL https://get.k3s.io | "
            f"INSTALL_K3S_VERSION=\"{version}\" "
            f"INSTALL_K3S_BIN_DIR=\"{local_bin_folder}\" "
            f"sh -s - {k3s_additional_cli_args} --token {k3s_token}"
        )
    else:  # agent
        if not k3s_url:
            raise ValueError("Missing mandatory parameter: k3s-url for agent")
        install_cmd = (
            f"curl -sfL https://get.k3s.io | "
            f"INSTALL_K3S_VERSION=\"{version}\" "
            f"INSTALL_K3S_BIN_DIR=\"{local_bin_folder}\" "
            f"sh -s - {k3s_additional_cli_args} --token {k3s_token} --server {k3s_url}"
        )
    
    result = collaborators.process().run_fn(
        args=install_cmd,
        working_dir=os.getcwd(),
        fail_msg=f"Failed to install K3s {node_type} service",
        fail_on_error=True,
        allow_single_shell_command_str=True
    )
    logger.info(f"K3s {node_type} service installed successfully")


def install_k3s_server(version: str, collaborators: CoreCollaborators, maybe_args: Optional[DynamicArgs]) -> str:
    """Install K3s server node."""
    # Extract and validate parameters
    args = extract_common_args(maybe_args)
    k3s_token = args["k3s_token"]
    k3s_additional_cli_args = args["k3s_additional_cli_args"]
    install_as_binary = args["install_as_binary"]
    
    if not k3s_token:
        raise ValueError("Missing mandatory parameter: k3s_token")
    
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
            collaborators, 
            local_bin_folder, 
            "server", 
            k3s_token, 
            None, 
            k3s_additional_cli_args
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
            k3s_additional_cli_args
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
        start_k3s_binary(
            collaborators, 
            local_bin_folder, 
            "agent", 
            k3s_token, 
            k3s_url, 
            k3s_additional_cli_args
        )
        
        return f"K3s agent binary installed successfully at {binary_path}"
    else:
        # Check if service is already installed
        if check_service_exists(collaborators, "agent", current_os):
            logger.warning("K3s agent system service is already installed and running.")
            return "K3s agent system service is already installed and running."
        
        # Install as service
        install_service(
            collaborators, 
            version, 
            local_bin_folder, 
            "agent", 
            k3s_token, 
            k3s_url, 
            k3s_additional_cli_args
        )
        
        return "K3s agent service installed successfully"


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