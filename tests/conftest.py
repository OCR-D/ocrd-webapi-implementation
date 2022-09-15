import os
import shutil
import pytest
from pathlib import Path
from pymongo import MongoClient
import requests
from ocrd_webapi.workspace_manager import WorkspaceManager
import ocrd_webapi.constants as constants
from fastapi.testclient import TestClient
from ocrd_webapi.main import app
from shutil import rmtree
from os import mkdir


TEST_WS_DIR = str("/tmp/test-wsm/workspaces")
WORKSPACE_2_ID = 'example-workspace-2'


@pytest.fixture(scope="session", autouse=True)
def do_before_all_tests(request, mongo_docker, mongo_client, utils):
    """
    - clean workspace- and workflow-directories
    - make sure mongodb is available
    """
    rmtree(constants.WORKSPACES_DIR)
    mkdir(constants.WORKSPACES_DIR)
    rmtree(constants.WORKFLOWS_DIR)
    mkdir(constants.WORKFLOWS_DIR)


@pytest.fixture(name='workspace_manager')
def _fixture_workspace_manager():
    return WorkspaceManager()


@pytest.fixture(name='mongo_client', scope="session")
def _fixture_mongo_client():
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


@pytest.fixture(name='dummy_workspace')
def _fixture_dummy_workspace(utils, client):
    file = {'workspace': open(utils.to_asset_path("example_ws.ocrd.zip"), 'rb')}
    response = client.post("/workspace", files=file)
    yield response.json()['@id'].split("/")[-1]


@pytest.fixture(name='dummy_workflow')
def _fixture_dummy_workflow(utils, client):
    nextflow_script = {'nextflow_script': open(utils.to_asset_path("nextflow-simple.nf"), 'rb')}
    response = client.post("/workflow", files=nextflow_script)
    yield response.json()['@id'].split("/")[-1]


@pytest.fixture(scope='session')
def client():
    with TestClient(app) as c:
        yield c



def pytest_sessionstart(session):
    Path(TEST_WS_DIR).mkdir(parents=True, exist_ok=True)


def pytest_sessionfinish(session, exitstatus):
    if exitstatus == 0:
        shutil.rmtree(TEST_WS_DIR)


class Utils:
    @staticmethod
    def get_workspace_rsrc_id(workspace_resrc):
        return workspace_resrc.id.rsplit('/', 1)[1]

    @staticmethod
    def to_asset_path(name):
        path_to_module = os.path.dirname(__file__)
        return os.path.join(os.path.abspath(path_to_module), "assets", name)


@pytest.fixture(scope="session")
def utils():
    return Utils()


def is_responsive(url, retries: int = 0):
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
def mongo_docker(docker_ip, docker_services):
    port = docker_services.port_for("mongo", 27017)
    url = f"http://{docker_ip}:{port}"
    docker_services.wait_until_responsive(
        timeout=10.0, pause=0.1, check=lambda: is_responsive(url)
    )
    return url
