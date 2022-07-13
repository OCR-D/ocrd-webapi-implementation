"""
Test-implementation of ocrd webApi: https://github.com/OCR-D/spec/blob/master/openapi.yml
"""
import datetime
import os
from ocrd_utils import getLogger, initLogging
from typing import Union, List
from fastapi.responses import FileResponse

from fastapi import FastAPI, UploadFile, Request, Header, HTTPException, status
from fastapi.responses import JSONResponse
from ocrd_webapi.models import (
    WorkspaceRsrc,
)
from ocrd_webapi.utils import (
    ResponseException,
)
from ocrd_webapi.constants import (
    SERVER_PATH,
    WORKSPACES_DIR,
)
from ocrd_webapi.workspace_manager import WorkspaceManager


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
initLogging()
log = getLogger('ocrd_webapi.main')
workspace_manager = WorkspaceManager(WORKSPACES_DIR)


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


@app.get("/")
async def test():
    """
    to test if server is running on root-path
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


@app.get("/workspace")
async def get_workspaces() -> List[WorkspaceRsrc]:
    """
    Get a list of existing workspaces

    curl http://localhost:8000/workspace/
    """
    return workspace_manager.get_workspaces()


# noinspection PyBroadException TODO: remove
@app.post("/workspace", responses={"201": {"model": WorkspaceRsrc}})
async def post_workspace(workspace: UploadFile) -> Union[None, WorkspaceRsrc]:
    """
    Create a new workspace

    curl -X POST http://localhost:8000/workspace -H 'content-type: multipart/form-data' -F file=@things/example_ws.ocrd.zip  # noqa
    """
    try:
        return await workspace_manager.create_workspace_from_zip(workspace)
    except Exception:
        # TODO: exception mapping to repsonse code:
        #   - return 422 if workspace invalid etc.
        #   - return 500 for unexpected errors
        log.exception("error in post_workspace")
        return None


@app.get("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def get_workspace(workspace_id: str, content_type: str = Header(...)) -> WorkspaceRsrc:
    """
    Get an existing workspace

    curl http://localhost:8000/workspace/-the-id-of-ws -H "content-type: application/json"
    curl http://localhost:8000/workspace/-the-id-of-ws -H "content-type: application/vnd.ocrd+zip"
        --output test-ocrd-bag.zip
    """
    if content_type == "application/json":
        workspace = workspace_manager.get_workspace_rsrc(workspace_id)
        if not workspace:
            raise ResponseException(404, {})
        return workspace
    elif content_type == "application/vnd.ocrd+zip":
        workspace = workspace_manager.get_workspace_bag(workspace_id)
        if not workspace:
            raise ResponseException(404, {})
        return FileResponse(workspace)
    else:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported media, expected application/json or application/vnd.ocrd+zip",
        )


@app.get("/workspace2/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def get_workspace_as_bag(workspace_id: str) -> WorkspaceRsrc:
    """
    draft

    return workspace as bagit

    curl http://localhost:8000/workspace2/the-id-of-ws
    """
    bag_path = workspace_manager.get_workspace_bag(workspace_id)
    if not bag_path:
        raise ResponseException(404)
    # TODO: remove bag after dispatch with workspace_manager.delete_workspace_bag() use
    #       fast-api-background-tasks for that:
    #       https://fastapi.tiangolo.com/tutorial/background-tasks/
    return FileResponse(bag_path)


@app.delete("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def delete_workspace(workspace_id: str) -> WorkspaceRsrc:
    """
    Delete a workspace
    TODO: curl-command to do it
    TODO: what about 410 (Gone), specified in API:
        - (how to) keep track of deleted workspaces?
            - create a Database with information about workspaces? Could be usefull for other tasks
              too
            - keep empty Directories of deleted workspaces for a while?
    """
    workspace = workspace_manager.delete_workspace(workspace_id)
    if not workspace:
        raise ResponseException(404, {})
    return workspace


@app.put("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def put_workspace(workspace: UploadFile, workspace_id: str) -> WorkspaceRsrc:
    """
    Update or create a workspace
    """
    try:
        return await workspace_manager.update_workspace(workspace, workspace_id)
    except Exception:
        # TODO: exception mapping to repsonse code:
        #   - return 422 if workspace invalid etc.
        #   - return 500 for unexpected errors
        log.exception("error in put_workspace")
        return None
