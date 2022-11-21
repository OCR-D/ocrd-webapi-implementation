import os

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Header,
    HTTPException,
    status,
    UploadFile,
)
from fastapi.responses import FileResponse

from ocrd_utils import getLogger

from ocrd_webapi import database
from ocrd_webapi.models import (
    WorkspaceRsrc
)
from ocrd_webapi.utils import (
    ResponseException,
    safe_init_logging,
    WorkspaceException,
    WorkspaceNotValidException,
)
from ocrd_webapi.workspace_manager import (
    WorkspaceManager
)

router = APIRouter(
    tags=["Workspace"],
)
safe_init_logging()
log = getLogger('ocrd_webapi.workspace')
workspace_manager = WorkspaceManager()


# TODO: Refine all the exceptions...
@router.get("/workspace")
async def list_workspaces():
    """
    Get a list of existing workspace urls

    curl http://localhost:8000/workspace/
    """
    workspace_urls = workspace_manager.get_workspaces()
    response = []
    for ws in workspace_urls:
        response.append(WorkspaceRsrc(id=ws, description="Workspace"))
    return response

@router.get("/workspace/{workspace_id}")
async def get_workspace(background_tasks: BackgroundTasks, workspace_id: str, accept: str = Header(...)):
    """
    Get an existing workspace

    When testet with fastapi's interactive API docs / Swagger (e.g. http://127.0.0.1:8000/docs) the
    accept-header is allways set to application/json (no matter what is specified in the gui) so to
    test getting the workspace as a zip it cannot be used.
    See: https://github.com/OCR-D/ocrd-webapi-implementation/issues/2

    can be testet with:
    `curl http://localhost:8000/workspace/-the-id-of-ws -H "Accept: application/json"` and
    `curl http://localhost:8000/workspace/{ws-id} -H "Accept: application/vnd.ocrd+zip" -o foo.zip`
    """
    if accept == "application/json":
        workspace_url = workspace_manager.get_workspace_url(workspace_id)
        if not workspace_url:
            raise ResponseException(404, {})
        return WorkspaceRsrc(id=workspace_url, description="Workspace")
    elif accept == "application/vnd.ocrd+zip":
        bag_path = await workspace_manager.get_workspace_bag(workspace_id)
        if not bag_path:
            raise ResponseException(404, {})
        # Remove the produced bag after sending it in the response
        background_tasks.add_task(os.unlink, bag_path)
        return FileResponse(bag_path)
    else:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Unsupported media, expected application/json or application/vnd.ocrd+zip",
        )

@router.post("/workspace", responses={"201": {"model": WorkspaceRsrc}})
async def post_workspace(workspace: UploadFile):
    """
    Create a new workspace

    curl -X POST http://localhost:8000/workspace -H 'content-type: multipart/form-data' -F workspace=@things/example_ws.ocrd.zip  # noqa
    """
    try:
        workspace_url = await workspace_manager.create_workspace_from_zip(workspace)
    except WorkspaceNotValidException as e:
        raise ResponseException(422, {"error": "workspace not valid", "reason": str(e)})
    except Exception:
        log.exception("unexpected error in post_workspace")
        raise ResponseException(500, {"error": "internal server error"})

    return WorkspaceRsrc(id=workspace_url, description="Workspace")

@router.put("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def put_workspace(workspace: UploadFile, workspace_id: str):
    """
    Update or create a workspace
    """
    try:
        updated_workspace_url = await workspace_manager.update_workspace(workspace, workspace_id)
    except WorkspaceNotValidException as e:
        raise ResponseException(422, {"error": "workspace not valid", "reason": str(e)})
    except Exception:
        log.exception("unexpected error in put_workspace")
        raise ResponseException(500, {"error": "internal server error"})

    return WorkspaceRsrc(id=updated_workspace_url, description="Workspace")

@router.delete("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def delete_workspace(workspace_id: str):
    """
    Delete a workspace
    curl -v -X DELETE 'http://localhost:8000/workspace/put-workspace-id-here'
    """
    try:
        deleted_workspace_url = await workspace_manager.delete_workspace(workspace_id)
    except WorkspaceException:
        if await database.get_workspace(workspace_id):
            raise ResponseException(410, {})
        else:
            raise ResponseException(404, {})

    return WorkspaceRsrc(id=deleted_workspace_url, description="Workspace")
