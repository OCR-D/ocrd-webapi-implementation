"""
tests for ocrd_webapi.routers.processor.py
"""
import os.path

import pytest
import subprocess
from ocrd_webapi import constants


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


def test_run_prcessor(client, dummy_workspace):
    # act
    new_file_grp = "OCR-D-DUMMY"
    params = {"input_file_grps": 'OCR-D-IMG', "output_file_grps": new_file_grp,
              "workspace_id": dummy_workspace, "parameters": {}}
    resp = client.post(f"/processor/ocrd-dummy", json=params)
    # assert
    assert resp.status_code // 100 == 2, f"run-processor returned error-code: {resp.status_code}"



