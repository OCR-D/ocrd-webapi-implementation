"""
here are tests for workspaces that conatain mets-files that are not named "mets.xml" but something
else
"""
from os.path import (
    exists,
    join,
)
from ocrd_webapi.constants import WORKSPACES_DIR

from .utils_test import (
    assert_status_code,
    parse_resource_id
)


def test_post_workspace(asset_workspace3, workspace_mongo_coll, client):
    response = client.post("/workspace", files=asset_workspace3)
    assert_status_code(response.status_code, expected_floor=2)
    workspace_id = parse_resource_id(response)
    assert exists(join(WORKSPACES_DIR, workspace_id)), "workspace-dir not existing"

    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_from_db, "workspace-entry was not created in mongodb"
    db_id = workspace_from_db["_id"]
    assert db_id == workspace_id, f"wrong workspace id. Expected: {workspace_id}, found {db_id}"


def test_get_workspace(asset_workspace3, client):
    response = client.post("/workspace", files=asset_workspace3)
    workspace_id = parse_resource_id(response)
    headers = {"accept": "application/vnd.ocrd+zip"}
    response = client.get(f"/workspace/{workspace_id}", headers=headers)

    # assert
    assert_status_code(response.status_code, expected_floor=2)
    assert response.headers.get('content-type').find("zip") > -1, \
        "content-type should be something with 'zip'"


def test_run_workflow(asset_workspace3, client, dummy_workflow_id):
    response = client.post("/workspace", files=asset_workspace3)
    workspace_id = parse_resource_id(response)

    # act
    # WorkflowArgs were removed, the line below does not work anymore
    # response = client.post(f"/workflow/{dummy_workflow}", json={"workspace_id": workspace_id})
    response = client.post(f"/workflow/{dummy_workflow_id}?workspace_id={workspace_id}")

    # assert
    assert_status_code(response.status_code, expected_floor=2)
    # TODO: assert the workflow finished successfully. Currently mets.xml is not dynamic, so first
    #       the possibility to provide a different-mets-name to run the workflow has to be
    #       implemented
