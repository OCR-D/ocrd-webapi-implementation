"""
here are tests for workspaces that conatain mets-files that are not named "mets.xml" but something
else
"""
from os.path import (
    exists,
    join,
)
from ocrd_webapi.constants import WORKSPACES_DIR


def test_post_workspace(utils, workspace_mongo_coll, client):
    # arrange
    file = {'workspace': open(utils.to_asset_path("example_ws_different_mets.ocrd.zip"), 'rb')}

    # act
    response = client.post("/workspace", files=file)

    # assert
    assert response.status_code // 100 == 2, f"expected status code 2xx, got {response.status_code}"
    workspace_id = response.json()['@id'].split("/")[-1]
    assert exists(join(WORKSPACES_DIR, workspace_id)), "workspace-dir not existing"

    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_from_db, "workspace-entry was not created in mongodb"
    db_id = workspace_from_db["_id"]
    assert db_id == workspace_id, f"wrong workspace id. Expected: {workspace_id}, found {db_id}"


def test_get_workspace(utils, client):
    # arrange
    file = {'workspace': open(utils.to_asset_path("example_ws_different_mets.ocrd.zip"), 'rb')}
    response = client.post("/workspace", files=file)
    workspace_id = response.json()['@id'].split("/")[-1]

    # act
    response = client.get(f"/workspace/{workspace_id}",
                          headers={"accept": "application/vnd.ocrd+zip"})

    # assert
    assert response.status_code // 100 == 2, f"expected statuscode 2xx, got {response.status_code}"
    assert response.headers.get('content-type').find("zip") > -1, \
        "content-type should be something with 'zip'"


def test_run_workflow(utils, client, dummy_workflow):
    # arrange
    file = {'workspace': open(utils.to_asset_path("example_ws_different_mets.ocrd.zip"), 'rb')}
    response = client.post("/workspace", files=file)
    workspace_id = response.json()['@id'].split("/")[-1]

    # act
    # WorkflowArgs were removed, the line below does not work anymore
    # response = client.post(f"/workflow/{dummy_workflow}", json={"workspace_id": workspace_id})
    response = client.post(f"/workflow/{dummy_workflow}?workspace_id={workspace_id}")

    # assert
    assert response.status_code // 100 == 2, f"expected statuscode 2xx, got {response.status_code}"
    # TODO: assert the workflow finished successfully. Currently mets.xml is not dynamic, so first
    #       the possibility to provide a different-mets-name to run the workflow has to be
    #       implemented
