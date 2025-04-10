#!/usr/bin/env python3

import os
import platform
import subprocess
from loguru import logger
from typing import Optional

from provisioner_installers_plugin.src.installer.domain.dynamic_args import DynamicArgs

from provisioner_shared.components.runtime.shared.collaborators import CoreCollaborators


def install_k3s_server(version: str, collaborators: CoreCollaborators, maybe_args: Optional[DynamicArgs]) -> str:
    # Extract parameters from dynamic args
    dynamic_args_dict = maybe_args.as_dict()
    k3s_token = dynamic_args_dict.get("k3s-token")
    k3s_additional_cli_args: str = dynamic_args_dict.get("k3s-args", "")
    install_as_binary = dynamic_args_dict.get("install-as-binary", False)
    
    # Validate mandatory parameters
    if not k3s_token:
        raise ValueError("Missing mandatory parameter: k3s_token")
    
    # Set up local bin folder path
    local_bin_folder = os.path.expanduser("~/.local/bin")
    os.makedirs(local_bin_folder, exist_ok=True)
    
    # Detect OS
    current_os = platform.system().lower()
    if current_os not in ["linux", "darwin"]:
        raise ValueError(f"Unsupported OS: {current_os}")
    
    # Check for binary installation if on macOS
    if current_os == "darwin" and not install_as_binary:
        raise ValueError("Installing K3s as a system service on macOS is not supported (use --install-as-binary)")
    
    logger.info(f"Installing K3s server, version: {version}, OS: {current_os}")
    
    # Check if binary is already installed
    binary_path = os.path.join(local_bin_folder, "k3s")
    binary_exists = os.path.exists(binary_path)
    
    # Install based on mode (binary or service)
    if install_as_binary:
        if binary_exists:
            logger.warning("K3s server binary is already installed.")
            return "K3s server binary is already installed."
        
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
            fail_msg="Failed to install K3s server binary",
            fail_on_error=True,
            allow_single_shell_command_str=True
        )
        logger.info(result)
        logger.info("K3s server binary installed successfully")

        k3s_additional_cli_args = k3s_additional_cli_args.replace("\"", "")
        # Allow 'pi' user to use sudo without password
        # RUN usermod -aG sudo pi && echo 'pi ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/pi
        # Create log directory and file with proper permissions first
        collaborators.process().run_fn(
            args="sudo mkdir -p /var/log && sudo touch /var/log/k3s.log && sudo chmod 666 /var/log/k3s.log",
            working_dir=os.getcwd(),
            fail_msg="Failed to create k3s log file",
            fail_on_error=True,
            allow_single_shell_command_str=True
        )
        run_command = f"nohup sudo {local_bin_folder}/k3s server --token {k3s_token} {k3s_additional_cli_args} > /var/log/k3s.log 2>&1 &"
        logger.info("run_command:")
        logger.info(run_command)
        result = collaborators.process().run_fn(
            args=run_command,
            working_dir=os.getcwd(),
            fail_msg="Failed to start K3s server",
            fail_on_error=True,
            allow_single_shell_command_str=True
        )
        logger.info(result)
        logger.info("K3s server started successfully")

        return f"K3s server binary installed and started successfully at {binary_path}"
    else:
        # Check if service is already installed (Linux only)
        if current_os == "linux":
            try:
                result = collaborators.process().run_fn(
                    args="systemctl list-units --full -all | grep -Fq k3s.service",
                    working_dir=os.getcwd(),
                    fail_msg="Failed to check for existing K3s service",
                    fail_on_error=True,
                    allow_single_shell_command_str=True
                )
                
                if result:
                    logger.warning("K3s server system service is already installed and running.")
                    return "K3s server system service is already installed and running."
            except Exception as e:
                logger.warning(f"Failed to check for existing K3s service: {e}")
        
        # Install as service
        install_cmd = (
            f"curl -sfL https://get.k3s.io | "
            f"INSTALL_K3S_VERSION=\"{version}\" "
            f"INSTALL_K3S_BIN_DIR=\"{local_bin_folder}\" "
            f"sh -s - {k3s_additional_cli_args} --token {k3s_token}"
        )
        
        result = collaborators.process().run_fn(
            args=install_cmd,
            working_dir=os.getcwd(),
            fail_msg="Failed to install K3s server service",
            fail_on_error=True,
            allow_single_shell_command_str=True
        )
        
        logger.info("K3s server service installed successfully")
        return "K3s server service installed successfully"


def install_k3s_agent(version: str, collaborators: CoreCollaborators, maybe_args: Optional[DynamicArgs]) -> str:
    # Extract parameters from dynamic args
    dynamic_args_dict = maybe_args.as_dict()
    k3s_token = dynamic_args_dict.get("k3s-token")
    k3s_url = dynamic_args_dict.get("k3s-url")
    k3s_additional_cli_args = dynamic_args_dict.get("k3s-args", "")
    install_as_binary = dynamic_args_dict.get("install-as-binary", False)
    
    # Validate mandatory parameters
    if not k3s_token:
        raise ValueError("Missing mandatory parameter: k3s-token")
    if not k3s_url:
        raise ValueError("Missing mandatory parameter: k3s-url")
    
    # Set up local bin folder path
    local_bin_folder = os.path.expanduser("~/.local/bin")
    os.makedirs(local_bin_folder, exist_ok=True)
    
    # Detect OS
    current_os = platform.system().lower()
    if current_os not in ["linux", "darwin"]:
        raise ValueError(f"Unsupported OS: {current_os}")
    
    # Check for binary installation if on macOS
    if current_os == "darwin" and not install_as_binary:
        raise ValueError("Installing K3s as a system service on macOS is not supported (use --install-as-binary)")
    
    logger.info(f"Installing K3s agent, version: {version}, OS: {current_os}")
    
    # Check if binary is already installed
    binary_path = os.path.join(local_bin_folder, "k3s")
    binary_exists = os.path.exists(binary_path)
    
    # Install based on mode (binary or service)
    if install_as_binary:
        if binary_exists:
            logger.warning("K3s agent binary is already installed.")
            return "K3s agent binary is already installed."
        
        # Install as binary
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
            fail_msg="Failed to install K3s agent binary",
            fail_on_error=True,
            allow_single_shell_command_str=True
        )
        logger.info(result)
        logger.info("K3s agent binary installed successfully")

        k3s_additional_cli_args = k3s_additional_cli_args.replace("\"", "")
        # Allow 'pi' user to use sudo without password
        # RUN usermod -aG sudo pi && echo 'pi ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/pi
        # Create log directory and file with proper permissions first
        collaborators.process().run_fn(
            args="sudo mkdir -p /var/log && sudo touch /var/log/k3s.log && sudo chmod 666 /var/log/k3s.log",
            working_dir=os.getcwd(),
            fail_msg="Failed to create k3s log file",
            fail_on_error=True,
            allow_single_shell_command_str=True
        )
        run_command = f"nohup sudo {local_bin_folder}/k3s agent --token {k3s_token} --server {k3s_url} {k3s_additional_cli_args} > /var/log/k3s.log 2>&1 &"
        logger.info("run_command:")
        logger.info(run_command)
        result = collaborators.process().run_fn(
            args=run_command,
            working_dir=os.getcwd(),
            fail_msg="Failed to start K3s agent",
            fail_on_error=True,
            allow_single_shell_command_str=True
        )
        logger.info(result)
        logger.info("K3s agent started successfully")
        
        return f"K3s agent binary installed successfully at {binary_path}"
    else:
        # Check if service is already installed (Linux only)
        if current_os == "linux":
            try:
                result = subprocess.run(
                    "systemctl list-units --full -all | grep -Fq k3s-agent.service", 
                    shell=True, 
                    capture_output=True
                )
                service_exists = result.returncode == 0
                
                if service_exists:
                    logger.warning("K3s agent system service is already installed and running.")
                    return "K3s agent system service is already installed and running."
            except Exception as e:
                logger.warning(f"Failed to check for existing K3s agent service: {e}")
        
        # Install as service
        install_cmd = (
            f"curl -sfL https://get.k3s.io | "
            f"INSTALL_K3S_VERSION=\"{version}\" "
            f"INSTALL_K3S_BIN_DIR=\"{local_bin_folder}\" "
            f"sh -s - {k3s_additional_cli_args} --token {k3s_token} --server {k3s_url}"
        )
        
        result = collaborators.process().run_fn(
            args=install_cmd,
            working_dir=os.getcwd(),
            fail_msg="Failed to install K3s agent service",
            fail_on_error=True,
            allow_single_shell_command_str=True
        )
        
        logger.info("K3s agent service installed successfully")
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