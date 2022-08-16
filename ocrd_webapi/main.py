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
    WorkflowRsrc,
)
from ocrd_webapi.utils import (
    ResponseException,
    WorkspaceNotValidException,
)
from ocrd_webapi.constants import (
    SERVER_PATH,
    WORKSPACES_DIR,
    WORKFLOWS_DIR,
    DB_URL,
)
from ocrd_webapi.workspace_manager import WorkspaceManager
from ocrd_webapi.workflow_manager import WorkflowManager
from ocrd_webapi.database import initiate_database


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
workflow_manager = WorkflowManager(WORKFLOWS_DIR)


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
    os.makedirs(WORKFLOWS_DIR, exist_ok=True)
    await initiate_database(DB_URL)


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

    curl -X POST http://localhost:8000/workspace -H 'content-type: multipart/form-data' -F workspace=@things/example_ws.ocrd.zip  # noqa
    """
    try:
        return await workspace_manager.create_workspace_from_zip(workspace)
    except WorkspaceNotValidException:
        # TODO: give hints for cause of validation error to user.
        # Therefore add attr to WorkspaceNotValidException and put that into response json
        raise ResponseException(422, {"error": "workspace not valid"})
    except Exception:
        log.exception("unexpected error in post_workspace")
        raise ResponseException(500, {"error": "internal server error"})


@app.get("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def get_workspace(workspace_id: str, accept: str = Header(...)) -> WorkspaceRsrc:
    """
    Get an existing workspace

    can be testet with:
    `curl http://localhost:8000/workspace/-the-id-of-ws -H "Accept: application/json"` and
    `curl http://localhost:8000/workspace/-the-id-of-ws -H "Accept: application/vnd.ocrd+zip"
        --output test-ocrd-bag.zip`
    """
    if accept == "application/json":
        workspace = workspace_manager.get_workspace_rsrc(workspace_id)
        if not workspace:
            raise ResponseException(404, {})
        return workspace
    elif accept == "application/vnd.ocrd+zip":
        workspace = workspace_manager.get_workspace_bag(workspace_id)
        if not workspace:
            raise ResponseException(404, {})
        return FileResponse(workspace)
    else:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Unsupported media, expected application/json or application/vnd.ocrd+zip",
        )


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


@app.get("/workflow")
async def list_workflow_scripts() -> List[WorkflowRsrc]:
    """
    Get a list of existing workflow spaces. Each workflow space has a Nextflow script inside.

    curl http://localhost:8000/workflow/
    """
    return workflow_manager.get_workflows()


@app.post("/workflow", responses={"201": {"model": WorkflowRsrc}})
async def upload_workflow_script(nextflow_script: UploadFile) -> Union[None, WorkflowRsrc]:
    """
    Create a new workflow space. Upload a Nextflow script inside.

    curl -X POST http://localhost:8000/workflow -H 'content-type: multipart/form-data' -F file=@things/nextflow.nf  # noqa
    """
    try:
        return await workflow_manager.create_workflow_space(nextflow_script)
    except Exception:
        # TODO: exception mapping to repsonse code:
        #   - return 422 if workflow invalid etc.
        #   - return 500 for unexpected errors
        log.exception("error in post_workflow")
        return None


@app.get("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
async def get_workflow_script(workflow_id: str) -> WorkflowRsrc:
    """
    Get the Nextflow script of an existing workflow space. Specify your download path with --output

    curl -X 'GET' 'http://localhost:8000/workflow/{workflow_id}' -H 'accept: application/json' --output ./nextflow.nf
    """

    workflow_script = workflow_manager.get_workflow_script_rsrc(workflow_id)

    if not workflow_script:
        raise ResponseException(404, {})
    return FileResponse(path=workflow_script.id,
                        media_type="application/json",
                        filename=workflow_script.id)


@app.put("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
async def update_workflow_script(nextflow_script: UploadFile, workflow_id: str) -> Union[None, WorkflowRsrc]:
    """
    Update or create a new workflow space. Upload a Nextflow script inside.
    """
    try:
        return await workflow_manager.update_workflow_space(nextflow_script, workflow_id)
    except Exception:
        # TODO: exception mapping to repsonse code:
        #   - return 422 if workflow invalid etc.
        #   - return 500 for unexpected errors
        log.exception("error in put_workflow")
        return None

"""
Not in the Web API Specification. Will be implemented if needed.

@app.delete("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
async def delete_workflow_space(workflow_id: str) -> WorkflowRsrc:
    pass
"""

"""
Executes the Nextflow script identified with {workflow_id}.
The instance is identified by creating a {job_id}
Input: workspace_id and fileGrp
Output: overwrites the OCR-D results inside the {workspace_id}
"""
@app.post("/workflow/{workflow_id}", responses={"201": {"model": WorkflowRsrc}})
async def start_workflow(workflow_id: str, workspace_id: str) -> Union[None, WorkflowRsrc]:
    """
    Trigger a Nextflow execution by using a Nextflow script with id {workflow_id} on a
    workspace with id {workspace_id}
    """
    try:
        return workflow_manager.start_nf_workflow(workflow_id, workspace_id)
    except Exception:
        # TODO: exception mapping to repsonse code:
        #   - return 422 if workflow invalid etc.
        #   - return 500 for unexpected errors
        log.exception("error in start_workflow")
        return None

"""
TODO: Implement @app.get("/workflow/{workflow_id}/{job_id}") -> Still unclear how to implement it

Provides the execution status of the Nextflow run identified with {job_id}.
Input: job_id
Output: Execution status, zip with Nextflow run related files (logs, errs, reports, etc.)
"""
