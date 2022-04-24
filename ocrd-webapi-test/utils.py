import os
import asyncio
from .constants import (
    SERVER_PATH,
    WORKSPACES_DIR,
)


class ResponseException(Exception):
    """
    Exception to return a response
    """
    def __init__(self, status_code: int, body: dict | None = None):
        self.status_code = status_code
        self.body = body


def to_workspace_url(workspace_id: str) -> str:
    """
    create url where workspace is available
    """
    return f"{SERVER_PATH}/workspace/{workspace_id}"


def to_workspace_dir(workspace_id: str) -> str:
    """
    return path to workspace with id `workspace_id`. No check if existing
    """
    return os.path.join(WORKSPACES_DIR, workspace_id)


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