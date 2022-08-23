import os
from .constants import (
    WORKSPACES_DIR,
    WORKFLOWS_DIR,
)
from enum import Enum
from typing import Union

__all__ = [
    "ResponseException",
    "JobState",
    "to_processor_job_dir",
    "to_workflow_job_dir",
    "WorkspaceException",
    "WorkspaceNotValidException",
    "WorkspaceGoneException",
    "read_baginfos_from_zip",

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


def to_processor_job_dir(job_id) -> str:
    """
    returns path to processor-job which is saved as json-txt
    """
    return os.path.join(WORKSPACES_DIR, job_id)


def to_workflow_job_dir(workflow_id) -> str:
    """
    returns path to workflow-job which is saved as json-txt
    """
    return os.path.join(WORKFLOWS_DIR, workflow_id)


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
