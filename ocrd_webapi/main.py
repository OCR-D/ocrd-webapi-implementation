"""
Test-implementation of ocrd webApi: https://github.com/OCR-D/spec/blob/master/openapi.yml
"""
import datetime
import os
from typing import Union, List

from fastapi import FastAPI, UploadFile, Request, Header, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from ocrd_utils import getLogger

from ocrd_webapi.constants import (
    SERVER_PATH,
    WORKSPACES_DIR,
    WORKFLOWS_DIR,
    DB_URL,
)
from ocrd_webapi.database import (
    initiate_database,
    get_workflow_job,
    set_workflow_job_finished,
)
from ocrd_webapi.models import (
    WorkspaceRsrc,
    WorkflowRsrc,
    WorkflowArgs,
    WorkflowJobRsrc,
)
from ocrd_webapi.utils import (
    ResponseException,
    WorkspaceNotValidException,
    safe_init_logging,
)
from ocrd_webapi.workflow_manager import WorkflowManager
from ocrd_webapi.workspace_manager import WorkspaceManager
from ocrd_webapi import database
from ocrd_webapi.utils import (
    WorkspaceException,
    to_workspace_dir
)

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
safe_init_logging()
log = getLogger('ocrd_webapi.main')
workspace_manager = WorkspaceManager()
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


@app.post("/workspace", responses={"201": {"model": WorkspaceRsrc}})
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


@app.get("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
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
        background_tasks.add_task(os.unlink, bag_path)
        return FileResponse(bag_path)
    else:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Unsupported media, expected application/json or application/vnd.ocrd+zip",
        )


@app.delete("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
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


@app.put("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
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

    curl -X POST http://localhost:8000/workflow -F nextflow_script=@things/nextflow.nf  # noqa
    """
    try:
        return await workflow_manager.create_workflow_space(nextflow_script)
    except Exception:
        log.exception("error in upload_workflow_script")
        raise ResponseException(500, {"error": "internal server error"})


@app.get("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
async def get_workflow_script(workflow_id: str, accept: str = Header(...)) -> Union[WorkflowRsrc, FileResponse]:
    """
    Get the Nextflow script of an existing workflow space. Specify your download path with --output

    curl -X GET http://localhost:8000/workflow/{workflow_id} -H "Accept: text/vnd.ocrd.workflow" --output ./nextflow.nf
    """
    if accept in ["application/json", "text/vnd.ocrd.workflow"]:
        workflow_script = workflow_manager.get_workflow_script_rsrc(workflow_id)
        if not workflow_script:
            raise ResponseException(404, {})
        if accept == "application/json":
            return workflow_script
        else:
            return FileResponse(path=workflow_script.id, filename=workflow_script.id)
    else:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Unsupported media, expected application/json or text/vnd.ocrd.workflow",
        )


@app.put("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
async def update_workflow_script(nextflow_script: UploadFile, workflow_id: str) -> Union[None, WorkflowRsrc]:
    """
    Update or create a new workflow space. Upload a Nextflow script inside.

    curl -X PUT http://localhost:8000/workflow/{workflow_id} -F nextflow_script=@things/nextflow-simple.nf
    """
    try:
        return await workflow_manager.update_workflow_space(nextflow_script, workflow_id)
    except Exception:
        log.exception("error in update_workflow_script")
        raise ResponseException(500, {"error": "internal server error"})


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
@app.post("/workflow/{workflow_id}", responses={"201": {"model": WorkflowJobRsrc}})
async def start_workflow(workflow_id: str, workflow_args: WorkflowArgs) -> Union[None, WorkflowJobRsrc]:
    """
    Trigger a Nextflow execution by using a Nextflow script with id {workflow_id} on a
    workspace with id {workspace_id}. The OCR-D results are stored inside the {workspace_id}.

    curl -X POST http://localhost:8000/workflow/{workflow_id}?workspace_id={workspace_id}
    """
    if not os.path.exists(workflow_manager.to_workflow_dir(workflow_id)):
        raise ResponseException(500, {"error": f"Workflow not existing. Id: {workflow_id}"})
    if not os.path.exists(to_workspace_dir(workflow_args.workspace_id)):
        raise ResponseException(500, {"error": "Workspace not existing. Id:"
                                               f" {workflow_args.workspace_id}"})

    try:
        return await workflow_manager.start_nf_workflow(workflow_id, workflow_args)
    except Exception as e:
        log.exception("error in start_workflow")
        raise ResponseException(500, {"error": "internal server error", "message": str(e)})


@app.get("/workflow/{workflow_id}/{job_id}", responses={"201": {"model": WorkflowJobRsrc}})
async def get_workflowjob(workflow_id: str, job_id: str) -> WorkflowJobRsrc:
    """
    Query a job from the database. Used to query if a job is finished or still running

    workflow_id is not needed in this implementation, but it is used in the specification. In this
    implementation each job-id is unique so workflow_id is not necessary. But it could be necessary
    in other implementations for example if a job_id is only unique in conjunction with a
    workflow_id.
    """
    if workflow_manager.is_job_finished(workflow_id, job_id):
        await set_workflow_job_finished(job_id)
    job = await get_workflow_job(job_id)

    if not job:
        raise ResponseException(404, {})
    return job.to_rsrc()
