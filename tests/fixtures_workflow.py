import pytest
from ocrd_webapi.managers.workflow_manager import WorkflowManager
from .asserts_test import assert_status_code
from .constants import DB_NAME
from .utils_test import allocate_asset, parse_resource_id


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


@pytest.fixture(name='workflow_manager')
def _fixture_workflow_manager():
    return WorkflowManager()


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
