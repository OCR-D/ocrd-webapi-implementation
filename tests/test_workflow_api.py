from time import sleep

from .asserts_test import (
    assert_db_entry_created,
    assert_status_code,
    assert_workflow_dir
)
from .utils_test import (
    parse_resource_id,
    parse_job_state,
)


def test_post_workflow_script_unauthorized(client, auth, workflow_mongo_coll, asset_workflow1):
    response = client.post("/workflow", files=asset_workflow1, auth=("no_user", "no_pass"))
    assert_status_code(response.status_code, expected_floor=4)


# Test cases
def test_post_workflow_script(client, auth, workflow_mongo_coll, asset_workflow1):
    # Post a new workflow script
    response = client.post("/workflow", files=asset_workflow1, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    workflow_id = parse_resource_id(response)
    assert_workflow_dir(workflow_id)

    # Database checks
    workflow_from_db = workflow_mongo_coll.find_one(
        {"workflow_id": workflow_id}
    )
    assert_db_entry_created(workflow_from_db, workflow_id, db_key="workflow_id")


def test_put_workflow_script(client, auth, workflow_mongo_coll, asset_workflow1, asset_workflow2):
    # Post a new workflow script
    response = client.post("/workflow", files=asset_workflow1, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    workflow_id = parse_resource_id(response)
    assert_workflow_dir(workflow_id)
    workflow_from_db = workflow_mongo_coll.find_one(
        {"workflow_id": workflow_id}
    )
    assert_db_entry_created(workflow_from_db, workflow_id, db_key="workflow_id")
    workflow_dir_path1 = workflow_from_db["workflow_path"]
    workflow_path1 = workflow_from_db["workflow_script_path"]
    assert workflow_dir_path1, "Failed to extract workflow dir path 1"
    assert workflow_path1, "Failed to extract workflow path 1"

    # Put to the same workflow_id
    request = f"/workflow/{workflow_id}"
    response = client.put(request, files=asset_workflow2, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    workflow_id = parse_resource_id(response)
    assert_workflow_dir(workflow_id)
    workflow_from_db = workflow_mongo_coll.find_one(
        {"workflow_id": workflow_id}
    )
    assert_db_entry_created(workflow_from_db, workflow_id, db_key="workflow_id")
    workflow_dir_path2 = workflow_from_db["workflow_path"]
    workflow_path2 = workflow_from_db["workflow_script_path"]
    assert workflow_dir_path2, "Failed to extract workflow dir path 1"
    assert workflow_path2, "Failed to extract workflow path 1"

    assert workflow_dir_path1 == workflow_dir_path2, \
        f"Workflow dir paths should match, but does not: {workflow_dir_path1} != {workflow_dir_path2}"
    assert workflow_path1 != workflow_path2, \
        f"Workflow paths should not, but match: {workflow_path1} == {workflow_path2}"


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
    assert response.headers.get('content-disposition').find(".nf") > -1, \
        "filename should have the '.nf' extension"


def test_run_workflow(client, auth, dummy_workflow_id, dummy_workspace_id, workflow_job_mongo_coll):
    params = {"workspace_id": dummy_workspace_id}
    response = client.post(f"/workflow/{dummy_workflow_id}", json=params, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    job_id = parse_resource_id(response)
    assert job_id
    workflow_job_from_db = workflow_job_mongo_coll.find_one(
        {"workflow_job_id": job_id}
    )
    assert_db_entry_created(workflow_job_from_db, job_id, db_key="workflow_job_id")


def test_run_workflow_different_mets(client, auth, dummy_workflow_id, asset_workspace3, workflow_job_mongo_coll):
    # The name of the mets file is not `mets.xml` inside the provided workspace
    response = client.post("/workspace", files=asset_workspace3, auth=auth)
    workspace_id = parse_resource_id(response)
    params = {"workspace_id": workspace_id}
    response = client.post(f"/workflow/{dummy_workflow_id}", json=params, auth=auth)
    assert_status_code(response.status_code, expected_floor=2)
    job_id = parse_resource_id(response)
    assert job_id

    workflow_job_from_db = workflow_job_mongo_coll.find_one(
        {"workflow_job_id": job_id}
    )
    assert_db_entry_created(workflow_job_from_db, job_id, db_key="workflow_job_id")

    # TODO: assert the workflow finished successfully. Currently mets.xml is not dynamic, so first
    #  the possibility to provide a different-mets-name to run the workflow has to be implemented


# TODO: This should be better implemented...
def test_workflow_job_status(client, auth, dummy_workflow_id, dummy_workspace_id):
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
