#!/bin/bash

CURRENT_FOLDER_ABS_PATH=$(dirname "${BASH_SOURCE[0]}")
ROOT_FOLDER_ABS_PATH=$(dirname "${CURRENT_FOLDER_ABS_PATH}")

source "${ROOT_FOLDER_ABS_PATH}/external/shell_scripts_lib/logger.sh"
source "${ROOT_FOLDER_ABS_PATH}/external/shell_scripts_lib/io.sh"

VERSION=0.1.0
PROVISIONER_TARBALL_NAME="provisioner_examples_plugin-${VERSION}.tar.gz"

build_sdist_tarball()  {
  log_info "Build a tarball package with local Python distribution"
  # poetry build -f sdist -vvv || exit
  poetry build -f sdist || exit
}

prerequisites() {
  # Update lock file changes
  log_info "Updating changes to the Poetry lock file"
  poetry lock
}

main() {
  local cwd=$(pwd)

  prerequisites
  build_sdist_tarball

  local pip_tarball_folder_path=$(mktemp -d "${TMPDIR:-/tmp}/provisioner_examples_plugin.XXXXXX")

  log_info "Copy provisioner tarball. path: ${pip_tarball_folder_path}"
  mv "dist/${PROVISIONER_TARBALL_NAME}" "${pip_tarball_folder_path}"

  cd "${pip_tarball_folder_path}" || exit
  
  log_info "Installing provisioners plugin/library as pip package from tarball..."
  python3 -m pip install "${pip_tarball_folder_path}/${PROVISIONER_TARBALL_NAME}"
  
  cd "${cwd}" || exit
}

main "$@"