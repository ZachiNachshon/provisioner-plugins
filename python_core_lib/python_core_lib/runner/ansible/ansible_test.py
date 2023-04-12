#!/usr/bin/env python3

import os
import unittest

from python_core_lib.errors.cli_errors import InvalidAnsibleHostPair
from python_core_lib.infra.context import Context
from python_core_lib.runner.ansible.ansible_runner import (
    AnsibleHost,
    AnsiblePlaybook,
    AnsibleRunnerLocal,
)
from python_core_lib.test_lib.assertions import Assertion
from python_core_lib.utils.io_utils import IOUtils
from python_core_lib.utils.io_utils_fakes import FakeIOUtils
from python_core_lib.utils.paths import Paths

#
# To run these directly from the terminal use:
#  poetry run coverage run -m pytest python_core_lib/runner/ansible/ansible_test.py
#
ANSIBLE_PLAYBOOK_TEST_PATH = "/ansible/playbook/path"

ANSIBLE_DUMMY_PLAYBOOK_CONTENT = """
---
- name: Test Dummy Playbook
  hosts: selected_hosts
  gather_facts: no
  environment:
    DRY_RUN: True
    VERBOSE: True
    # SILENT: True

  roles:
    - role: {ansible_playbooks_path}/roles/hello_world
      tags: ['hello']
"""

ANSIBLE_DUMMY_PLAYBOOK_NAME = "dummy_playbook"
ANSIBLE_DUMMY_PLAYBOOK = AnsiblePlaybook(name=ANSIBLE_DUMMY_PLAYBOOK_NAME, content=ANSIBLE_DUMMY_PLAYBOOK_CONTENT)

ANSIBLE_HOSTS = [
    AnsibleHost(
        host="localhost",
        ip_address="ansible_connection=local",
        username="test-user",
        password="test-pass",
    )
]

ANSIBLE_VAR_1 = "key1=value1"
ANSIBLE_VAR_2 = "key2=value2"
ANSIBLE_VARIABLES = [ANSIBLE_VAR_1, ANSIBLE_VAR_2]

ANSIBLE_TAG_1 = "test_tag_1"
ANSIBLE_TAG_2 = "test_tag_2"
ANSIBLE_TAGS = [ANSIBLE_TAG_1, ANSIBLE_TAG_2]


class AnsibleRunnerTestShould(unittest.TestCase):
    def test_run_ansible_fail_on_invalid_host_ip_pair(self):
        ctx = Context.create(dry_run=False, verbose=True, auto_prompt=True)
        Assertion.expect_raised_failure(
            self,
            ex_type=InvalidAnsibleHostPair,
            method_to_run=lambda: AnsibleRunnerLocal.create(
                ctx=ctx,
                io_utils=FakeIOUtils.create(ctx),
                paths=Paths.create(ctx),
            ).run_fn(
                selected_hosts=[AnsibleHost("localhost", None)],
                playbook=ANSIBLE_DUMMY_PLAYBOOK,
            ),
        )

    def test_run_ansible_dry_run_flow(self):
        ctx = Context.create(dry_run=True, verbose=True, auto_prompt=True)
        Assertion.expect_outputs(
            self,
            method_to_run=lambda: AnsibleRunnerLocal.create(
                ctx=ctx, io_utils=IOUtils.create(ctx), paths=Paths.create(ctx)
            ).run_fn(
                selected_hosts=ANSIBLE_HOSTS,
                playbook=ANSIBLE_DUMMY_PLAYBOOK,
                ansible_vars=ANSIBLE_VARIABLES,
                ansible_tags=ANSIBLE_TAGS,
            ),
            expected=[
                ANSIBLE_DUMMY_PLAYBOOK_NAME,
                "name: Test Dummy Playbook",
                "hosts: selected_hosts",
                "role: DRY_RUN_RESPONSE/roles/hello_world",
                "tags: ['hello']",
                f"ansible-playbook -i {os.path.expanduser('~/.config/provisioner/ansible/hosts')} DRY_RUN_RESPONSE -e local_bin_folder='~/.local/bin' -e {ANSIBLE_VAR_1} -e {ANSIBLE_VAR_2} --tags {ANSIBLE_TAG_1},{ANSIBLE_TAG_2} -vvvv",
            ],
        )
