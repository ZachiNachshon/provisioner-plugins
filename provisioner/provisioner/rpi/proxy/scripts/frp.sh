#!/bin/bash

source ./utils/logger.sh
source ./utils/checks.sh
source ./utils/docker.sh
source ./utils/props.sh
source ./utils/network.sh
source ./utils/envs.sh
source ./utils/browser.sh
source ./rpi/proxy/.env

start_proxy_server() {
  local image_tag=$1
  local server_name=$2
  local client_server_token=$3

#  local server_local_address=$(read_network_address)
  local server_local_address=$(property rpi.proxy.frp.server.bind.address)
  local server_port=$(property rpi.proxy.frp.server.bind.port)
  local kcp_port=$(property rpi.proxy.frp.server.kcp.port)
  local udp_port=$(property rpi.proxy.frp.server.udp.port)

  local dashboard_port=$(property rpi.proxy.frp.server.dashboard.port)
  local dashboard_user=$(env_var SECRET_RPI_PROXY_FRP_DASHBOARD_USER)
  local dashboard_pass=$(env_var SECRET_RPI_PROXY_FRP_DASHBOARD_PASSWORD)

  log_info "Stopping any running frp servers..."
  clean_container "${server_name}"

  # `--network=host` means the docker container run on host network
#  docker run -d --network=host \
  log_info "Starting a fresh frp server..."
#  docker run -itd --name "${server_name}" \
#        -v ${PWD}/rpi/proxy/config_test/frps.ini:/etc/frp/frps.ini:ro \
#        -v ${PWD}/rpi/proxy/logs:/etc/frp/logs/ \
#        -p 7000:7000 \
#        -p 6000:6000 \
#        "${image_tag}"

  docker run -d \
      --name "${server_name}" \
      -v ${PWD}/rpi/proxy/config_test/frps.ini:/etc/frp/frps.ini:ro \
      -v ${PWD}/rpi/proxy/logs:/etc/frp/logs/ \
      -p 7000:7000 \
      -p 6000:6000 \
      "${image_tag}"
#      -e FRP_SERVER_ADDR="${server_local_address}" \
#      -e FRP_SERVER_PORT="${server_port}" \
#      -e FRP_KCP_PORT="${kcp_port}" \
#      -e FRP_UDP_PORT="${udp_port}" \
#      -e FRP_PRIVILEGE_TOKEN="${client_server_token}" \
#      -e FRP_DASHBOARD_PORT="${dashboard_port}" \
#      -e FRP_DASHBOARD_USR="${dashboard_user}" \
#      -e FRP_DASHBOARD_PWD="${dashboard_pass}" \
#      -p "${server_port}":"${server_port}" \
#      -p "${dashboard_port}":"${dashboard_port}" \

}

start_proxy_client() {
  local image_tag=$1
  local client_name=$2
  local client_server_token=$3

  local server_remote_address=$(property rpi.proxy.frp.server.remote.address)
  local server_port=$(property rpi.proxy.frp.server.bind.port)

  local admin_ui_port=$(property rpi.proxy.frp.client.admin.ui.port)
  local admin_ui_user=$(env_var SECRET_RPI_PROXY_FRP_CLIENT_ADMIN_USER)
  local admin_ui_pass=$(env_var SECRET_RPI_PROXY_FRP_CLIENT_ADMIN_PASSWORD)

  log_info "Stopping any running frp clients..."
  clean_container "${client_name}"

#  -e SERVER_ADDR=192.168.1.200 \
#     -e SERVER_PORT=7000 \
#     -e PROTO=tcp \
#     -e LOCAL_IP=127.0.0.1 \
#     -e LOCAL_PORT=22 \
#     -e REMOTE_PORT=6000 \
  log_info "Starting a fresh frp client..."
  docker run -itd --name "${client_name}" \
     -e MODE=client \
     -v ${PWD}/rpi/proxy/config_test/frpc.ini:/etc/frp/frpc.ini:ro \
     -v ${PWD}/rpi/proxy/logs:/etc/frp/logs/ \
     "${image_tag}"

#  docker run -d \
#      --name "${client_name}" \
#      -v ${PWD}/rpi/proxy/config/frpc.ini:/etc/frp/frpc.ini:ro \
#      -v ${PWD}/rpi/proxy/logs:/etc/frp/logs/ \
#      -e FRP_SERVER_ADDR="${server_remote_address}" \
#      -e FRP_SERVER_PORT="${server_port}" \
#      -e FRP_PRIVILEGE_TOKEN="${client_server_token}" \
#      -e FRP_CLIENT_ADMIN_UI_PORT="${admin_ui_port}" \
#      -e FRP_CLIENT_ADMIN_USER="${admin_ui_user}" \
#      -e FRP_CLIENT_ADMIN_PASS="${admin_ui_pass}" \
#      "${image_tag}"
}

prerequisites() {
  check_tool docker
  check_image anchor/frp
#  check_image anchor/heroku-cli
}

main() {
  action=$1

  local image_tag=$(property docker.frp.image.tag)
  local server_name=$(property rpi.proxy.frp.server.name)
  local client_name=$(property rpi.proxy.frp.client.name)
  local client_server_token=$(env_var SECRET_RPI_PROXY_FRP_CLIENT_SERVER_TOKEN)

  if [[ ${action} == "--run-server" ]]; then

    start_proxy_server "${image_tag}" "${server_name}" "${client_server_token}"

  elif [[ ${action} == "--log-server" ]]; then

    tail -f ${PWD}/rpi/proxy/logs/frps.log

  elif [[ ${action} == "--stop-server" ]]; then

    clean_container "${server_name}"

  elif [[ ${action} == "--check-server" ]]; then

    local server_remote_address=$(property rpi.proxy.frp.server.remote.address)
    local server_port=$(property rpi.proxy.frp.server.bind.port)
    curl --connect-timeout 3 --silent --show-error "http://${server_remote_address}:${server_port}/version"

  elif [[ ${action} == "--run-client" ]]; then

    start_proxy_client "${image_tag}" "${client_name}" "${client_server_token}"

  elif [[ ${action} == "--log-client" ]]; then

    tail -f ${PWD}/rpi/proxy/logs/frpc.log

  elif [[ ${action} == "--stop-client" ]]; then

    clean_container "${client_name}"

  elif [[ ${action} == "--client-open-admin-ui" ]]; then

    local client_local_address=$(read_network_address)
    local admin_ui_port=$(property rpi.proxy.frp.client.admin.ui.port)
    open_browser "http://${client_local_address}:${admin_ui_port}"

  elif [[ ${action} == "--server-open-dashboard" ]]; then

    local server_remote_address=$(property rpi.proxy.frp.server.remote.address)
    local dashboard_port=$(property rpi.proxy.frp.server.dashboard.port)
    open_browser "http://${server_remote_address}:${dashboard_port}"

  else
    log_fatal "Invalid action flag, supported flags: --run-server, --run-client."
  fi
}

main "$@"