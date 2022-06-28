"""
https://tonybaloney.github.io/posts/async-test-patterns-for-pytest-and-unittest.html
"""
import os.path

import pytest

from fastapi import UploadFile
from pathlib import Path
import zipfile


@pytest.mark.asyncio
async def test_create_workspace_from_zip(workspace_manager, workspaces_dir, utils):
    # arrange
    with open("assets/example_ws.ocrd.zip", "rb") as fin:
        file = UploadFile("test", file=fin, content_type="application/zip")
        # act
        workspace = await workspace_manager.create_workspace_from_zip(file)

    # assert
    uid = utils.get_workspace_rsrc_id(workspace)
    mets_path = Path(workspaces_dir, uid, "mets.xml")
    assert mets_path.exists(), "Expected mets-file located here:'%s'" % mets_path


@pytest.mark.asyncio
async def test_update_workspace(workspace_manager, workspaces_dir):
    # arrange
    uid = "test-123"
    with open("assets/example_ws.ocrd.zip", "rb") as fin:
        file = UploadFile("test", file=fin, content_type="application/zip")
        # act
        await workspace_manager.create_workspace_from_zip(file, uid)
    # assert
    mets_path = Path(workspaces_dir, uid, "mets.xml")
    assert mets_path.exists(), "Expected mets-file located here:'%s'" % mets_path


def test_get_workspace_rsrc(workspace_manager, dummy_workspace, utils):
    # arrange
    uid = utils.get_workspace_rsrc_id(dummy_workspace)
    # act
    workspace = workspace_manager.get_workspace_rsrc(uid)
    # assert
    assert workspace and workspace.id, "Workspace: %s" % workspace


def test_get_workspaces(workspace_manager, dummy_workspace):
    # act
    workspaces = workspace_manager.get_workspaces()
    # assert
    assert isinstance(workspaces, list), "expected list, but got %s" % type(workspaces)
    assert len(workspaces) > 0, "expected elements in list"
    assert workspaces[0].id, "expected workspace_rsrc"


def test_delete_workspaces(workspace_manager, dummy_workspace, utils):
    # act
    uid = utils.get_workspace_rsrc_id(dummy_workspace)
    workspace_manager.delete_workspace(uid)
    # assert
    deleted_ws = workspace_manager.get_workspace_rsrc(uid)
    assert not deleted_ws, "workspace should have been deleted"


def test_get_workspaces_as_bag(workspace_manager, dummy_workspace, utils):
    # arrange
    uid = utils.get_workspace_rsrc_id(dummy_workspace)

    # act
    bag_path = workspace_manager.get_workspace_bag(uid)

    # assert
    assert os.path.exists(bag_path), "expected bag-file not existing"
    assert zipfile.is_zipfile(bag_path), "created resource is no zipfile"
