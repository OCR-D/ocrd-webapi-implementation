"""
- for the tests the "storing"-directory is set to /tmp/ocrd_webapi_test. See config.py read_config()
  for how that is accomplished currently.
- to get the on_startup_event of the app running `with TestClient(app) as client` is necessary. The
  on_startup_event is used to init mongodb. Maybe it is possible to move that to a fixture (with
  session-state maybe), but didn't try it yet
"""
import pytest
from os.path import exists, join
from time import sleep

from ocrd_webapi.constants import (
    BASE_DIR,
    WORKFLOWS_ROUTER,
    MONGO_TESTDB,
)
from .utils_test import (
    assert_status_code,
    parse_resource_id,
    parse_job_state,
    assert_db_entry_created,
)

# TODO: Utilize the Workflow manager instead of this
WORKFLOWS_DIR = join(BASE_DIR, WORKFLOWS_ROUTER)


# TODO: Database part for Workflows is missing
# Implement both the source code and the tests
@pytest.fixture(autouse=True)
def run_around_tests(mongo_client):
    # Before each test (until yield):
    mongo_client[MONGO_TESTDB]["workflow"].delete_many({})
    yield
    # After each test:


# Helper assert functions
def assert_workflow_dir(workflow_id):
    assert exists(join(WORKFLOWS_DIR, workflow_id)), \
        "workflow-dir not existing"


def assert_not_workflow_dir(workflow_id):
    assert not exists(join(WORKFLOWS_DIR, workflow_id)), \
        "workflow-dir existing"


def assert_workflows_len(expected_len, client):
    response = client.get("/workflow")
    assert_status_code(response.status_code, expected_floor=2)
    response_len = len(response.json())
    assert expected_len == response_len, \
        "more workflows than expected existing"


# Test cases
def test_post_workflow_script(client, auth, workflow_mongo_coll, asset_workflow1):
    # Post a new workflow script
    response = client.post("/workflow", files=asset_workflow1, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    workflow_id = parse_resource_id(response)
    assert_workflow_dir(workflow_id)

    # Database checks
    workflow_from_db = workflow_mongo_coll.find_one()
    assert_db_entry_created(workflow_from_db, workflow_id)


def test_put_workflow_script(client, auth, asset_workflow1, asset_workflow2, asset_workflow3):
    # Post a new workflow script
    response = client.post("/workflow", files=asset_workflow1, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    workflow_id = parse_resource_id(response)
    assert_workflow_dir(workflow_id)

    # Put to the same workflow_id
    request = f"/workflow/{workflow_id}"
    response = client.put(request, files=asset_workflow2, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    workflow_id = parse_resource_id(response)
    assert_workflow_dir(workflow_id)

    # TODO: Do database checks


def test_put_workflow_script_non_existing(client, auth, asset_workflow1):
    # Put to a non-existing workflow_id
    non_existing = 'non_existing_123'
    request = f"/workflow/{non_existing}"
    response = client.put(request, files=asset_workflow1, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    newly_created_workflow_id = parse_resource_id(response)
    assert_workflow_dir(newly_created_workflow_id)

    # TODO: Do database checks


def test_get_workflow_script(client, auth, asset_workflow1):
    # Post a new workflow script
    response = client.post("/workflow", files=asset_workflow1, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    workflow_id = parse_resource_id(response)
    assert_workflow_dir(workflow_id)

    # Get the same workflow script
    headers = {"accept": "text/vnd.ocrd.workflow"}
    response = client.get(f"/workflow/{workflow_id}", headers=headers)
    assert_status_code(response.status_code, expected_floor=2)
    # the response is actually the workflow script
    # checking for the resource_id doesn't make sense
    # workflow_id = parse_resource_id(response)

    # It should be checked the following way
    # Not working currently:
    # assert response.headers.get('content-type').find(".nf") > -1, \
    #    "content-type missing '.nf'"
    # assert response.headers.get('content-type').find("nextflow") > -1, \
    #    "content-type missing 'nextflow'"

    # TODO: Do database checks


def test_run_workflow(client, auth, dummy_workflow_id, dummy_workspace_id):
    params = {"workspace_id": dummy_workspace_id}
    response = client.post(f"/workflow/{dummy_workflow_id}", json=params, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    job_id = parse_resource_id(response)
    assert job_id

    # TODO: Do database checks


def test_run_workflow_different_mets(client, auth, dummy_workflow_id, asset_workspace3):
    # The name of the mets file is not `mets.xml` inside the provided workspace
    response = client.post("/workspace", files=asset_workspace3, auth=auth)
    workspace_id = parse_resource_id(response)
    params = {"workspace_id": workspace_id}
    response = client.post(f"/workflow/{dummy_workflow_id}", json=params, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    job_id = parse_resource_id(response)
    assert job_id

    # TODO: assert the workflow finished successfully. Currently mets.xml is not dynamic, so first
    # the possibility to provide a different-mets-name to run the workflow has to be implemented
    # TODO: Do database checks


# TODO: This should be better implemented...
def test_job_status(client, auth, dummy_workflow_id, dummy_workspace_id):
    params = {"workspace_id": dummy_workspace_id}
    response = client.post(f"/workflow/{dummy_workflow_id}", json=params, auth=auth)
    job_id = parse_resource_id(response)

    job_state = 'NoState'
    # try several times because finishing execution needs some time
    for x in range(0, 100):
        response = client.get(f"workflow/{dummy_workflow_id}/{job_id}")
        job_state = parse_job_state(response)
        if job_state is None:
            break
        if job_state == 'STOPPED' or job_state == 'SUCCESS':
            break
        sleep(3)

    assert (job_state == 'STOPPED' or job_state == 'SUCCESS'), \
        f"expecting job.state to be set to stopped/success but is {job_state}"

    # TODO: Do database checks


# TODO: Implement the test once there is an
# delete workflow script source code implemented
# delete workflow is not in the WebAPI specification
def test_delete_workflow_script(client, auth):
    pass


def test_delete_workspace_non_existing(client, auth):
    pass
