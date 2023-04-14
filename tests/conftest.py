import os
import shutil
import pytest

from .constants import WORKFLOWS_DIR, WORKSPACES_DIR

pytest_plugins = [
    "tests.fixtures.fixtures_database",
    "tests.fixtures.fixtures_rabbitmq",
    "tests.fixtures.fixtures_server",
    "tests.fixtures.fixtures_workflow",
    "tests.fixtures.fixtures_workspace",
]


@pytest.fixture(scope="session", autouse=True)
def do_before_all_tests():
    shutil.rmtree(WORKSPACES_DIR, ignore_errors=True)
    os.makedirs(WORKSPACES_DIR)
    shutil.rmtree(WORKFLOWS_DIR, ignore_errors=True)
    os.makedirs(WORKFLOWS_DIR)


@pytest.fixture(scope="session")
def docker_compose_project_name(docker_compose_project_name):
    return "ocrd_webapi_test_image"
