from os import unlink
from typing import List, Union
import logging

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Header,
    HTTPException,
    status,
    UploadFile,
)
from fastapi.responses import FileResponse
from ocrd_webapi.exceptions import (
    ResponseException,
    WorkspaceException,
    WorkspaceGoneException,
    WorkspaceNotValidException,
)
from ocrd_webapi.managers.workspace_manager import WorkspaceManager
from ocrd_webapi.models.workspace import WorkspaceRsrc
from ocrd_webapi.utils import safe_init_logging

router = APIRouter(
    tags=["Workspace"],
)

safe_init_logging()

# TODO: More flexible configuration for logging level should be possible
logger = logging.getLogger(__name__)
logging.getLogger(__name__).setLevel(logging.INFO)
workspace_manager = WorkspaceManager()


# TODO: Refine all the exceptions...
@router.get("/workspace")
async def list_workspaces() -> List[WorkspaceRsrc]:
    """
    Get a list of existing workspace urls

    curl http://localhost:8000/workspace/
    """
    workspace_urls = workspace_manager.get_workspaces()
    response = []
    for ws_url in workspace_urls:
        response.append(WorkspaceRsrc.create(workspace_url=ws_url))
    return response


@router.get("/workspace/{workspace_id}")
async def get_workspace(
        background_tasks: BackgroundTasks,
        workspace_id: str,
        accept: str = Header(...)
) -> Union[WorkspaceRsrc, FileResponse, ResponseException]:
    """
    Get an existing workspace

    When tested with FastAPI's interactive API docs / Swagger (e.g. http://127.0.0.1:8000/docs) the
    accept-header is always set to application/json (no matter what is specified in the gui) so to
    test getting the workspace as a zip it cannot be used.
    See: https://github.com/OCR-D/ocrd-webapi-implementation/issues/2

    can be tested with:
    `curl http://localhost:8000/workspace/-the-id-of-ws -H "accept: application/json"` and
    `curl http://localhost:8000/workspace/{ws-id} -H "accept: application/vnd.ocrd+zip" -o foo.zip`
    """
    if accept == "application/json":
        workspace_url = workspace_manager.get_resource(workspace_id, local=False)
        if workspace_url:
            return WorkspaceRsrc.create(workspace_url=workspace_url)
        raise ResponseException(404, {})
    if accept == "application/vnd.ocrd+zip":
        bag_path = await workspace_manager.get_workspace_bag(workspace_id)
        if bag_path:
            # Remove the produced bag after sending it in the response
            background_tasks.add_task(unlink, bag_path)
            return FileResponse(bag_path)
        raise ResponseException(404, {})
    raise HTTPException(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "Unsupported media, expected application/json \
        or application/vnd.ocrd+zip",
    )


@router.post("/workspace", responses={"201": {"model": WorkspaceRsrc}})
async def post_workspace(workspace: UploadFile) -> Union[WorkspaceRsrc, ResponseException]:
    """
    Create a new workspace

    curl -X POST http://localhost:8000/workspace -H 'content-type: multipart/form-data' -F workspace=@things/example_ws.ocrd.zip  # noqa
    """
    try:
        ws_url, ws_id = await workspace_manager.create_workspace_from_zip(workspace)
    except WorkspaceNotValidException as e:
        raise ResponseException(422, {"error": "workspace not valid", "reason": str(e)})
    except Exception as e:
        logger.exception(f"Unexpected error in post_workspace: {e}")
        raise ResponseException(500, {"error": "internal server error"})

    return WorkspaceRsrc.create(workspace_url=ws_url)


@router.put("/workspace/{workspace_id}", responses={"201": {"model": WorkspaceRsrc}})
async def put_workspace(workspace: UploadFile, workspace_id: str) -> Union[WorkspaceRsrc, ResponseException]:
    """
    Update or create a workspace
    """
    try:
        updated_workspace_url = await workspace_manager.update_workspace(file=workspace, workspace_id=workspace_id)
    except WorkspaceNotValidException as e:
        raise ResponseException(422, {"error": "workspace not valid", "reason": str(e)})
    except Exception as e:
        logger.exception(f"Unexpected error in put_workspace: {e}")
        raise ResponseException(500, {"error": "internal server error"})

    return WorkspaceRsrc.create(workspace_url=updated_workspace_url)


@router.delete("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def delete_workspace(workspace_id: str) -> Union[WorkspaceRsrc, ResponseException]:
    """
    Delete a workspace
    curl -v -X DELETE 'http://localhost:8000/workspace/{workspace_id}'
    """
    try:
        deleted_workspace_url = await workspace_manager.delete_workspace(
            workspace_id
        )
    except WorkspaceGoneException:
        raise ResponseException(410, {})
    except WorkspaceException:
        raise ResponseException(404, {})

    return WorkspaceRsrc.create(workspace_url=deleted_workspace_url)
