import pytest
from ocrd_webapi.managers.workspace_manager import WorkspaceManager
from .asserts_test import assert_status_code
from .constants import DB_NAME
from .utils_test import allocate_asset, parse_resource_id


@pytest.fixture(scope="session", name='workspace_mongo_coll')
def _fixture_workspace_mongo_coll(mongo_client):
    mydb = mongo_client[DB_NAME]
    workspace_coll = mydb["workspace"]
    yield workspace_coll
    workspace_coll.drop()


@pytest.fixture(name='workspace_manager')
def _fixture_workspace_manager():
    return WorkspaceManager()


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
