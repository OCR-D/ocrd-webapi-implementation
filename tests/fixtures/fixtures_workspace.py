from pytest import fixture
from ocrd_webapi.managers.workspace_manager import WorkspaceManager
from tests.asserts_test import assert_status_code
from tests.utils_test import allocate_asset, parse_resource_id


@fixture(name='workspace_manager')
def fixture_workspace_manager():
    return WorkspaceManager()


@fixture(name='asset_workspace1')
def fixture_asset_workspace1():
    file = {'workspace': allocate_asset("example_ws.ocrd.zip")}
    yield file


@fixture(name='asset_workspace2')
def fixture_asset_workspace2():
    file = {'workspace': allocate_asset("example_ws2.ocrd.zip")}
    yield file


@fixture(name='asset_workspace3')
def fixture_asset_workspace3():
    file = {'workspace': allocate_asset("example_ws_different_mets.ocrd.zip")}
    yield file


@fixture(name='dummy_workspace_id')
def fixture_dummy_workspace(asset_workspace1, client, auth):
    response = client.post("/workspace", files=asset_workspace1, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    yield parse_resource_id(response)  # returns dummy_workspace_id
