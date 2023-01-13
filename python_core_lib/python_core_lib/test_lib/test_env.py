#!/usr/bin/env python3

from python_core_lib.infra.context import Context
from python_core_lib.shared.collaborators_fakes import FakeCoreCollaborators
from python_core_lib.utils.os import MAC_OS, OsArch

ROOT_PATH_TEST_ENV = "/test/env/root"

class TestEnv:
    # Skip pytest warning for mot finding any tests under this class
    # Reason for scanning it because the name starts with "Test..."
    __test__ = False

    collaborators: FakeCoreCollaborators = None

    def __init__(self, ctx: Context, collaborators: FakeCoreCollaborators):
        self.ctx = ctx
        self.collaborators = collaborators

    @staticmethod
    def _create_env(ctx: Context) -> "TestEnv":
        return TestEnv(ctx, FakeCoreCollaborators(ctx=ctx))

    @staticmethod
    def create_test_default_context() -> Context:
        return Context.create(os_arch=OsArch(os=MAC_OS, arch="test_arch", os_release="test_os_release"))

    def create(ctx: Context = create_test_default_context()) -> "TestEnv":
        return TestEnv._create_env(ctx)

    def get_test_env_root_path(self) -> str:
        return ROOT_PATH_TEST_ENV

    def get_context(self) -> Context:
        return self.ctx

    def get_collaborators(self) -> FakeCoreCollaborators:
        return self.collaborators


