import os
import shutil
import pytest
from pathlib import Path
from fastapi import UploadFile
from pymongo import MongoClient
import asyncio
import requests
from ocrd_webapi.workspace_manager import WorkspaceManager
import ocrd_webapi.constants as constants
from ocrd_webapi.database import initiate_database

TEST_WS_DIR = str("/tmp/test-wsm/workspaces")
WORKSPACE_2_ID = 'example-workspace-2'


@pytest.fixture(scope="session")
def event_loop():
    """
    this is a workaround. Template is https://github.com/tortoise/tortoise-orm/issues/638.
    """
    return asyncio.get_event_loop()


@pytest.fixture(name='workspaces_dir')
def _fixture_workspaces_dir():
    return TEST_WS_DIR


@pytest.fixture(name='workspace_manager')
def _fixture_plain_workspace():
    return WorkspaceManager(TEST_WS_DIR)


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
async def _fixture_dummy_workspace(workspace_manager, utils):
    with open(utils.to_asset_path("example_ws.ocrd.zip"), "rb") as fin:
        file = UploadFile("test", file=fin, content_type="application/zip")
        return await workspace_manager.create_workspace_from_zip(file)


@pytest.fixture(name='init_db', scope="session")
async def _fixture_init_db():
    """
    purpose of this fixture is only to init the database. This should only be used when
    `TestClient(app)` is used, because it has to be done in the FastAPI-Object
    """
    await initiate_database(constants.DB_URL)


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
