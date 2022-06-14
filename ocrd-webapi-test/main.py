"""
Test-implementation of ocrd webApi: https://github.com/OCR-D/spec/blob/master/openapi.yml
"""
import datetime
import os
import subprocess
import uuid
import asyncio
import functools
from typing import List

from fastapi import FastAPI, UploadFile, File, Path, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseSettings
import aiofiles
import psutil
from .models import (
    DiscoveryResponse,
    Workspace,
    Processor,
    ProcessorJob,
    ProcessorArgs,
)
from .utils import (
    to_workspace_url,
    to_workspace_dir,
    ResponseException,
    validate_workspace
)
from .constants import (
    SERVER_PATH,
    WORKSPACES_DIR,
    JOB_DIR,
    WORKSPACE_ZIPNAME,
)
from workflow_service import WorkflowService
from workspace_service import WorkspaceService
from discovery_service import DiscoveryService


app = FastAPI(
    title="OCR-D Web API",
    description="HTTP API for offering OCR-D processing",
    contact={"email": "test@example.com"},
    license={
        "name": "Apache 2.0",
        "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
    },
    version="0.0.1",
    servers=[
        {
            "url": SERVER_PATH,
            "description": "The URL of your server offering the OCR-D API.",
        }
    ],
)
discovery_service = DiscoveryService()
workspace_service = WorkspaceService()
worfklow_service = WorkflowService()

@app.exception_handler(ResponseException)
async def exception_handler_empty404(request: Request, exc: ResponseException):
    """
    Exception-Handler needed to return Empty 404 JSON repsonse
    """
    return JSONResponse(status_code=exc.status_code, content={} if not exc.body else exc.body)


@app.on_event("startup")
async def startup_event():
    """
    Executed once on startup
    """
    os.makedirs(WORKSPACES_DIR, exist_ok=True)
    os.makedirs(JOB_DIR, exist_ok=True)


@app.get("/")
async def test():
    """
    to test if server is running on root-path
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


@app.get("/discovery", response_model=DiscoveryResponse)
async def discovery() -> DiscoveryResponse:
    """
    Discovery of capabilities of the server
    """
    # TODO: what is the meaning of `has_ocrd_all` and `has_docker`? If docker is used,
    #       (I plan to use docker `ocrd/all:medium` container) does this mean has_docker and
    #       has_ocrd_all  must both be true?
    return discovery_service.discovery()


@app.get("/workspace", response_model=List[Workspace])
def get_workspaces() -> List[Workspace]:
    """
    Return a list of all existing workspaces
    """
    workspace_service.get_workspace()



@app.get('/workspace/{workspace_id}', response_model=Workspace)
def get_workspace(workspace_id: str) -> Workspace:
    """
    Test if workspace exists
    """
    if not os.path.exists(to_workspace_dir(workspace_id)):
        raise ResponseException(404)
    return Workspace(id=to_workspace_url(workspace_id), description="Workspace")


@app.post("/workspace", response_model=None, responses={"201": {"model": Workspace}})
async def post_workspace(file: UploadFile = File(...)) -> None | Workspace:
    """
    Create a new workspace
    """
    uid = str(uuid.uuid4())
    workspace_dir = to_workspace_dir(uid)
    os.mkdir(workspace_dir)
    dest = os.path.join(workspace_dir, WORKSPACE_ZIPNAME)

    async with aiofiles.open(dest, "wb") as fpt:
        while content := await file.read(1024):
            await fpt.write(content)

    proc = await asyncio.create_subprocess_exec("unzip", dest, "-d", workspace_dir,
                                                stdout=subprocess.DEVNULL)
    await proc.communicate()
    os.remove(dest)

    if not await validate_workspace(uid):
        raise ResponseException(400, {"description": "Invalid workspace"})

    return Workspace(id=to_workspace_url(uid), description="Workspace")