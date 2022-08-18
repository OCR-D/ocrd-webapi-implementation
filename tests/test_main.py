"""
- for the tests the "storing"-directory is set to /tmp/ocrd_webapi_test. See config.py read_config()
  for how that is accomplished currently.
- to get the on_startup_event of the app running `with TestClient(app) as client` is necessary. The
  on_startup_event is used to init mongodb. Maybe it is possible to move that to a fixture (with
  session-state mabye), but didn't try it yet
"""
from fastapi.testclient import TestClient
import ocrd_webapi.constants as constants
from ocrd_webapi.main import app
import pytest
from shutil import rmtree
from os import mkdir
from os.path import exists, join
from pymongo.errors import ServerSelectionTimeoutError
from .conftest import WORKSPACE_2_ID


@pytest.fixture(scope="session", autouse=True)
def do_before_all_tests(request, mongo_client):
    # clean workspaces-directory
    rmtree(constants.WORKSPACES_DIR)
    mkdir(constants.WORKSPACES_DIR)
    # make sure a mongdb is available for the tests and abort if not
    try:
        mongo_client.admin.command("ismaster")
    except ServerSelectionTimeoutError as e:
        print(mongo_client.server)
        raise Exception(f"mongodb not available: {constants.DB_URL}. start e.g. with docker: "
                        "`docker run -d -p 27017:27017 mongo:latest`") from e


@pytest.fixture(autouse=True)
def run_around_tests(mongo_client):
    # Before each test (until yield):
    mongo_client[constants.MONGO_TESTDB]["workspace"].delete_many({})
    yield
    # After each test:


def test_post_workspace(utils, workspace_mongo_coll):
    # arrange
    file = {'workspace': open(utils.to_asset_path("example_ws.ocrd.zip"), 'rb')}

    # act
    with TestClient(app) as client:
        response = client.post("/workspace", files=file)

    # assert
    assert response.status_code == 200, "response should have 2xx status code"
    workspace_id = response.json()['@id'].split("/")[-1]
    assert exists(join(constants.WORKSPACES_DIR, workspace_id)), "workspace-dir not existing"

    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_from_db, "workspace-entry was not created in mongodb"
    db_id = workspace_from_db["_id"]
    assert db_id == workspace_id, f"wrong workspace id. Expected: {workspace_id}, found {db_id}"


def test_put_workspace(utils, workspace_mongo_coll):
    # arrange
    file1 = {'workspace': open(utils.to_asset_path("example_ws.ocrd.zip"), 'rb')}
    file2 = {'workspace': open(utils.to_asset_path("example_ws2.ocrd.zip"), 'rb')}
    test_id = "workspace_put_test_id"

    # act
    with TestClient(app) as client:
        response1 = client.put(f"/workspace/{test_id}", files=file1)
        # assert first workspace created correctly
        assert response1.status_code == 200, "response1 should have 2xx status code"
        assert exists(join(constants.WORKSPACES_DIR, test_id)), "workspace-dir not existing"

        # assert workspace created in mongodb
        workspace_from_db = workspace_mongo_coll.find_one()
        assert workspace_from_db, "workspace-entry was not created in mongodb"
        db_id = workspace_from_db["_id"]
        assert db_id == test_id, f"wrong workspace id. Expected: {test_id}, found {db_id}"
        ocrd_identifier1 = workspace_from_db["ocrd_identifier"]

        response2 = client.put(f"/workspace/{test_id}", files=file2)
        assert response2.status_code == 200, "response2 should have 2xx status code"

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


def test_delete_workspaces(utils, workspace_mongo_coll):
    # arrange
    import pudb
    pudb.set_trace()
    file = {'workspace': open(utils.to_asset_path("example_ws.ocrd.zip"), 'rb')}
    with TestClient(app) as client:
        response = client.post("/workspace", files=file)
        workspace_id = response.json()['@id'].split("/")[-1]
        assert exists(join(constants.WORKSPACES_DIR, workspace_id)), "workspace-dir not existing"

        # act
        response = client.delete(f"/workspace/{workspace_id}")
        assert response.status_code == 200, "response should have 2xx status code"

    # assert
    workspace_mongo_coll.find_one()
    assert not exists(join(constants.WORKSPACES_DIR, workspace_id)), "workspace-dir still existing"
    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_from_db, "workspace-entry not existing but should still exist"
    assert workspace_from_db["deleted"], "deleted-flag of workspace should be set to true"
