import shutil
import pytest
from pathlib import Path
from ocrd_webapi_test.workspace_manager import WorkspaceManager
from fastapi import UploadFile

TEST_WS_DIR = str(Path(Path.home(), "zeugs-ohne-backup/test-wsm/workspaces"))


@pytest.fixture(name='workspaces_dir')
def _fixture_workspaces_dir():
    return TEST_WS_DIR


@pytest.fixture(name='workspace_manager')
def _fixture_plain_workspace():
    return WorkspaceManager(TEST_WS_DIR)


@pytest.fixture(name='dummy_workspace')
async def _fixture_dummy_workspace(workspace_manager):
    with open("assets/example_ws.ocrd.zip", "rb") as fin:
        file = UploadFile("test", file=fin, content_type="application/zip")
        return await workspace_manager.create_workspace_from_zip(file)


def pytest_sessionstart(session):
    Path(TEST_WS_DIR).mkdir(parents=True, exist_ok=True)


def pytest_sessionfinish(session, exitstatus):
    if exitstatus == 0:
        shutil.rmtree(TEST_WS_DIR)


class Utils:
    @staticmethod
    def get_workspace_rsrc_id(workspace_resrc):
        return workspace_resrc.id.rsplit('/', 1)[1]


@pytest.fixture
def utils():
    return Utils()