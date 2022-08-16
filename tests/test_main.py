import os
from fastapi.testclient import TestClient
import ocrd_webapi.constants as constants
from ocrd_webapi.main import app
import pytest
from shutil import rmtree
from os import mkdir
from os.path import exists, join
import pymongo

"""
for the tests the "storing"-directory is set to /tmp/ocrd_webapi_test. See config.py read_config()
for how that is accomplished currently.
"""

# TODO: think about changing this in the long run!
mongo_client = pymongo.MongoClient(constants.DB_URL)
mydb = mongo_client["test_operandi"]
workspace_col = mydb["workspace"]


@pytest.fixture(scope="session", autouse=True)
def do_before_all_tests(request):
    # clean workspaces-directory
    rmtree(constants.WORKSPACES_DIR)
    mkdir(constants.WORKSPACES_DIR)


@pytest.fixture(autouse=True)
def run_around_tests():
    # Before each test (until yield):
    workspace_col.drop()
    yield
    # After each test:
    # TODO: clean Database


def test_post_workspace(utils):
    # arrange
    file = {'workspace': open(utils.to_asset_path("example_ws.ocrd.zip"), 'rb')}

    # act
    with TestClient(app) as client:
        response = client.post("/workspace", files=file)

    # assert
    assert response.status_code == 200, "responose should have 2xx status code"
    workspace_id = response.json()['@id'].split("/")[-1]
    assert exists(join(constants.WORKSPACES_DIR, workspace_id)), "workspace-dir not existing"
    # TODO: verify mongdb contains correct entries

    workspace_from_db = workspace_col.find_one()
    assert workspace_from_db, "workspace was not created"
    db_id = str(workspace_from_db["_id"].as_uuid())
    assert db_id == workspace_id, f"wrong workspace id. Expected: {workspace_id}, found {db_id}"
