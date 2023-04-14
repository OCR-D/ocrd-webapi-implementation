import os
import shutil
import pytest
import requests
from pymongo import MongoClient

from fastapi.testclient import TestClient
from ocrd_webapi.main import app
from ocrd_webapi.managers.workflow_manager import WorkflowManager
from ocrd_webapi.managers.workspace_manager import WorkspaceManager

from .asserts_test import assert_status_code
from .constants import (
    DB_NAME,
    DB_URL,
    OCRD_WEBAPI_USERNAME,
    OCRD_WEBAPI_PASSWORD,
    WORKFLOWS_DIR,
    WORKSPACES_DIR
)
from .utils_test import (
    allocate_asset,
    parse_resource_id,
)


@pytest.fixture(scope='session')
def client(start_mongo_docker):
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def start_mongo_docker(docker_ip, docker_services, do_before_all_tests):
    # This returns 6701, the port configured inside tests/docker-compose.yml
    port = docker_services.port_for("mongo", 27017)
    url = f"http://{docker_ip}:{port}"
    docker_services.wait_until_responsive(
        timeout=10.0,
        pause=0.1,
        check=lambda: is_url_responsive(url, retries=10)
    )


@pytest.fixture(scope="session", autouse=True)
def do_before_all_tests():
    """
    - clean workspace- and workflow-directories
    - make sure mongodb is available
    """
    shutil.rmtree(WORKSPACES_DIR, ignore_errors=True)
    os.makedirs(WORKSPACES_DIR)
    shutil.rmtree(WORKFLOWS_DIR, ignore_errors=True)
    os.makedirs(WORKFLOWS_DIR)


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


# Fixtures related to the Mongo DB
@pytest.fixture(scope="session", name='mongo_client')
def _fixture_mongo_client(start_mongo_docker):
    mongo_client = MongoClient(DB_URL, serverSelectionTimeoutMS=3000)
    yield mongo_client


@pytest.fixture(scope="session", name='workspace_mongo_coll')
def _fixture_workspace_mongo_coll(mongo_client):
    mydb = mongo_client[DB_NAME]
    workspace_coll = mydb["workspace"]
    yield workspace_coll
    workspace_coll.drop()


@pytest.fixture(scope="session", name='workflow_mongo_coll')
def _fixture_workflow_mongo_coll(mongo_client):
    mydb = mongo_client[DB_NAME]
    workflow_coll = mydb["workflow"]
    yield workflow_coll
    workflow_coll.drop()


@pytest.fixture(scope="session", name='workflow_job_mongo_coll')
def _fixture_workflow_job_mongo_coll(mongo_client):
    mydb = mongo_client[DB_NAME]
    workflow_job_coll = mydb["workflow_job"]
    yield workflow_job_coll
    workflow_job_coll.drop()


# Dummy authentication
@pytest.fixture(name='auth')
def _fixture_auth():
    yield OCRD_WEBAPI_USERNAME, OCRD_WEBAPI_PASSWORD


# TODO: Managers are not utilized during the tests
# TODO: Utilize them, once they are completely finalized
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


@pytest.fixture(name='asset_workflow3')
def _fixture_asset_workflow3():
    file = {'nextflow_script': allocate_asset("nextflow-simple.nf")}
    yield file


@pytest.fixture(name='dummy_workflow_id')
def _fixture_dummy_workflow(asset_workflow2, client, auth):
    response = client.post("/workflow", files=asset_workflow2, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    yield parse_resource_id(response)  # returns dummy_workflow_id


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
def _fixture_dummy_workspace(asset_workspace1, client, auth):
    response = client.post("/workspace", files=asset_workspace1, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    yield parse_resource_id(response)  # returns dummy_workspace_id
