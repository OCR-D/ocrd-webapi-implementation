from pytest import fixture
from ocrd_webapi.managers.workflow_manager import WorkflowManager
from tests.asserts_test import assert_status_code
from tests.utils_test import allocate_asset, parse_resource_id


@fixture(name='workflow_manager')
def fixture_workflow_manager():
    return WorkflowManager()


@fixture(name='asset_workflow1')
def fixture_asset_workflow1():
    file = {'nextflow_script': allocate_asset("nextflow.nf")}
    yield file


@fixture(name='asset_workflow2')
def fixture_asset_workflow2():
    file = {'nextflow_script': allocate_asset("nextflow-simple.nf")}
    yield file


@fixture(name='asset_workflow3')
def fixture_asset_workflow3():
    file = {'nextflow_script': allocate_asset("nextflow-simple.nf")}
    yield file


@fixture(name='dummy_workflow_id')
def fixture_dummy_workflow(asset_workflow2, client, auth):
    response = client.post("/workflow", files=asset_workflow2, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    yield parse_resource_id(response)  # returns dummy_workflow_id
