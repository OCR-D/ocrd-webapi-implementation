import os
import asyncio
import uuid
import json
from .constants import (
    SERVER_PATH,
    WORKSPACES_DIR,
)
from enum import Enum
from typing import Dict, Union

__all__ = [
    "ResponseException",
    "JobState",
    "to_workspace_url",
    "to_workspace_dir",
    "to_processor_job_dir",
    "create_processor_job",
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


async def validate_workspace(uuid) -> bool:
    """
    validate workspace with ocrd-docker and return true if valid
    """
    pcall = ["docker", "run", "--rm", "--workdir", "/data", "--volume",
             f"{to_workspace_dir(uuid)}/data:/data", "--", "ocrd/all:medium", "ocrd", "workspace",
             "validate"]
    proc = await asyncio.create_subprocess_exec(*pcall)
    await proc.communicate()

    return proc.returncode == 0


def to_processor_job_dir(job_id) -> str:
    """
    returns path to processor-job which is saved as json-txt
    """
    return os.path.join(WORKSPACES_DIR, job_id)


def create_processor_job(executable, workspace_id) -> Dict:
    """
    create a new ProcessorJob and save it to disk
    """
    uid = str(uuid.uuid4())
    document = {
        "@id": uid,  # TODO: change to url where job can be retrieved (create func like for a ws)
        "description": "ProcessorJob",
        "state": JobState.RUNNING.name,
        "processor": "TODO: put URL here",
        "workspace": {
            "@id": to_workspace_url(workspace_id),
            "description": "Workspace",
        }
    }
    with open(to_processor_job_dir(uid), 'w') as fptr:
        json.dump(document, fptr)
    return document
