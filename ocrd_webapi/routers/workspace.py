from fastapi import (
    APIRouter,
    BackgroundTasks,
    Header,
    HTTPException,
    status,
    UploadFile,
)
from fastapi.responses import FileResponse

# OCR-D core related imports
from ocrd_utils import getLogger

# OCR-D WebAPI related imports
from ocrd_webapi.models import (
    WorkspaceRsrc,
)
from ocrd_webapi.utils import (
    ResponseException,
    safe_init_logging,
    WorkspaceException,
    WorkspaceNotValidException,
)
from ocrd_webapi.workspace_manager import WorkspaceManager

from typing import (
    List,
    Union,
)


router = APIRouter(
    tags=["Workspace"],
)
safe_init_logging()
log = getLogger('ocrd_webapi.workspace')
workspace_manager = WorkspaceManager()


@router.get("/workspace")
async def get_workspaces() -> List[WorkspaceRsrc]:
    """
    Get a list of existing workspaces

    curl http://localhost:8000/workspace/
    """
    return workspace_manager.get_workspaces()

@router.get("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def get_workspace(background_tasks: BackgroundTasks, workspace_id: str, accept: str = Header(...)) -> Union[WorkspaceRsrc, FileResponse]:
    """
    Get an existing workspace

    can be testet with:
    `curl http://localhost:8000/workspace/-the-id-of-ws -H "Accept: application/json"` and
    `curl http://localhost:8000/workspace/{ws-id} -H "Accept: application/vnd.ocrd+zip" -o foo.zip`
    """
    if accept == "application/json":
        workspace = workspace_manager.get_workspace_rsrc(workspace_id)
        if not workspace:
            raise ResponseException(404, {})
        return workspace
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
async def post_workspace(workspace: UploadFile) -> Union[None, WorkspaceRsrc]:
    """
    Create a new workspace

    curl -X POST http://localhost:8000/workspace -H 'content-type: multipart/form-data' -F workspace=@things/example_ws.ocrd.zip  # noqa
    """
    try:
        return await workspace_manager.create_workspace_from_zip(workspace)
    except WorkspaceNotValidException as e:
        raise ResponseException(422, {"error": "workspace not valid", "reason": str(e)})
    except Exception:
        log.exception("unexpected error in post_workspace")
        raise ResponseException(500, {"error": "internal server error"})

@router.put("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def put_workspace(workspace: UploadFile, workspace_id: str) -> WorkspaceRsrc:
    """
    Update or create a workspace
    """
    try:
        return await workspace_manager.update_workspace(workspace, workspace_id)
    except WorkspaceNotValidException as e:
        raise ResponseException(422, {"error": "workspace not valid", "reason": str(e)})
    except Exception:
        log.exception("unexpected error in put_workspace")
        raise ResponseException(500, {"error": "internal server error"})

@router.delete("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def delete_workspace(workspace_id: str) -> WorkspaceRsrc:
    """
    Delete a workspace
    curl -v -X DELETE 'http://localhost:8000/workspace/put-workspace-id-here'
    """
    try:
        return await workspace_manager.delete_workspace(workspace_id)
    except WorkspaceException:
        if await database.get_workspace(workspace_id):
            raise ResponseException(410, {})
        else:
            raise ResponseException(404, {})
