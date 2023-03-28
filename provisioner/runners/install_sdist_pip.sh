#!/bin/bash

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ROOT_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")

source "${ROOT_FOLDER_ABS_PATH}/external/shell_scripts_lib/logger.sh"
source "${ROOT_FOLDER_ABS_PATH}/external/shell_scripts_lib/io.sh"

BINARY_NAME="provisioner"
BINARY_PATH="${HOME}/.local/bin"
VERSION=0.1.0
PROVISIONER_TARBALL_NAME="provisioner-${VERSION}.tar.gz"
PIP_PKG_FOLDER_PATH="${HOME}/.config/provisioner/.pip-pkg"
DEV_LAUNCHER_FILEPATH="runners/local_bin/provisioner-pip"

build_sdist_tarball()  {
  log_info "Build a tarball package with local Python distribution"
  # build-project is a custom Poetry plugin that builds sibling sub-modules
  poetry build-project -f sdist || exit
  # poetry build -f sdist -vvv || exit
  # poetry build -f sdist || exit
}

prepare_pip_pkg_folder() {
  if is_directory_exist "${PIP_PKG_FOLDER_PATH}"; then
    log_info "Clearing previous installed Python distribution"
    rm -rf "${PIP_PKG_FOLDER_PATH}"
  fi
  mkdir -p "${PIP_PKG_FOLDER_PATH}"
}

copy_pip_pkg_tarball() {
  log_info "Copy provisioner tarball"
  mv "dist/${PROVISIONER_TARBALL_NAME}" "${PIP_PKG_FOLDER_PATH}"
}

install_provisioner_launcher_binary() {
  if ! is_directory_exist "${BINARY_PATH}"; then
    log_info "Creating local bin folder (${BINARY_PATH})"
    mkdir -p "${BINARY_PATH}"
  fi

  log_info "Copy provisioner binary. path: ${BINARY_PATH}/${BINARY_NAME}"
  cp "${DEV_LAUNCHER_FILEPATH}" "${BINARY_PATH}/${BINARY_NAME}"
}

pip_install_provisioner() {
  cd "${PIP_PKG_FOLDER_PATH}" || exit
  log_info "Installing provisioners pip package from tarball..."
  pip3 install "${PROVISIONER_TARBALL_NAME}"
}

pip_install_all_dependencies() {
  # Create a virtual environment and install the project's dependencies.
  poetry install
  # Create a requirements.txt file in the project directory 
  # that lists all the dependencies needed by the project
  poetry export \
    -f requirements.txt \
    --without dev \
    --without-urls \
    --without-hashes \
    --output requirements.txt

  # Install Poetry into pip to avoid error - ModuleNotFoundError: No module named 'poetry'
  pip3 install -U poetry

  # Install all the packages listed in the requirements.txt file 
  # in the virtual environment or globally
  pip3 install -r requirements.txt
}

unpack_pip_pkg() {
  local cwd=$(pwd)
  cd "${PIP_PKG_FOLDER_PATH}" || exit
  log_info "Unpacking archive..."
  tar -xf "${PROVISIONER_TARBALL_NAME}"
  mv provisioner-${VERSION} provisioner
  cd "${cwd}" || exit
}

generate_launcher_script() {
  local cwd=$(pwd)
  cd "${PIP_PKG_FOLDER_PATH}" || exit
  log_info "Creating development scripts..."
  echo "#!/usr/bin/env python3

from provisioner.main import main

main()
" >> provisioner/dev.py

  log_info "Elevating execution permissions"
  chmod +x provisioner/dev.py
  cd "${cwd}" || exit
}

prerequisites() {
  # Update lock file changes
  poetry lock
}

create_dev_pip_package() {
  build_sdist_tarball
  prepare_pip_pkg_folder
  copy_pip_pkg_tarball
  unpack_pip_pkg
}

create_dev_launcher() {
  install_provisioner_launcher_binary
  generate_launcher_script
}

main() {
  local cwd=$(pwd)

  prerequisites
  create_dev_pip_package
  create_dev_launcher
  pip_install_provisioner
  
  # pip_install_all_dependencies

  cd "${cwd}" || exit
}

main "$@"