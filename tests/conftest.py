import os
import shutil
import pytest

from .constants import WORKFLOWS_DIR, WORKSPACES_DIR

pytest_plugins = [
    "tests.fixtures_modules",
    "tests.fixtures_workflow",
    "tests.fixtures_workspace",
]


@pytest.fixture(scope="session", autouse=True)
def do_before_all_tests():
    shutil.rmtree(WORKSPACES_DIR, ignore_errors=True)
    os.makedirs(WORKSPACES_DIR)
    shutil.rmtree(WORKFLOWS_DIR, ignore_errors=True)
    os.makedirs(WORKFLOWS_DIR)
