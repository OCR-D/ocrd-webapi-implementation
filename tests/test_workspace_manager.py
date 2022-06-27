"""
https://tonybaloney.github.io/posts/async-test-patterns-for-pytest-and-unittest.html
"""
import pytest
from ocrd_webapi_test.workspace_manager import WorkspaceManager
from fastapi import UploadFile


@pytest.fixture(name='workspace_manager')
def _fixture_plain_workspace():
    return WorkspaceManager()


@pytest.mark.asyncio
async def test_create_workspace_from_zip(workspace_manager):
    # arrange
    # act
    with open("assets/example_ws.ocrd.zip", "rb") as fin:
        file = UploadFile("test", file=fin, content_type="application/zip")
        workspace = await workspace_manager.create_workspace_from_zip(file)
    print("WORKSPACE WORKSPACE WORKSPACE ->")
    print(workspace)
    print("<- WORKSPACE WORKSPACE WORKSPACE")
    # this test throws an error because of my programming mistakes in create_workspace_from_zip.
    # test manually with running server first
    # assert
    assert False
