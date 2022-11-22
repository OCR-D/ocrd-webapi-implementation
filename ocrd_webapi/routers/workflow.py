import os
import secrets

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
    UploadFile,
)
from fastapi.responses import FileResponse
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
)

from ocrd_utils import getLogger

from ocrd_webapi import database
from ocrd_webapi.models.base import WorkflowArgs
from ocrd_webapi.models.workflow import WorkflowRsrc, WorkflowJobRsrc
from ocrd_webapi.models.workspace import WorkspaceRsrc

from ocrd_webapi.utils import (
    ResponseException,
    safe_init_logging,
)
from ocrd_webapi.workflow_manager import (
    WorkflowManager
)

router = APIRouter(
    tags=["Workflow"],
)

safe_init_logging()
log = getLogger('ocrd_webapi.workflow')
workflow_manager = WorkflowManager()
security = HTTPBasic()


def __dummy_security_check(auth):
    """
    Reference security check implementation
    """
    user = auth.username.encode("utf8")
    pw = auth.password.encode("utf8")
    expected_user = os.getenv("OCRD_WEBAPI_USERNAME", "test").encode("utf8")
    expected_pw = os.getenv("OCRD_WEBAPI_PASSWORD", "test").encode("utf8")
    if not user or not pw or not secrets.compare_digest(pw, expected_pw) or \
            not secrets.compare_digest(user, expected_user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            headers={"WWW-Authenticate": "Basic"})


# TODO: Refine all the exceptions...
@router.get("/workflow")
async def list_workflows():
    """
    Get a list of existing workflow space urls. Each workflow space has a Nextflow script inside.

    curl http://localhost:8000/workflow/
    """
    workflow_space_urls = workflow_manager.get_workflows()
    response = []
    for wf in workflow_space_urls:
        response.append(WorkflowRsrc(id=wf, description="Workflow"))
    return response


@router.get("/workflow/{workflow_id}")
async def get_workflow_script(workflow_id: str, accept: str = Header(...)):
    """
    Get the Nextflow script of an existing workflow space. Specify your download path with --output

    When tested with FastAPI's interactive API docs / Swagger (e.g. http://127.0.0.1:8000/docs) the
    accept-header is always set to application/json (no matter what is specified in the gui) so it
    can not be used to test getting the workflow as a file. See:
    https://github.com/OCR-D/ocrd-webapi-implementation/issues/2

    curl -X GET http://localhost:8000/workflow/{workflow_id} -H "accept: text/vnd.ocrd.workflow" --output ./nextflow.nf
    curl -X GET http://localhost:8000/workflow/{workflow_id} -H "accept: application/json" --output ./nextflow.nf
    """
    if accept in ["text/vnd.ocrd.workflow", "application/json"]:
        workflow_script_path = workflow_manager.get_workflow_script(workflow_id)
        workflow_script_url = workflow_manager._to_resource_url(workflow_id)
        if not workflow_script_path:
            raise ResponseException(404, {})
        if accept == "text/vnd.ocrd.workflow":
            return FileResponse(path=workflow_script_path, filename="workflow_script.nf")
        else:
            return WorkflowRsrc(id=workflow_script_url, description="Workflow nextflow script")
    else:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Unsupported media, expected application/json or text/vnd.ocrd.workflow",
        )


@router.get("/workflow/{workflow_id}/{job_id}", responses={"201": {"model": WorkflowJobRsrc}})
async def get_workflow_job(workflow_id: str, job_id: str):
    """
    Query a job from the database. Used to query if a job is finished or still running

    workflow_id is not needed in this implementation, but it is used in the specification. In this
    implementation each job-id is unique so workflow_id is not necessary. But it could be necessary
    in other implementations for example if a job_id is only unique in conjunction with a
    workflow_id.
    """
    if workflow_manager.is_job_finished(workflow_id, job_id):
        await database.set_workflow_job_state(job_id, 'STOPPED')
    job = await database.get_workflow_job(job_id)

    if not job:
        raise ResponseException(404, {})
    return job.to_rsrc()


@router.post("/workflow", responses={"201": {"model": WorkflowRsrc}})
async def upload_workflow_script(nextflow_script: UploadFile,
                                 auth: HTTPBasicCredentials = Depends(security)):
    """
    Create a new workflow space. Upload a Nextflow script inside.

    curl -X POST http://localhost:8000/workflow -F nextflow_script=@things/nextflow.nf  # noqa
    """

    __dummy_security_check(auth)
    try:
        workflow_url = await workflow_manager.create_workflow_space(nextflow_script)
    except Exception:
        log.exception("error in upload_workflow_script")
        raise ResponseException(500, {"error": "internal server error"})

    return WorkflowRsrc(id=workflow_url, description="Workflow")


@router.post("/workflow/{workflow_id}", responses={"201": {"model": WorkflowJobRsrc}})
async def run_workflow(workflow_id: str, workflow_args: WorkflowArgs):
    """
    Trigger a Nextflow execution by using a Nextflow script with id {workflow_id} on a
    workspace with id {workspace_id}. The OCR-D results are stored inside the {workspace_id}.

    curl -X POST http://localhost:8000/workflow/{workflow_id}?workspace_id={workspace_id}
    """
    try:
        parameters = await workflow_manager.start_nf_workflow(workflow_id, workflow_args.workspace_id)
    except Exception as e:
        log.exception("error in start_workflow")
        raise ResponseException(500, {"error": "internal server error", "message": str(e)})

    # Parse parameters for better readability of the code
    job_url = parameters[0]
    job_status = parameters[1]
    workflow_url = parameters[2]
    workspace_url = parameters[3]
    workflow_rsrc = WorkflowRsrc(id=workflow_url, description="Workflow")
    workspace_rsrc = WorkspaceRsrc(id=workspace_url, description="Workspace")

    return WorkflowJobRsrc(id=job_url, state=job_status, workflow=workflow_rsrc,
                           workspace=workspace_rsrc, description="Workflow-Job")


@router.put("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
async def update_workflow_script(nextflow_script: UploadFile, workflow_id: str,
                                 auth: HTTPBasicCredentials = Depends(security)):
    """
    Update or create a new workflow space. Upload a Nextflow script inside.

    curl -X PUT http://localhost:8000/workflow/{workflow_id} -F nextflow_script=@things/nextflow-simple.nf
    """

    __dummy_security_check(auth)
    try:
        updated_workflow_url = await workflow_manager.update_workflow_space(nextflow_script, workflow_id)
    except Exception:
        log.exception("error in update_workflow_script")
        raise ResponseException(500, {"error": "internal server error"})

    return WorkflowRsrc(id=updated_workflow_url, description="Workflow")

    # Not in the Web API Specification. Will be implemented if needed.
    # TODO: Implement that since we have some sort of dummy security check
    """
    @router.delete("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
    async def delete_workflow_space(workflow_id: str) -> WorkflowRsrc:
        pass
    """
