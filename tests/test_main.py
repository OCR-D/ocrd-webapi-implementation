import os
from fastapi.testclient import TestClient
import ocrd_webapi.constants as constants
from ocrd_webapi.main import app
import pytest
from shutil import rmtree
from os import mkdir
from os.path import exists, join
"""
for the tests the "storing"-directory is set to /tmp/ocrd_webapi_test. See config.py read_config()
for how that is accomplished currently.
"""

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def do_before_all_tests(request):
    # clean workspaces-directory
    rmtree(constants.WORKSPACES_DIR)
    mkdir(constants.WORKSPACES_DIR)


def test_post_workspace(utils):
    file = {'workspace': open(utils.to_asset_path("example_ws.ocrd.zip"), 'rb')}
    response = client.post("/workspace", files=file)
    assert response.status_code == 200, "responose should have 2xx status code"
    workspace_id = response.json()['@id'].split("/")[-1]
    assert exists(join(constants.WORKSPACES_DIR, workspace_id)), "workspace-dir not existing"
