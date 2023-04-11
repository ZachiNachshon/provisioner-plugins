#!/bin/bash

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ROOT_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")

source "${ROOT_FOLDER_ABS_PATH}/logger.sh"
source "${ROOT_FOLDER_ABS_PATH}/io.sh"
source "${ROOT_FOLDER_ABS_PATH}/cmd.sh"
source "${ROOT_FOLDER_ABS_PATH}/strings.sh"
source "${ROOT_FOLDER_ABS_PATH}/checks.sh"

SCRIPT_MENU_TITLE="Poetry pip Installer"

CLI_ARGUMENT_PACKAGE_TYPE=""       # sdist/wheel/dev
CLI_FLAG_IS_PLUGIN=""              # true/false if missing
CLI_FLAG_DELETE=""                 # true/false if missing
CLI_FLAG_FORCE_INSTALL_DEPS=""     # true/false if missing

CLI_VALUE_PACKAGE_TYPE=""

POETRY_PACKAGE_NAME=""
POETRY_PACKAGE_VERSION=""

DEV_BINARY_PATH="${HOME}/.local/bin"

is_dev_package_type() {
  [[ "${CLI_VALUE_PACKAGE_TYPE}" == "dev" ]]
}

is_wheel_package_type() {
  [[ "${CLI_VALUE_PACKAGE_TYPE}" == "wheel" ]]
}

is_sdist_package_type() {
  [[ "${CLI_VALUE_PACKAGE_TYPE}" == "sdist" ]]
}

is_plugin() {
  [[ -n "${CLI_FLAG_IS_PLUGIN}" ]]
}

is_delete() {
  [[ -n "${CLI_FLAG_DELETE}" ]]
}

is_force_install_deps() {
  [[ -n "${CLI_FLAG_FORCE_INSTALL_DEPS}" ]]
}

get_escaped_package_path() {
  echo "${POETRY_PACKAGE_NAME}" | xargs | tr '-' '_'
}

get_sdist_name() {
  local escaped_pkg_name=$(get_escaped_package_path)
  echo "${escaped_pkg_name}-${POETRY_PACKAGE_VERSION}.tar.gz"
}

get_dev_pip_pkg_path() {
  echo "${HOME}/.config/${POETRY_PACKAGE_NAME}/.pip-pkg"
}

dev_prepare_pip_pkg_folder() {
  local dev_pip_pkg_path=$(get_dev_pip_pkg_path)
  if is_dry_run || is_directory_exist "${dev_pip_pkg_path}"; then
    log_info "Clearing previous locally installed Python distribution"
    cmd_run "rm -rf ${dev_pip_pkg_path}"
  fi
  cmd_run "mkdir -p ${dev_pip_pkg_path}"
}

dev_copy_pip_pkg_tarball() {
  local sdist_name=$(get_sdist_name)
  local dev_pip_pkg_path=$(get_dev_pip_pkg_path)

  log_info "Copy local pip package sdist tarball"
  cmd_run "mv dist/${sdist_name} ${dev_pip_pkg_path}"
}

dev_unpack_pip_pkg_tarball() {
  local sdist_name=$(get_sdist_name)
  local dev_pip_pkg_path=$(get_dev_pip_pkg_path)
  local cwd=$(pwd)

  if ! is_dry_run; then
    cd "${dev_pip_pkg_path}" || exit
  fi

  log_info "Unpacking local sdist pip package archive..."
  cmd_run "tar -xf ${sdist_name}"

  # Rename the sdist root folder from <package-name>-<version> to <package-name>
  cmd_run "mv ${POETRY_PACKAGE_NAME}-${POETRY_PACKAGE_VERSION} ${POETRY_PACKAGE_NAME}"

  if ! is_dry_run; then
    cd "${cwd}" || exit
  fi
}

dev_generate_launcher_script() {
  local escaped_pkg_name=$(get_escaped_package_path)
  local escaped_pkg_name_upper=$(to_upper "${escaped_pkg_name}")
  cat << EOF
#!/usr/bin/env python3
import os
import sys

"""
This file is used as a command launcher for ${POETRY_PACKAGE_NAME} private installation.
"""
def get_pkg_target_path():
    """
    Content of .pip-pkg folder is the extraction of pip wheel/sdist:
    .
    ├── ${escaped_pkg_name}
    │   ├── LICENSE
    │   ├── PKG-INFO
    │   ├── ${escaped_pkg_name}
    │   │   ├── ...
    │   │   └── <poetry-included-files-and-folders>
    │   └── setup.py
    └── ${escaped_pkg_name}-${POETRY_PACKAGE_VERSION}.tar.gz
    """
    return os.environ.get(
        "${escaped_pkg_name_upper}_PKG_PATH",  # used only for testing - DO NOT OVERRIDE
        os.path.expanduser(os.path.join("~", ".config", "${POETRY_PACKAGE_NAME}", ".pip-pkg", "${POETRY_PACKAGE_NAME}"))
    )


def launch(pkg_path: str):
    # Add the custom installation directory to PYTHONPATH so the modules are found
    sys.path = [pkg_path] + sys.path
    cwd = os.getcwd()
    try:
        os.chdir(pkg_path)
        from ${escaped_pkg_name}.main import main
        main()
        os.chdir(cwd)
    except ModuleNotFoundError:
        print("The '${escaped_pkg_name}' package could not be found. "
              "Please refer to the docs for installation instructions and troubleshooting")
        os.chdir(cwd)
        exit(2)


if __name__ == '__main__':
    launch(pkg_path=get_pkg_target_path())
EOF
}

dev_install_launcher_binary() {
  local dev_launch_script=$1

  if ! is_directory_exist "${DEV_BINARY_PATH}"; then
    log_info "Creating local bin folder (${DEV_BINARY_PATH})"
    cmd_run "mkdir -p ${DEV_BINARY_PATH}"
  fi

  local binary_path="${DEV_BINARY_PATH}/${POETRY_PACKAGE_NAME}"
  if is_dry_run; then
    log_info "\n\n${dev_launch_script}\n"
  else
    log_info "Copy ${POETRY_PACKAGE_NAME} binary. path: ${binary_path}"
    echo "${dev_launch_script}" > "${binary_path}"
  fi

  log_info "Elevating execution permissions"
  cmd_run "chmod +x ${binary_path}"
}

install_dev_local_pip_package() {
  dev_prepare_pip_pkg_folder
  dev_copy_pip_pkg_tarball
  dev_unpack_pip_pkg_tarball

  if is_plugin; then
    log_warning "Python libraries does not support an executable dev launcher script"
  else
    local dev_launch_script=$(dev_generate_launcher_script "${POETRY_PACKAGE_NAME}")
    dev_install_launcher_binary "${dev_launch_script}"
  fi
}

delete_dev_local_pip_package() {
  local dev_pip_pkg_path=$(get_dev_pip_pkg_path)
  if is_dry_run || is_directory_exist "${dev_pip_pkg_path}"; then
    log_info "Clearing locally installed Python distribution"
    cmd_run "rm -rf ${dev_pip_pkg_path}"
  else
    log_info "No locally installed Python distribution could be found"
  fi

  local binary_path="${DEV_BINARY_PATH}/${POETRY_PACKAGE_NAME}"
  if is_dry_run || ([[ -n ${POETRY_PACKAGE_NAME} ]] && is_file_exist "${binary_path}"); then
    log_info "Clearing locally installed Python binary"
    cmd_run "rm -rf ${binary_path}"
  else
    log_info "No locally installed Python binary could be found"
  fi 
}

install_pip_package_from_sdist() {
  local cwd=$(pwd)
  local sdist_filename=$(get_sdist_name)
  local pip_tarball_folder_path=""

  if ! is_dry_run; then
    pip_tarball_folder_path=$(mktemp -d "${TMPDIR:-/tmp}/${POETRY_PACKAGE_NAME}.XXXXXX")
  else
    pip_tarball_folder_path="/dry/run/dummy/path"
  fi 

  log_info "Copy sdist tarball. path: ${pip_tarball_folder_path}"
  cmd_run "mv dist/${sdist_filename} ${pip_tarball_folder_path}"

  if ! is_dry_run; then
    cd "${pip_tarball_folder_path}" || exit
  fi
  
  log_info "Installing pip package from sdist tarball..."
  cmd_run "python3 -m pip install ${pip_tarball_folder_path}/${sdist_filename} --no-python-version-warning --disable-pip-version-check"
  
  if ! is_dry_run; then
    cd "${cwd}" || exit
    # Clear temporary folder
    if [[ -n "${POETRY_PACKAGE_NAME}" ]]; then
      cmd_run "rm -rf ${pip_tarball_folder_path}"
    fi
  fi
}

delete_pip_package_from_sdist() {
  log_info "Uninstalling pip package. name: ${POETRY_PACKAGE_NAME}"
  cmd_run "python3 -m pip uninstall ${POETRY_PACKAGE_NAME} -y"
}

install_pip_package_from_wheel() {
  log_fatal "Installing a pip wheel is not yet supported"
}

delete_pip_package_from_wheel() {
  log_fatal "Uninstalling a pip wheel is not yet supported"
}

build_sdist_tarball()  {
  local build_cmd=""

  if [[ -n "${CLI_FLAG_IS_PLUGIN}" ]]; then
    log_info "Build a local Python source distribution ${COLOR_YELLOW}library${COLOR_NONE} (sdist tarball)"
    build_cmd="poetry build -f sdist"
  else
    log_info "Build a local Python source distribution ${COLOR_YELLOW}executable${COLOR_NONE} (sdist tarball)"
    build_cmd="poetry build-project -f sdist"
  fi

  if is_verbose; then
    build_cmd+=" -vv"
  fi
  
  cmd_run "${build_cmd} || exit"
}

maybe_force_install_deps() {
  if is_force_install_deps; then
    pip_install_all_dependencies
  fi
}

build_wheel_package() {
  log_fatal "Building pip wheel not supported yet"
}

build_pip_package() {
  if is_sdist_package_type; then
    build_sdist_tarball
  elif is_wheel_package_type; then
    build_wheel_package
  elif is_dev_package_type; then
    build_sdist_tarball
  else
    log_fatal "Invalid package type. value: ${CLI_VALUE_PACKAGE_TYPE}"
  fi
}

install_pip_package() {
  if is_dev_package_type; then
    install_dev_local_pip_package
  elif is_sdist_package_type; then
    install_pip_package_from_sdist
    maybe_force_install_deps
  elif is_wheel_package_type; then
    install_pip_package_from_wheel
    maybe_force_install_deps
  fi
}

delete_pip_package() {
  if is_dev_package_type; then
    delete_dev_local_pip_package
  elif is_sdist_package_type; then
    delete_pip_package_from_sdist
  elif is_wheel_package_type; then
    delete_pip_package_from_wheel
  fi
}

resolve_project_name_version() {
  # POETRY_PACKAGE_NAME="provisioner"
  # POETRY_PACKAGE_VERSION="0.0.0"

  # if ! is_dry_run; then
  local poetry_project_info=$(cmd_run "poetry version")
  local poetry_project_info=$(poetry version --no-ansi)
  local name_ver_array=(${poetry_project_info})
  POETRY_PACKAGE_NAME=$(printf ${name_ver_array[0]})
  POETRY_PACKAGE_VERSION=$(printf ${name_ver_array[1]})
  # fi
}

pip_install_all_dependencies() {
  log_info "Installing all non-dev project dependencies to pip"

  # Create a virtual environment and install the project's dependencies.
  cmd_run "poetry install"

  # Create a requirements.txt file in the project directory 
  # that lists all the dependencies needed by the project
  cmd_run """poetry export \
    -f requirements.txt \
    --without dev \
    --without-urls \
    --without-hashes \
    --output requirements.txt"""

  # Install Poetry into pip to avoid error - ModuleNotFoundError: No module named 'poetry'
  cmd_run "pip3 install -U poetry"

  # Install all the packages listed in the requirements.txt file 
  # in the virtual environment or globally
  cmd_run "pip3 install -r requirements.txt"
}

print_help_menu_and_exit() {
  local exec_filename=$1
  local file_name=$(basename "${exec_filename}")
  echo -e ""
  echo -e "${SCRIPT_MENU_TITLE} - Build, install and release a pip package"
  echo -e " "
  echo -e "${COLOR_WHITE}USAGE${COLOR_NONE}"
  echo -e "  "${file_name}" [command] [option] [flag]"
  echo -e " "
  echo -e "${COLOR_WHITE}ARGUMENTS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}package-type${COLOR_NONE} <option>     Type of the pip package [${COLOR_GREEN}options: sdist/wheel/dev${COLOR_NONE}]"
  echo -e " "
  echo -e "${COLOR_WHITE}FLAGS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}--delete${COLOR_NONE}                  Delete a previously installed package"
  echo -e "  ${COLOR_LIGHT_CYAN}--force-install-deps${COLOR_NONE}      Force install all dependencies to pip"
  echo -e "  ${COLOR_LIGHT_CYAN}--plugin${COLOR_NONE}                  Build a non-executable library package"
  echo -e "  ${COLOR_LIGHT_CYAN}-y${COLOR_NONE} (--auto-prompt)        Do not prompt for approval and accept everything"
  echo -e "  ${COLOR_LIGHT_CYAN}-d${COLOR_NONE} (--dry-run)            Run all commands in dry-run mode without file system changes"
  echo -e "  ${COLOR_LIGHT_CYAN}-v${COLOR_NONE} (--verbose)            Output debug logs for commands executions"
  echo -e "  ${COLOR_LIGHT_CYAN}-s${COLOR_NONE} (--silent)             Do not output logs for commands executions"
  echo -e "  ${COLOR_LIGHT_CYAN}-h${COLOR_NONE} (--help)               Show available actions and their description"
  echo -e " "
  echo -e "${COLOR_WHITE}GLOBALS${COLOR_NONE}"
  echo -e "  ${COLOR_LIGHT_CYAN}PYPI_TOKEN${COLOR_NONE}                Valid PyPI token with write access for publishing releases"
  echo -e " "
  exit 0
}

parse_program_arguments() {
  if [ $# = 0 ]; then
    print_help_menu_and_exit "$0"
  fi

  while [[ "$#" -gt 0 ]]; do
    case "$1" in
      package-type*)
        CLI_ARGUMENT_PACKAGE_TYPE="package-type"
        CLI_VALUE_PACKAGE_TYPE=$(cut -d = -f 2- <<<"${1}" | xargs)
        shift
        ;;
      --delete*)
        CLI_FLAG_DELETE="true"
        shift
        ;;
      --force-install-deps*)
        CLI_FLAG_FORCE_INSTALL_DEPS="true"
        shift
        ;;
      --plugin*)
        CLI_FLAG_IS_PLUGIN="true"
        shift
        ;;
      -d | --dry-run)
        # Used by logger.sh
        export LOGGER_DRY_RUN="true"
        shift
        ;;
      -y | --auto-prompt)
        # Used by prompter.sh
        export PROMPTER_SKIP_PROMPT="y"
        shift
        ;;
      -v | --verbose)
        # Used by logger.sh
        export LOGGER_VERBOSE="true"
        shift
        ;;
      -s | --silent)
        # Used by logger.sh
        export LOGGER_SILENT="true"
        shift
        ;;
      -h | --help)
        print_help_menu_and_exit "$0"
        ;;
      *)
        log_fatal "Unknown option $1 (did you mean =$1 ?)"
        ;;
    esac
  done
}

check_invalid_package_type_value() {
  # If command is empty and its value is empty or invalid - not valid
  [[ -z "${CLI_ARGUMENT_PACKAGE_TYPE}" ]] ||
    # If options are not part of the valid values
    [[ -n "${CLI_ARGUMENT_PACKAGE_TYPE}" && (
      "${CLI_VALUE_PACKAGE_TYPE}" != "sdist" &&
      "${CLI_VALUE_PACKAGE_TYPE}" != "dev" &&
      "${CLI_VALUE_PACKAGE_TYPE}" != "wheel") ]]
}

verify_program_arguments() {
  if check_invalid_package_type_value; then
    log_fatal "Argument 'package-type' is missing a mandatory option. options: sdist/wheel"
  fi
  evaluate_dry_run_mode
}

prerequisites() {
  check_tool "poetry"

  if ! is_delete; then
    # Update lock file changes
    log_info "Updating changes to the Poetry lock file"
    cmd_run "poetry lock"
  fi
}

get_script_name() {
  local file_name=$(basename "${exec_filename}")
  # Return filename without extension
  echo "${file_name%.*}"
}

main() {
  parse_program_arguments "$@"
  verify_program_arguments

  prerequisites
  resolve_project_name_version

  if is_delete; then
    delete_pip_package
  else
    build_pip_package
    install_pip_package
  fi
}

main "$@"
