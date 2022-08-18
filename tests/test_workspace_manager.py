"""
https://tonybaloney.github.io/posts/async-test-patterns-for-pytest-and-unittest.html
"""
import os.path

import pytest

from fastapi import UploadFile
from pathlib import Path
import zipfile
from .conftest import WORKSPACE_2_ID
from ocrd_webapi.database import initiate_database
from ocrd_webapi.constants import DB_URL


@pytest.mark.asyncio
async def test_create_workspace_from_zip(workspace_manager, workspaces_dir, utils, init_db):
    # arrange
    with open(utils.to_asset_path("example_ws.ocrd.zip"), "rb") as fin:
        file = UploadFile("test", file=fin, content_type="application/zip")
        # act
        workspace = await workspace_manager.create_workspace_from_zip(file)

    # assert
    uid = utils.get_workspace_rsrc_id(workspace)
    mets_path = Path(workspaces_dir, uid, "mets.xml")
    assert mets_path.exists(), "Expected mets-file located here:'%s'" % mets_path


@pytest.mark.asyncio
async def test_update_workspace(dummy_workspace, workspace_manager, workspaces_dir, utils, init_db):
    # arrange
    uid = utils.get_workspace_rsrc_id(dummy_workspace)
    mets_path = Path(workspaces_dir, uid, "mets.xml")
    with open(mets_path) as fin2:
        assert WORKSPACE_2_ID not in fin2.read(), (
            "test arrangement failed. Expect string '%s' not to be in metsfile" % WORKSPACE_2_ID
        )

    # act
    with open(utils.to_asset_path("example_ws2.ocrd.zip"), "rb") as fin:
        file = UploadFile("test", file=fin, content_type="application/zip")
        updated_workspace = await workspace_manager.update_workspace(file, uid)

    # assert
    assert updated_workspace and updated_workspace.id, "updating failed/returned None"
    with open(mets_path) as fin:
        assert WORKSPACE_2_ID in fin.read(), "expected string '%s' in metsfile" % WORKSPACE_2_ID


def test_get_workspace_rsrc(workspace_manager, dummy_workspace, utils, init_db):
    # arrange
    uid = utils.get_workspace_rsrc_id(dummy_workspace)
    # act
    workspace = workspace_manager.get_workspace_rsrc(uid)
    # assert
    assert workspace and workspace.id, "Workspace: %s" % workspace


def test_get_workspaces(workspace_manager, dummy_workspace, init_db):
    # act
    workspaces = workspace_manager.get_workspaces()
    # assert
    assert isinstance(workspaces, list), "expected list, but got %s" % type(workspaces)
    assert len(workspaces) > 0, "expected elements in list"
    assert workspaces[0].id, "expected workspace_rsrc"


async def test_delete_workspaces(workspace_manager, dummy_workspace, utils, init_db):
    # act
    uid = utils.get_workspace_rsrc_id(dummy_workspace)
    await workspace_manager.delete_workspace(uid)
    # assert
    deleted_ws = workspace_manager.get_workspace_rsrc(uid)
    assert not deleted_ws, "workspace should have been deleted"


def test_get_workspaces_as_bag(workspace_manager, dummy_workspace, utils, init_db):
    # arrange
    uid = utils.get_workspace_rsrc_id(dummy_workspace)

    # act
    bag_path = workspace_manager.get_workspace_bag(uid)

    # assert
    assert os.path.exists(bag_path), "expected bag-file not existing"
    assert zipfile.is_zipfile(bag_path), "created resource is not a zipfile"
