"""
tests for ocrd_webapi.routers.processor.py
"""
import os.path

import pytest
import subprocess
from ocrd_webapi import (
    constants,
    utils
)
from time import sleep

@pytest.fixture(scope="session", autouse=True)
def do_around_tests():
    """
    when a processor runs in a docker containers files are created in the workspaces. These files
    belong to root and thus cannot be deleted with "normal" rigths. Because of that a docker-command
    is used to clean workspaces after the tests.
    """
    yield
    subprocess.run(["docker", "run", "--rm", "-v", f"{constants.WORKSPACES_DIR}:/workspaces",
                    "alpine", "find", "/workspaces", "-mindepth", "1", "-delete"])


def test_run_prcessor(client, dummy_workspace_id):
    # act
    new_file_grp = "OCR-D-DUMMY"
    params = {"input_file_grps": 'OCR-D-IMG', "output_file_grps": new_file_grp,
              "workspace_id": dummy_workspace_id, "parameters": {}}
    resp = client.post("/processor/ocrd-dummy", json=params)

    # assert
    assert resp.status_code // 100 == 2, f"run-processor returned error-code: {resp.status_code}"
    job_id = resp.json()['@id'].split("/")[-1]
    for x in range(0, 10):
        # try several times because finishing execution needs some time
        if client.get(f"processor/ocrd-dummy/{job_id}").json()['state'] in ['STOPPED', 'SUCCESS']:
            break
        sleep(0.5)
    path = os.path.join(utils.to_workspace_dir(dummy_workspace_id), new_file_grp)
    assert os.path.exists(path), f"ouput_file_grp not created. expecting exists: '{path}'"
