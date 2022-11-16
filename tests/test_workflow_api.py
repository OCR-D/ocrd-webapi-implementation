"""
- for the tests the "storing"-directory is set to /tmp/ocrd_webapi_test. See config.py read_config()
  for how that is accomplished currently.
- to get the on_startup_event of the app running `with TestClient(app) as client` is necessary. The
  on_startup_event is used to init mongodb. Maybe it is possible to move that to a fixture (with
  session-state mabye), but didn't try it yet
"""
import ocrd_webapi.constants as constants
import pytest
from os.path import exists, join
from .conftest import WORKSPACE_2_ID
from time import sleep

from .utils_test import (
    assert_status_code,
    parse_resource_id,
)


def test_upload_workflow_script(asset_workflow1, client, auth):
    response = client.post("/workflow", files=asset_workflow1, auth=auth)
    workflow_id = parse_resource_id(response)
    assert_status_code(response.status_code, expected_floor=2)
    assert_workflow_dir(workflow_id)


def test_get_workflow_script(asset_workflow1, client, auth):
    client.post("/workflow", files=asset_workflow1, auth=auth)
    existing_workflow_id = find_workflow_id(client)
    request = f"/workflow/{existing_workflow_id}"
    headers = {"accept": "text/vnd.ocrd.workflow"}
    response = client.get(request, headers=headers)
    assert_status_code(response.status_code, expected_floor=2)
    assert_workflow_dir(existing_workflow_id)


def test_update_workflow_script(asset_workflow2, client, auth):
    existing_workflow_id = find_workflow_id(client)
    request = f"/workflow/{existing_workflow_id}"
    response = client.put(request, files=asset_workflow2, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    assert_workflow_dir(existing_workflow_id)


def test_start_workflow_script(client, dummy_workspace_id, dummy_workflow_id, auth):
    # WorkflowArgs were removed, the line below does not work anymore
    # response = client.post(f"/workflow/{dummy_workflow}", json={"workspace_id": dummy_workspace}, auth=auth)
    response = client.post(f"/workflow/{dummy_workflow_id}?workspace_id={dummy_workspace_id}", auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    assert_job_id(response)

def assert_workflows_len(expected_len, client):
    response = client.get("/workflow")
    assert_status_code(response.status_code, expected_floor=2)
    response_len = len(response.json())
    assert expected_len == response_len, "more workflows than expected existing"

def assert_workflow_dir(workflow_id):
    assert exists(join(constants.WORKFLOWS_DIR, workflow_id)), "workflow-dir not existing"

def assert_job_id(response):
    # Asserts that the job id is not an empty string
    assert not response.json()['@id'].split("/")[-1] == "", "job id was not assigned"

def find_workflow_id(client):
    """Find an existing workflow id"""
    response = client.get("/workflow")
    # Return the id of the first member in the workflow list
    if len(response.json()) > 0:
        existing_workflow_id = response.json()[0]['@id'].split("/")[-1]
    else:
        existing_workflow_id = "NO_WORKFLOWS_AVAILABLE"
    return existing_workflow_id

def test_job_status(client, dummy_workspace_id, dummy_workflow_id):
    # arrange
    # WorkflowArgs were removed, the line below does not work anymore
    # response = client.post(f"/workflow/{dummy_workflow}", json={"workspace_id": dummy_workspace})
    response = client.post(f"/workflow/{dummy_workflow_id}?workspace_id={dummy_workspace_id}")
    job_id = parse_resource_id(response)

    # act
    for x in range(0,20):
        # try several times because finishing execution needs some time
        response = client.get(f"workflow/{dummy_workflow_id}/{job_id}")
        state = response.json()['state']
        if state == 'STOPPED':
            break
        sleep(0.5)

    # assert
    assert state == 'STOPPED', f"expecting job.state to be set to stopped but is {state}"

