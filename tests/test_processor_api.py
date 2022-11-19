import os.path
import pytest
import subprocess
from time import sleep

from ocrd_webapi import (
    constants,
)
from .utils_test import (
    assert_status_code,
    parse_resource_id,
)

@pytest.fixture(scope="session", autouse=True)
def do_around_tests():
    """
    when a processor runs in a docker containers files are created in the workspaces. These files
    belong to root and thus cannot be deleted with "normal" rigths. Because of that a docker-command
    is used to clean workspaces after the tests.
    """
    yield
    # constants.WORKSPACE_DIR - may not always be de default dir 
    # depending on the passed parameter to the WorkflowManager constructor.
    subprocess.run(["docker", "run", "--rm", "-v", f"{constants.WORKSPACES_DIR}:/workspaces",
                    "alpine", "find", "/workspaces", "-mindepth", "1", "-delete"])

# TODO: This should be better implemented...
def test_run_prcessor(client, dummy_workspace_id):
    # act
    new_file_grp = "OCR-D-DUMMY"
    params = {"input_file_grps": 'OCR-D-IMG', "output_file_grps": new_file_grp,
              "workspace_id": dummy_workspace_id, "parameters": {}}
    response = client.post("/processor/ocrd-dummy", json=params)

    assert_status_code(response.status_code, expected_floor=2)
    job_id = parse_resource_id(response)

    # try several times because finishing execution needs some time
    for x in range(0, 10):
        if client.get(f"processor/ocrd-dummy/{job_id}").json()['state'] in ['STOPPED', 'SUCCESS']:
            break
        sleep(0.5)

    path = os.path.join(constants.WORKSPACES_DIR, dummy_workspace_id, new_file_grp)
    assert os.path.exists(path), f"ouput_file_grp not created. expecting exists: '{path}'"
