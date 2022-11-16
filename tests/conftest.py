import os
import shutil
import pytest
import requests
from pathlib import Path
from pymongo import MongoClient

from fastapi.testclient import TestClient

import ocrd_webapi.constants as constants
from ocrd_webapi.main import app
from ocrd_webapi.workflow_manager import WorkflowManager
from ocrd_webapi.workspace_manager import WorkspaceManager

from .utils_test import (
    allocate_asset,
    assert_status_code,
    parse_resource_id,
)


TEST_WS_DIR = str("/tmp/ocrd-web-api-test/workspaces")
TEST_WF_DIR = str("/tmp/ocrd-web-api-test/workflows")
WORKSPACE_2_ID = 'example-workspace-2'

def pytest_sessionstart(session):
    Path(TEST_WS_DIR).mkdir(parents=True, exist_ok=True)
    Path(TEST_WF_DIR).mkdir(parents=True, exist_ok=True)

def pytest_sessionfinish(session, exitstatus):
    if exitstatus == 0:
        shutil.rmtree(TEST_WS_DIR)
        shutil.rmtree(TEST_WF_DIR)

@pytest.fixture(scope="session", autouse=True)
def do_before_all_tests():
    """
    - clean workspace- and workflow-directories
    - make sure mongodb is available
    """
    shutil.rmtree(constants.WORKSPACES_DIR)
    os.mkdir(constants.WORKSPACES_DIR)
    shutil.rmtree(constants.WORKFLOWS_DIR)
    os.mkdir(constants.WORKFLOWS_DIR)

@pytest.fixture(scope='session')
def client(start_docker):
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="session")
def start_docker(do_before_all_tests, docker_ip, docker_services):
    port = docker_services.port_for("mongo", 27017)
    url = f"http://{docker_ip}:{port}"
    docker_services.wait_until_responsive(
        timeout=10.0, pause=0.1, check=lambda: is_url_responsive(url, retries=10)
    )

def is_url_responsive(url, retries: int = 0):
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except Exception:
            if retries <= 0:
                return False
            retries -= 1

@pytest.fixture(scope="session")
def docker_compose_project_name(docker_compose_project_name):
    return "ocrd-webapi-mongo-testdb"

@pytest.fixture(name='mongo_client', scope="session")
def _fixture_mongo_client(start_docker):
    # TODO: think about changing this in the long run!
    mongo_client = MongoClient(constants.DB_URL, serverSelectionTimeoutMS=3000)
    yield mongo_client


@pytest.fixture(name='workspace_mongo_coll', scope="session")
def _fixture_workspace_mongo_coll(mongo_client):
    # TODO: think about changing this in the long run!
    mydb = mongo_client[constants.MONGO_TESTDB]
    workspace_coll = mydb["workspace"]
    yield workspace_coll
    workspace_coll.drop()



@pytest.fixture(name='auth')
def _fixture_auth():
    user = os.getenv("OCRD_WEBAPI_USERNAME")
    pw = os.getenv("OCRD_WEBAPI_PASSWORD")
    yield user, pw
@pytest.fixture(name='workspace_manager')
def _fixture_workspace_manager():
    return WorkspaceManager()
@pytest.fixture(name='workflow_manager')
def _fixture_workflow_manager():
    return WorkflowManager()

# Workflow asset files
@pytest.fixture(name='asset_workflow1')
def _fixture_asset_workflow1():
    file = {'nextflow_script': allocate_asset("nextflow.nf")}
    yield file
@pytest.fixture(name='asset_workflow2')
def _fixture_asset_workflow2():
    file = {'nextflow_script': allocate_asset("nextflow-simple.nf")}
    yield file
@pytest.fixture(name='dummy_workflow_id')
def _fixture_dummy_workflow(asset_workflow2, client, auth):
    response = client.post("/workflow", files=asset_workflow2, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    yield parse_resource_id(response) # returns dummy_workflow_id

# Workspace asset files
@pytest.fixture(name='asset_workspace1')
def _fixture_asset_workspace1():
    file = {'workspace': allocate_asset("example_ws.ocrd.zip")}
    yield file
@pytest.fixture(name='asset_workspace2')
def _fixture_asset_workspace2():
    file = {'workspace': allocate_asset("example_ws2.ocrd.zip")}
    yield file
@pytest.fixture(name='asset_workspace3')
def _fixture_asset_workspace3():
    file = {'workspace': allocate_asset("example_ws_different_mets.ocrd.zip")}
    yield file
@pytest.fixture(name='dummy_workspace_id')
def _fixture_dummy_workspace(asset_workspace1, client):
    response = client.post("/workspace", files=asset_workspace1)
    assert_status_code(response.status_code, expected_floor=2)
    yield parse_resource_id(response) # returns dummy_workspace_id


