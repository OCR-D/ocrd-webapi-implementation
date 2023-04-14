from os.path import join

from .asserts_test import (
    assert_db_entry_created,
    assert_db_entry_deleted,
    assert_status_code,
    assert_workspace_dir,
    assert_not_workspace_dir
)
from .constants import WORKSPACES_DIR
from .utils_test import parse_resource_id


def assert_workspaces_len(client, expected_len):
    response = client.get("/workspace")
    assert_status_code(response.status_code, expected_floor=2)
    response_len = len(response.json())
    assert expected_len == response_len, \
        "more workspaces than expected existing"


# Test cases
def test_post_workspace(client, auth, workspace_mongo_coll, asset_workspace1):
    response = client.post("/workspace", files=asset_workspace1, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    workspace_id = parse_resource_id(response)
    assert_workspace_dir(workspace_id)

    # Database checks
    resource_from_db = workspace_mongo_coll.find_one(
        {"workspace_id": workspace_id}
    )
    assert_db_entry_created(resource_from_db, workspace_id, db_key="workspace_id")


def test_post_workspace_different_mets(client, auth, workspace_mongo_coll, asset_workspace3):
    # The name of the mets file is not `mets.xml` inside the provided workspace
    response = client.post("/workspace", files=asset_workspace3, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    workspace_id = parse_resource_id(response)
    assert_workspace_dir(workspace_id)

    # Database checks
    resource_from_db = workspace_mongo_coll.find_one(
        {"workspace_id": workspace_id}
    )
    assert_db_entry_created(resource_from_db, workspace_id, db_key="workspace_id")


def test_put_workspace(client, auth, workspace_mongo_coll, asset_workspace1, asset_workspace2):
    test_id = "workspace_put_test_id"
    request1 = f"/workspace/{test_id}"
    response1 = client.put(request1, files=asset_workspace1, auth=auth)
    assert_status_code(response1.status_code, expected_floor=2)
    assert_workspace_dir(test_id)

    # Database checks
    workspace_from_db = workspace_mongo_coll.find_one(
        {"workspace_id": test_id}
    )
    assert_db_entry_created(workspace_from_db, test_id, db_key="workspace_id")
    ocrd_identifier1 = workspace_from_db["ocrd_identifier"]
    assert ocrd_identifier1, f"Ocrd identifier 1 not extracted successfully"

    request2 = f"/workspace/{test_id}"
    response2 = client.put(request2, files=asset_workspace2, auth=auth)
    assert_status_code(response2.status_code, expected_floor=2)

    # Database checks
    workspace_from_db = workspace_mongo_coll.find_one(
        {"workspace_id": test_id}
    )
    ocrd_identifier2 = workspace_from_db["ocrd_identifier"]
    assert ocrd_identifier2, f"Ocrd identifier 2 not extracted successfully"

    assert ocrd_identifier1 != ocrd_identifier2, \
        f"Ocrd identifiers should not match: {ocrd_identifier1} == {ocrd_identifier2}"

    # assert workspace updated correctly on disk
    # TODO: Use resource manager instance to check this...
    mets_path = join(WORKSPACES_DIR, test_id, "mets.xml")
    with open(mets_path) as fin:
        workspace_2_id = 'example-workspace-2'
        assert workspace_2_id in fin.read(), \
            "expected string '%s' in mets file" % workspace_2_id


def test_delete_workspace(client, auth, workspace_mongo_coll, asset_workspace1):
    # Upload a workspace
    response = client.post("/workspace", files=asset_workspace1, auth=auth)
    workspace_id = parse_resource_id(response)
    assert_status_code(response.status_code, expected_floor=2)
    assert_workspace_dir(workspace_id)

    # Delete the uploaded workspace
    response = client.delete(f"/workspace/{workspace_id}", auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    assert_not_workspace_dir(workspace_id)

    workspace_from_db = workspace_mongo_coll.find_one(
        {"workspace_id": workspace_id}
    )
    assert_db_entry_deleted(workspace_from_db)


def test_delete_workspace_non_existing(client, auth, workspace_mongo_coll, asset_workspace1):
    response = client.post("/workspace", files=asset_workspace1, auth=auth)
    workspace_id = parse_resource_id(response)
    response = client.delete(f"/workspace/{workspace_id}", auth=auth)
    assert_status_code(response.status_code, expected_floor=2)  # Deleted
    response = client.delete(f"/workspace/{workspace_id}", auth=auth)
    assert_status_code(response.status_code, expected_floor=4)  # Not available


def test_get_workspace(client, auth, asset_workspace3):
    response = client.post("/workspace", files=asset_workspace3, auth=auth)
    workspace_id = parse_resource_id(response)
    headers = {"accept": "application/vnd.ocrd+zip"}
    response = client.get(f"/workspace/{workspace_id}", headers=headers)
    assert_status_code(response.status_code, expected_floor=2)
    assert response.headers.get('content-type').find("zip") > -1, \
        "content-type should be something with 'zip'"


def test_get_workspace_non_existing(client):
    headers = {"accept": "application/vnd.ocrd+zip"}
    response = client.get(f"/workspace/non-existing-workspace-id", headers=headers)
    assert response.status_code == 404, \
        "expect 404 error code for non existing workspace"
