#!/bin/bash

# Title         Provisioner Wrapper
# Author        Zachi Nachshon <zachi.nachshon@gmail.com>
# Supported OS  Linux & macOS
# Description   Run a Provisioner CLI command on local/remote host machine
#==========================================================================
CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")

export LOGGER_DRY_RUN=${DRY_RUN}
export LOGGER_VERBOSE=${VERBOSE}
export LOGGER_SILENT=${SILENT}

COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW="\033[0;33m"
COLOR_BLUE="\033[0;34m"
COLOR_PURPLE="\033[0;35m"
COLOR_LIGHT_CYAN='\033[0;36m'
COLOR_WHITE='\033[1;37m'
COLOR_NONE='\033[0m'

ICON_GOOD="${COLOR_GREEN}✔${COLOR_NONE}"
ICON_WARN="${COLOR_YELLOW}⚠${COLOR_NONE}"
ICON_BAD="${COLOR_RED}✗${COLOR_NONE}"

exit_on_error() {
  exit_code=$1
  message=$2
  if [ $exit_code -ne 0 ]; then
    #        >&1 echo "\"${message}\" command failed with exit code ${exit_code}."
    # >&1 echo "\"${message}\""
    exit $exit_code
  fi
}

is_verbose() {
  [[ -n "${LOGGER_VERBOSE}" ]]
}

is_silent() {
  [[ -n ${LOGGER_SILENT} ]]
}

is_dry_run() {
  [[ -n ${LOGGER_DRY_RUN} ]]
}

evaluate_run_mode() {
  if is_dry_run; then
    echo -e "${COLOR_YELLOW}Dry run: enabled${COLOR_NONE}" >&1
  fi

  if is_verbose; then
    echo -e "${COLOR_YELLOW}Verbose: enabled${COLOR_NONE}" >&1
  fi

  if is_silent; then
    echo -e "${COLOR_YELLOW}Silent: enabled${COLOR_NONE}" >&1
  fi

  new_line
}

_log_base() {
  prefix=$1
  shift
  echo -e "${prefix}$*" >&1
}

log_debug() {
  local debug_level_txt="DEBUG"
  if is_dry_run; then
    debug_level_txt+=" (Dry Run)"
  fi

  if ! is_silent && is_verbose; then
    _log_base "${COLOR_WHITE}${debug_level_txt}${COLOR_NONE}: " "$@"
  fi
}

log_info() {
  local info_level_txt="INFO"
  if is_dry_run; then
    info_level_txt+=" (Dry Run)"
  fi

  if ! is_silent; then
    _log_base "${COLOR_GREEN}${info_level_txt}${COLOR_NONE}: " "$@"
  fi
}

log_warning() {
  local warn_level_txt="WARNING"
  if is_dry_run; then
    warn_level_txt+=" (Dry Run)"
  fi

  if ! is_silent; then
    _log_base "${COLOR_YELLOW}${warn_level_txt}${COLOR_NONE}: " "$@"
  fi
}

log_error() {
  local error_level_txt="ERROR"
  if is_dry_run; then
    error_level_txt+=" (Dry Run)"
  fi
  _log_base "${COLOR_RED}${error_level_txt}${COLOR_NONE}: " "$@"
}

log_fatal() {
  local fatal_level_txt="ERROR"
  if is_dry_run; then
    fatal_level_txt+=" (Dry Run)"
  fi
  _log_base "${COLOR_RED}${fatal_level_txt}${COLOR_NONE}: " "$@"
  message="$@"
  exit_on_error 1 "${message}"
}

new_line() {
  echo -e "" >&1
}

log_indicator_good() {
  local error_level_txt=""
  if is_dry_run; then
    error_level_txt+=" (Dry Run)"
  fi
  if ! is_silent; then
    _log_base "${ICON_GOOD}${error_level_txt} " "$@"
  fi
}

log_indicator_warning() {
  local error_level_txt=""
  if is_dry_run; then
    error_level_txt+=" (Dry Run)"
  fi
  if ! is_silent; then
    _log_base "${ICON_WARN}${error_level_txt} " "$@"
  fi
}

log_indicator_bad() {
  local error_level_txt=""
  if is_dry_run; then
    error_level_txt+=" (Dry Run)"
  fi
  if ! is_silent; then
    _log_base "${ICON_BAD}${error_level_txt} " "$@"
  fi
}

is_tool_exist() {
  local name=$1
  [[ $(command -v "${name}") ]]
}

should_install_using_pip() {
  [[ "${ENV_INSTALL_METHOD}" == "pip" ]]
}

should_install_using_github_release() {
  [[ "${ENV_INSTALL_METHOD}" == "github-release" ]]
}

get_local_pip_pkg_path() {
  local pkg_name=$1
  echo "${ENV_LOCAL_PIP_PKG_FOLDER_PATH}/${pkg_name}"
}

is_file_exist() {
  local path=$1
  [[ -f "${path}" || $(is_symlink "${path}") ]]
}

is_symlink() {
  local abs_path=$1
  [[ -L "${abs_path}" ]]
}

is_directory_exist() {
  local path=$1
  [[ -d "${path}" ]]
}

#######################################
# Checks if local utility exists
# Globals:
#   None
# Arguments:
#   name - utility CLI name
# Usage:
#   is_tool_exist "kubectl"
#######################################
is_tool_exist() {
  local name=$1
  [[ $(command -v "${name}") ]]
}

#######################################
# Return OS type as plain string
# Globals:
#   OSTYPE
# Arguments:
#   None
# Usage:
#   read_os_type
#######################################
read_os_type() {
  if [[ "${OSTYPE}" == "linux"* ]]; then
    echo "linux"
  elif [[ "${OSTYPE}" == "darwin"* ]]; then
    echo "darwin"
  else
    echo "OS type is not supported. os: ${OSTYPE}"
  fi
}

#######################################
# Run a command from string
# Globals:
#   is_verbose - based on env var LOGGER_VERBOSE
#   is_dry_run - based on env var LOGGER_DRY_RUN
# Arguments:
#   cmd_string - shell command in string format
# Usage:
#   cmd_run "echo 'hello world'"
#######################################
cmd_run() {
  local cmd_string=$1
  if is_verbose; then
    echo """
    ${cmd_string}
  """ >&1
  fi
  if ! is_dry_run; then
    eval "${cmd_string}"
  fi
}

verify_mandatory_run_arguments() {
  if should_install_using_github_release; then
    if [[ -z "${ENV_GITHUB_OWNER}" ]]; then
        log_fatal "missing Ansible variable for GitHub release. name: github_owner"
    fi
    if [[ -z "${ENV_GITHUB_REPOSITORY}" ]]; then
        log_fatal "missing Ansible variable for GitHub release. name: github_repository"
    fi
  fi
}

verify_supported_os() {
  local os_type=$(read_os_type)
  if [[ "${os_type}" != "linux" && "${os_type}" != "darwin" ]]; then
    log_fatal "OS is not supported. type: ${os_type}"
  fi
}

github_download_release_asset() {
  local owner=$1  
  local repo=$2
  local tag_name=$3
  local asset_name=$4
  local dl_path=$5
  local token=$6

  local header=""
  if [[ -n "${token}" ]]; then
    header="-H \"Authorization: Bearer ${token}\""
  fi

  cwd=$(pwd)
  if [[ -n "${dl_path}" ]] && ! is_directory_exist "${dl_path}"; then
    cmd_run "mkdir -p ${dl_path}"
  fi

  if [[ -n "${dl_path}" ]]; then
    cmd_run "cd ${dl_path} || exit"
  fi

  local curl_flags="-LJO"
  if is_verbose; then
    curl_flags="-LJOv"
  fi

  # Get the release information
  release_info=$(cmd_run "curl ${curl_flags} ${header} https://api.github.com/repos/${owner}/${repo}/releases/tags/${tag_name}")

  # Get the asset ID
  asset_id=$(echo "${release_info}" | jq ".assets[] | select(.name == \"${asset_name}\") | .id")

  if ! is_dry_run && [[ -z "${asset_id}" ]]; then
    log_fatal "Failed to retrieve asset id from GitHub release. tag: ${tag_name}, asset_name: ${asset_name}"
  fi

  # Download the asset
  cmd_run "curl ${curl_flags} ${header} -H \"Accept: application/octet-stream\" https://api.github.com/repos/${repo}/releases/assets/${asset_id}"

  if [[ -n "${dl_path}" ]]; then
    cmd_run "cd ${cwd} || exit"
  fi
}

uninstall_via_pip() {
  local pkg_name=$1
  local pkg_version=$2
  log_debug "Uninstalling pip package. name: ${pkg_name}"
  cmd_run "python3 -m pip uninstall --yes ${pkg_name}"
}

install_via_github_release() {
  local pkg_name=$1
  local pkg_version=$2
  local asset_name="${pkg_name}.tar.gz"

  local pkg_folder_path=$(get_local_pip_pkg_path "${pkg_name}")
  if is_directory_exist "${pkg_folder_path}"; then
    log_debug "Removing local pip pkg. path: ${pkg_folder_path}"
    cmd_run "rm -rf ${pkg_folder_path}"
  fi

  log_debug "Downloading a GitHub release. dest: ${pkg_folder_path}"
  github_download_release_asset \
    "${ENV_GITHUB_OWNER}" \
    "${ENV_GITHUB_REPOSITORY}" \
    "${ENV_PROVISIONER_VERSION}" \
    "${asset_name}" \
    "${pkg_folder_path}" \
    "${ENV_GIT_ACCESS_TOKEN}"

  if is_dry_run || is_file_exist "${pkg_folder_path}/${asset_name}"; then
    uninstall_via_pip "${pkg_name}" "${pkg_version}"
    log_debug "Installing from GitHub release. name: ${asset_name}, version: ${pkg_version}"
    cmd_run "python3 -m pip install ${pkg_folder_path}/${asset_name} --no-python-version-warning --disable-pip-version-check"
  else
    log_fatal "Cannot find downloaded package asset to install. path: ${pkg_folder_path}/${asset_name}"
  fi
}

install_via_pip() {
  local pkg_name=$1
  local pkg_version=$2

  uninstall_via_pip "${pkg_name}" "${pkg_version}"

  log_debug "Installing from pip registry. name: ${pkg_name}, version: ${pkg_version}"
  cmd_run "python3 -m pip install ${pkg_name}==${pkg_version} --no-python-version-warning --disable-pip-version-check"
}

pip_get_package_version() {
  local pkg_name=$1
  local version="DUMMY_VER"
  if ! is_dry_run; then
    version=$(python3 -m pip show "${pkg_name}" --no-color --no-python-version-warning --disable-pip-version-check | grep -i '^Version:' | awk '{print $2}')
  fi
  echo "${version}"
}

is_pip_installed() {
  local pkg_name=$1
  log_debug "Checking if installed from pip. name: ${pkg_name}"
  cmd_run "python3 -m pip list --no-color --no-python-version-warning --disable-pip-version-check | grep -w ${pkg_name} | head -1 > /dev/null"
}

install_package() {
  local pkg_name=$1
  local pkg_version=$2

  if should_install_using_pip; then
    install_via_pip "${pkg_name}" "${pkg_version}"
  elif should_install_using_github_release; then
    install_via_github_release "${pkg_name}" "${pkg_version}"
  else
    log_fatal "Install method is not supported. name: ${ENV_INSTALL_METHOD}"
  fi
}

install_or_update() {
  local pkg_name=$1
  local pkg_version=$2

  if ! is_pip_installed "${pkg_name}"; then
    log_debug "Pip package is not installed. name: ${pkg_name}"
    install_package "${pkg_name}" "${pkg_version}"
  else
    log_debug "Trying to read pip package version. name: ${pkg_name}"
    local current_version=$(pip_get_package_version "${pkg_name}")
    if [[ "${current_version}" == "${ENV_PROVISIONER_VERSION}" ]]; then
      log_debug "Found installed pip package with expected version. name: ${pkg_name}, version: ${pkg_version}"
    else
      log_debug "Pip package does not have the expected version. name: ${pkg_name}, current_version: ${current_version}, expected: ${pkg_version}"
      install_package "${pkg_name}" "${pkg_version}"
    fi
  fi
}

install_provisioner_engine() {
  # Install Provisioner Engine
  install_or_update "${ENV_PROVISIONER_BINARY}" "${ENV_PROVISIONER_VERSION}"

  # Only provisioner tool should be available as a binary, it is the engine that runs other plugins
  if is_tool_exist "${ENV_PROVISIONER_BINARY}"; then
    log_debug "Found installed binary. name: ${ENV_PROVISIONER_BINARY}, path: $(which "${ENV_PROVISIONER_BINARY}")"
  else
    log_fatal "The ${ENV_PROVISIONER_BINARY} binary is not installed as a global command"
  fi
}

install_provisioner_plugins() {
  # Install Required Plugins using array of tuple items:
  #   ['provisioner_examples_plugin:0.1.0', 'provisioner_installers_plugin:0.2.0']

  # Remove the square brackets and split the string into an array
  required_plugins=("${ENV_REQUIRED_PLUGINS//[\[\]]/}")

  log_debug "Installing required plugins: ${ENV_REQUIRED_PLUGINS}"

  for plugin in "${required_plugins[@]}"; do
      # Remove the single quotes from each element
      plugin="${plugin//\'}"
      # Extract name
      plugin_name=$(cut -d : -f -1 <<<"${plugin}" | xargs)
      # Extract version
      plugin_version=$(cut -d : -f 2- <<<"${plugin}" | xargs)
      install_or_update "${plugin_name}" "${plugin_version}"
  done
}

main() {
  evaluate_run_mode
  verify_supported_os
  verify_mandatory_run_arguments

  install_provisioner_engine
  install_provisioner_plugins

  if is_verbose; then
    new_line
    echo "========= Running ${ENV_PROVISIONER_BINARY} Command =========" >&1
  fi
  cmd_run "${ENV_PROVISIONER_COMMAND}"

  # log_info "Printing menu:"
  # "${ENV_PROVISIONER_BINARY}"
}

main "$@"
