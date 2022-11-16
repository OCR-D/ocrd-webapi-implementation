"""
- for the tests the "storing"-directory is set to /tmp/ocrd_webapi_test. See config.py read_config()
  for how that is accomplished currently.
- to get the on_startup_event of the app running `with TestClient(app) as client` is necessary. The
  on_startup_event is used to init mongodb. Maybe it is possible to move that to a fixture (with
  session-state mabye), but didn't try it yet
"""
import ocrd_webapi.constants as constants
import pytest
from os.path import exists, join
from .conftest import WORKSPACE_2_ID
from time import sleep

from .utils_test import (
    assert_status_code,
    parse_resource_id,
)


@pytest.fixture(autouse=True)
def run_around_tests(mongo_client):
    # Before each test (until yield):
    mongo_client[constants.MONGO_TESTDB]["workspace"].delete_many({})
    yield
    # After each test:

def assert_workspaces_len(expected_len, client):
    response = client.get("/workspace")
    assert_status_code(response.status_code, expected_floor=2)
    response_len = len(response.json())
    assert expected_len == response_len, "more workspaces than expected existing"

def assert_workspace_dir(workspace_id):
    assert exists(join(constants.WORKSPACES_DIR, workspace_id)), "workspace-dir not existing"

def find_workspace_id(client):
    """Find an existing workspace id"""
    response = client.get("/workspace")
    # Return the id of the first member in the workspace list
    if len(response.json()) > 0:
        existing_workspace_id = response.json()[0]['@id'].split("/")[-1]
    else:
        existing_workspace_id = "NO_WORKSPACES_AVAILABLE"
    return existing_workspace_id

def test_post_workspace(asset_workspace1, workspace_mongo_coll, client):
    # act
    response = client.post("/workspace", files=asset_workspace1)

    # assert
    assert_status_code(response.status_code, expected_floor=2)
    workspace_id = parse_resource_id(response)
    assert_workspace_dir(workspace_id)

    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_from_db, "workspace-entry was not created in mongodb"
    db_id = workspace_from_db["_id"]
    assert db_id == workspace_id, f"wrong workspace id. Expected: {workspace_id}, found {db_id}"


def test_put_workspace(asset_workspace1, asset_workspace2, workspace_mongo_coll, client):
    test_id = "workspace_put_test_id"

    # act part 1
    request1 = f"/workspace/{test_id}"
    response1 = client.put(request1, files=asset_workspace1)

    # assert first workspace was created (put) correctly
    assert_status_code(response1.status_code, expected_floor=2)
    assert exists(join(constants.WORKSPACES_DIR, test_id)), "workspace-dir not existing"

    # assert workspace created in mongodb
    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_from_db, "workspace-entry was not created in mongodb"
    db_id = workspace_from_db["_id"]
    assert db_id == test_id, f"wrong workspace id. Expected: {test_id}, found {db_id}"
    ocrd_identifier1 = workspace_from_db["ocrd_identifier"]

    # act part 2
    request2 = f"/workspace/{test_id}"
    response2 = client.put(request2, files=asset_workspace2)
    assert_status_code(response2.status_code, expected_floor=2)

    # assert workspace updated correctly in mongodb
    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_mongo_coll.count_documents({}) == 1, "expect exactly 1 workspace in db"
    ocrd_identifier2 = workspace_from_db["ocrd_identifier"]
    assert ocrd_identifier1 and ocrd_identifier2 and ocrd_identifier1 != ocrd_identifier2, (
        "put_workspace didn't update the workspace in the database. ocrd_identifier1: "
        f"{ocrd_identifier1}. ocrd_identifier2: {ocrd_identifier2}"
    )
    # assert workspace updated correctly on disk
    mets_path = join(constants.WORKSPACES_DIR, test_id, "mets.xml")
    with open(mets_path) as fin:
        assert WORKSPACE_2_ID in fin.read(), "expected string '%s' in metsfile" % WORKSPACE_2_ID


def test_delete_workspaces(asset_workspace1, workspace_mongo_coll, client):
    response = client.post("/workspace", files=asset_workspace1)
    workspace_id = parse_resource_id(response)
    assert exists(join(constants.WORKSPACES_DIR, workspace_id)), "workspace-dir not existing"

    # act
    response = client.delete(f"/workspace/{workspace_id}")
    assert_status_code(response.status_code, expected_floor=2)

    # assert
    workspace_mongo_coll.find_one()
    assert not exists(join(constants.WORKSPACES_DIR, workspace_id)), "workspace-dir still existing"
    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_from_db, "workspace-entry not existing but should still exist."
    assert workspace_from_db["deleted"], "deleted-flag of workspace should be set to true"


def test_delete_previous_existing_workspaces(asset_workspace1, workspace_mongo_coll, client):
    response = client.post("/workspace", files=asset_workspace1)
    workspace_id = parse_resource_id(response)

    request = f"/workspace/{workspace_id}"
    response = client.delete(request)
    assert_status_code(response.status_code, expected_floor=2) # Deleted
    response = client.delete(request)
    assert_status_code(response.status_code, expected_floor=4) # Not available

