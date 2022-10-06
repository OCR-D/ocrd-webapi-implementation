import os
from .constants import (
    WORKSPACES_DIR,
    WORKFLOWS_DIR,
    SERVER_PATH,
)
from enum import Enum
from typing import Union

__all__ = [
    "ResponseException",
    "JobState",
    "to_workflow_job_dir",
    "to_workspace_url",
    "to_workspace_dir",
    "to_workflow_url",
    "WorkspaceException",
    "WorkspaceNotValidException",
    "WorkspaceGoneException",
    "read_baginfos_from_zip",
    "safe_init_logging",
    "to_workflow_job_url",
    "to_workflow_url",
    "WorkflowJobException",
]
import zipfile
import bagit
import tempfile
from ocrd_utils import initLogging


class ResponseException(Exception):
    """
    Exception to return a response
    """
    def __init__(self, status_code: int, body: Union[dict, None] = None):
        self.status_code = status_code
        self.body = body


class JobState(Enum):
    QUEUED = 1
    RUNNING = 2
    STOPPED = 3


def to_workflow_job_dir(workflow_id, job_id) -> str:
    """
    returns path to workflow-job directory
    """
    return os.path.join(WORKFLOWS_DIR, workflow_id, job_id)


def to_workspace_url(workspace_id: str) -> str:
    """
    create the url where workspace is available e.g. http://localhost:8000/workspace/{workspace_id}

    does not verify that the workspace_id exists
    """
    return f"{SERVER_PATH}/workspace/{workspace_id}"


def to_workspace_dir(workspace_id: str) -> str:
    """
    return path to workspace with id `workspace_id`. No check if existing
    """
    return os.path.join(WORKSPACES_DIR, workspace_id)


def to_workflow_url(workflow_id: str) -> str:
    """
    create the url where a workflow is available e.g. http://localhost:8000/workflow/{workflow_id}

    does not verify that the workflow_id exists
    """
    return f"{SERVER_PATH}/workflow/{workflow_id}"


def to_workflow_job_url(workflow_id: str, job_id: str) -> str:
    return f"{SERVER_PATH}/workflow/{workflow_id}/{job_id}"


def to_processor_job_url(processor_name: str, job_id: str) -> str:
    """
    create the url where the processor job is available e.g. http://localhost:8000/processor/ocrd-dummy/{job_id}

    does not verify that the proessor or/and the processor-job exists
    """
    return f"{SERVER_PATH}/processor/{processor_name}/{job_id}"


logging_initialized = False


def safe_init_logging() -> None:
    """
    wrapper around ocrd_utils.initLogging. It assures that ocrd_utils.initLogging is only called
    once. This function may be called mutliple times
    """
    global logging_initialized
    if not logging_initialized:
        logging_initialized = True
        initLogging()


class WorkspaceException(Exception):
    """
    Exception to indicate something is wrong with the workspace
    """
    pass


class WorkspaceNotValidException(WorkspaceException):
    pass


class WorkspaceGoneException(WorkspaceException):
    pass


class WorkflowJobException(Exception):
    """
    Exception to indicate something is wrong with a workflow-job
    """
    pass


def read_baginfos_from_zip(path_to_zip) -> dict:
    """
    Extracts bag-info.txt from bagit-file and turns it into a dict

    Args:
        path_to_zip: path to bagit-file

    Returns:
        bag-info.txt from bagit as a dict
    """
    with zipfile.ZipFile(path_to_zip, 'r') as z:
        bag_info_bytes = z.read("bag-info.txt")
        with tempfile.NamedTemporaryFile() as tmp:
            with open(tmp.name, 'wb') as f:
                f.write(bag_info_bytes)
            return bagit._load_tag_file(tmp.name)
