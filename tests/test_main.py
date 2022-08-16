import os
from fastapi.testclient import TestClient
import ocrd_webapi.constants as constants
from ocrd_webapi.main import app
import pytest
from shutil import rmtree
from os import mkdir
from os.path import exists, join
"""
for the tests the "storing"-directory is set to /tmp/ocrd_webapi_test. See config.py read_config()
for how that is accomplished currently.
"""

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def do_before_all_tests(request):
    # clean workspaces-directory
    rmtree(constants.WORKSPACES_DIR)
    mkdir(constants.WORKSPACES_DIR)

    # clean workflows-directory
    rmtree(constants.WORKFLOWS_DIR)
    mkdir(constants.WORKFLOWS_DIR)

def test_post_workspace(utils):
    file = {'workspace': open(utils.to_asset_path("example_ws.ocrd.zip"), 'rb')}
    response = client.post("/workspace", files=file)
    assert_status_code(response.status_code, expected_floor=2)
    workspace_id = get_workspace_id(response)
    assert_workspace_dir(workspace_id)
    assert_workspaces_len(1)

def test_upload_workflow_script(utils):
    nextflow_script = {'nextflow_script': open(utils.to_asset_path("nextflow.nf"), 'rb')}
    response = client.post("/workflow", files=nextflow_script)
    workflow_id = get_workflow_id(response)
    assert_status_code(response.status_code, expected_floor=2)
    assert_workflow_dir(workflow_id)
    assert_workflows_len(1)

def test_get_workflow_script(utils):
    existing_workflow_id = find_workflow_id()
    response = client.get(f"/workflow/{existing_workflow_id}")
    assert_status_code(response.status_code, expected_floor=2)
    assert_workflow_dir(existing_workflow_id)
    assert_workflows_len(1)

def test_update_workflow_script(utils):
    nextflow_script = {'nextflow_script': open(utils.to_asset_path("nextflow-simple.nf"), 'rb')}
    existing_workflow_id = find_workflow_id()
    response = client.put(f"/workflow/{existing_workflow_id}", files=nextflow_script)
    assert_status_code(response.status_code, expected_floor=2)
    assert_workflow_dir(existing_workflow_id)
    assert_workflows_len(1)

def test_start_workflow_script(utils):
    existing_workspace_id = find_workspace_id()
    existing_workflow_id = find_workflow_id()
    response = client.post(f"/workflow/{existing_workflow_id}?workspace_id={existing_workspace_id}")
    assert_status_code(response.status_code, expected_floor=2)
    assert_job_id(response)


# NOTE: Duplications for Workspace/Workflow will be removed 
# when there is a single Resource Manager implemented

# Helper functions
def assert_status_code(status_code, expected_floor):
    status_floor = status_code // 100
    assert status_floor == expected_floor, f"response should have {expected_floor}xx status code"

def assert_workspaces_len(expected_len):
    response = client.get("/workspace")
    assert_status_code(response.status_code, expected_floor=2)
    response_len = len(response.json())
    assert expected_len == response_len, "more workspaces than expected existing"

def assert_workflows_len(expected_len):
    response = client.get("/workflow")
    assert_status_code(response.status_code, expected_floor=2)
    response_len = len(response.json())
    assert expected_len == response_len, "more workflows than expected existing"

def assert_workspace_dir(workspace_id):
    assert exists(join(constants.WORKSPACES_DIR, workspace_id)), "workspace-dir not existing"

def assert_workflow_dir(workflow_id):
    assert exists(join(constants.WORKFLOWS_DIR, workflow_id)), "workflow-dir not existing"

def assert_job_id(response):
    # Asserts that the job id is not an empty string
    assert not response.json()['@id'].split("/")[-1] == "", "job id was not assigned" 

# Extract the workspace id from a response
def get_workspace_id(response):
    return response.json()['@id'].split("/")[-1]

# Extract the workflow id from a response
def get_workflow_id(response):
    return response.json()['@id'].split("/")[-1]

# Find an existing workspace id
def find_workspace_id():
    response = client.get("/workspace")
    # Return the id of the first member in the workspace list
    if len(response.json()) > 0:
        existing_workspace_id = response.json()[0]['@id'].split("/")[-1]
    else:
        existing_workspace_id = "NO_WORKSPACES_AVAILABLE"
    return existing_workspace_id

# Find an existing workflow id
def find_workflow_id():
    response = client.get("/workflow")
    # Return the id of the first member in the workflow list
    if len(response.json()) > 0:
        existing_workflow_id = response.json()[0]['@id'].split("/")[-1]
    else:
        existing_workflow_id = "NO_WORKFLOWS_AVAILABLE"
    return existing_workflow_id

