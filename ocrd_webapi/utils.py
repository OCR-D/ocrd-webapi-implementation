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
]


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


class WorkspaceNotValidException(Exception):
    pass