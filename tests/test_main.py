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


@pytest.fixture(autouse=True)
def run_around_tests(mongo_client):
    # Before each test (until yield):
    mongo_client[constants.MONGO_TESTDB]["workspace"].delete_many({})
    yield
    # After each test:


def test_upload_workflow_script(utils, client, auth):
    nextflow_script = {'nextflow_script': open(utils.to_asset_path("nextflow.nf"), 'rb')}
    response = client.post("/workflow", files=nextflow_script, auth=auth)
    workflow_id = get_workflow_id(response)
    assert_status_code(response.status_code, expected_floor=2)
    assert_workflow_dir(workflow_id)


def test_get_workflow_script(utils, client, auth):
    nextflow_script = {'nextflow_script': open(utils.to_asset_path("nextflow.nf"), 'rb')}
    client.post("/workflow", files=nextflow_script, auth=auth)
    existing_workflow_id = find_workflow_id(client)
    response = client.get(f"/workflow/{existing_workflow_id}",
                          headers={"accept": "text/vnd.ocrd.workflow"})
    assert_status_code(response.status_code, expected_floor=2)
    assert_workflow_dir(existing_workflow_id)


def test_update_workflow_script(utils, client, auth):
    nextflow_script = {'nextflow_script': open(utils.to_asset_path("nextflow-simple.nf"), 'rb')}
    existing_workflow_id = find_workflow_id(client)
    response = client.put(f"/workflow/{existing_workflow_id}", files=nextflow_script, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    assert_workflow_dir(existing_workflow_id)


def test_start_workflow_script(client, dummy_workspace, dummy_workflow, auth):
    # WorkflowArgs were removed, the line below does not work anymore
    # response = client.post(f"/workflow/{dummy_workflow}", json={"workspace_id": dummy_workspace}, auth=auth)
    response = client.post(f"/workflow/{dummy_workflow}?workspace_id={dummy_workspace}", auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    assert_job_id(response)


# NOTE: Duplications for Workspace/Workflow will be removed
# when there is a single Resource Manager implemented

# Helper functions
# TODO: think about moving helper functions to conftest.Utils or another place
def assert_status_code(status_code, expected_floor):
    status_floor = status_code // 100
    assert status_floor == expected_floor, f"response should have {expected_floor}xx status code"


def assert_workspaces_len(expected_len, client):
    response = client.get("/workspace")
    assert_status_code(response.status_code, expected_floor=2)
    response_len = len(response.json())
    assert expected_len == response_len, "more workspaces than expected existing"


def assert_workflows_len(expected_len, client):
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


def get_workspace_id(response):
    """Extract the workspace id from a response"""
    return response.json()['@id'].split("/")[-1]


def get_workflow_id(response):
    """Extract the workflow id from a response"""
    return response.json()['@id'].split("/")[-1]


def find_workspace_id(client):
    """Find an existing workspace id"""
    response = client.get("/workspace")
    # Return the id of the first member in the workspace list
    if len(response.json()) > 0:
        existing_workspace_id = response.json()[0]['@id'].split("/")[-1]
    else:
        existing_workspace_id = "NO_WORKSPACES_AVAILABLE"
    return existing_workspace_id


def find_workflow_id(client):
    """Find an existing workflow id"""
    response = client.get("/workflow")
    # Return the id of the first member in the workflow list
    if len(response.json()) > 0:
        existing_workflow_id = response.json()[0]['@id'].split("/")[-1]
    else:
        existing_workflow_id = "NO_WORKFLOWS_AVAILABLE"
    return existing_workflow_id


def test_post_workspace(utils, workspace_mongo_coll, client):
    # arrange
    file = {'workspace': open(utils.to_asset_path("example_ws.ocrd.zip"), 'rb')}

    # act
    response = client.post("/workspace", files=file)

    # assert
    assert_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['@id'].split("/")[-1]
    assert_workspace_dir(workspace_id)

    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_from_db, "workspace-entry was not created in mongodb"
    db_id = workspace_from_db["_id"]
    assert db_id == workspace_id, f"wrong workspace id. Expected: {workspace_id}, found {db_id}"


def test_put_workspace(utils, workspace_mongo_coll, client):
    # arrange
    file1 = {'workspace': open(utils.to_asset_path("example_ws.ocrd.zip"), 'rb')}
    file2 = {'workspace': open(utils.to_asset_path("example_ws2.ocrd.zip"), 'rb')}
    test_id = "workspace_put_test_id"

    # act part 1
    response1 = client.put(f"/workspace/{test_id}", files=file1)

    # assert first workspace was created (put) correctly
    assert response1.status_code == 200, "response1 should have 2xx status code"
    assert exists(join(constants.WORKSPACES_DIR, test_id)), "workspace-dir not existing"

    # assert workspace created in mongodb
    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_from_db, "workspace-entry was not created in mongodb"
    db_id = workspace_from_db["_id"]
    assert db_id == test_id, f"wrong workspace id. Expected: {test_id}, found {db_id}"
    ocrd_identifier1 = workspace_from_db["ocrd_identifier"]

    # act part 2
    response2 = client.put(f"/workspace/{test_id}", files=file2)
    assert response2.status_code == 200, "response2 should have 2xx status code"

    # assert workspace updated correctly in mongodb
    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_mongo_coll.count_documents({}) == 1, "expect exactly 1 workspace in db"
    ocrd_identifier2 = workspace_from_db["ocrd_identifier"]
    assert ocrd_identifier1 and ocrd_identifier2 and ocrd_identifier1 != ocrd_identifier2, (
        "put_workspace didn't update the workspace in the database. ocrd_identifier1: "
        f"{ocrd_identifier1}. ocrd_identifier2: {ocrd_identifier2}"
    )
    # assert workspace updated correctly on disk
    mets_path = join(constants.WORKSPACES_DIR, test_id, "mets.xml")
    with open(mets_path) as fin:
        assert WORKSPACE_2_ID in fin.read(), "expected string '%s' in metsfile" % WORKSPACE_2_ID


def test_delete_workspaces(utils, workspace_mongo_coll, client):
    # arrange
    file = {'workspace': open(utils.to_asset_path("example_ws.ocrd.zip"), 'rb')}
    response = client.post("/workspace", files=file)
    workspace_id = response.json()['@id'].split("/")[-1]
    assert exists(join(constants.WORKSPACES_DIR, workspace_id)), "workspace-dir not existing"

    # act
    response = client.delete(f"/workspace/{workspace_id}")
    assert response.status_code == 200, "response should have 2xx status code"

    # assert
    workspace_mongo_coll.find_one()
    assert not exists(join(constants.WORKSPACES_DIR, workspace_id)), "workspace-dir still existing"
    workspace_from_db = workspace_mongo_coll.find_one()
    assert workspace_from_db, "workspace-entry not existing but should still exist."
    assert workspace_from_db["deleted"], "deleted-flag of workspace should be set to true"


def test_delete_previous_existing_workspaces(utils, workspace_mongo_coll, client):
    # arrange
    file = {'workspace': open(utils.to_asset_path("example_ws.ocrd.zip"), 'rb')}
    response = client.post("/workspace", files=file)
    workspace_id = response.json()['@id'].split("/")[-1]

    # act
    response = client.delete(f"/workspace/{workspace_id}")
    assert response.status_code == 200, "response should have 2xx status code"

    # assert
    response = client.delete(f"/workspace/{workspace_id}")
    assert response.status_code == 410, "response should have 410 status code"


def test_job_status(client, dummy_workspace, dummy_workflow):
    # arrange
    # WorkflowArgs were removed, the line below does not work anymore
    # response = client.post(f"/workflow/{dummy_workflow}", json={"workspace_id": dummy_workspace})
    response = client.post(f"/workflow/{dummy_workflow}?workspace_id={dummy_workspace}")
    job_id = response.json()['@id'].split("/")[-1]
    print(response.json())

    # act
    for x in range(0,20):
        # try several times because finishing execution needs some time
        response = client.get(f"workflow/{dummy_workflow}/{job_id}")
        state = response.json()['state']
        if state == 'STOPPED':
            break
        sleep(0.5)

    # assert
    assert state == 'STOPPED', f"expecting job.state to be set to stopped but is {state}"
