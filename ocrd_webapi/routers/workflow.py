import os
import secrets

from fastapi import (
    APIRouter,
    BackgroundTasks,
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

# OCR-D core related imports
from ocrd_utils import getLogger

# OCR-D WebAPI related imports
from ocrd_webapi.constants import (
    WORKFLOWS_DIR,
)
from ocrd_webapi.database import (
    initiate_database,
    get_workflow_job,
    set_workflow_job_finished,
)
from ocrd_webapi.models import (
    WorkflowRsrc,
    WorkflowArgs,
    WorkflowJobRsrc,
)
from ocrd_webapi.utils import (
    ResponseException,
    safe_init_logging,
    to_workspace_dir,
)
from ocrd_webapi.workflow_manager import WorkflowManager

from typing import (
    List,
    Union,
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
    currently it would be possible to upload any nextflow script and execute anything on the server
    this way. The purpose of this security is just for temporarily disable that possibility kind of
    TODO: delete this 
    (Mehmed: Don't delete, yet. It's a good idea to have dummy functionalities as an example (till we get real ones).)
    """
    user = auth.username.encode("utf8")
    pw = auth.password.encode("utf8")
    expected_user = os.getenv("OCRD_WEBAPI_USERNAME", "").encode("utf8")
    expected_pw = os.getenv("OCRD_WEBAPI_PASSWORD", "").encode("utf8")
    if not user or not pw or not secrets.compare_digest(pw, expected_pw) or \
            not secrets.compare_digest(user, expected_user):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            headers={"WWW-Authenticate": "Basic"})

@router.get("/workflow")
async def list_workflow_scripts() -> List[WorkflowRsrc]:
    """
    Get a list of existing workflow spaces. Each workflow space has a Nextflow script inside.

    curl http://localhost:8000/workflow/
    """
    return workflow_manager.get_workflows()

@router.get("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
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

@router.get("/workflow/{workflow_id}/{job_id}", responses={"201": {"model": WorkflowJobRsrc}})
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

@router.post("/workflow", responses={"201": {"model": WorkflowRsrc}})
async def upload_workflow_script(nextflow_script: UploadFile, auth: HTTPBasicCredentials = Depends(
                                 security)) -> Union[None, WorkflowRsrc]:
    """
    Create a new workflow space. Upload a Nextflow script inside.

    curl -X POST http://localhost:8000/workflow -F nextflow_script=@things/nextflow.nf  # noqa
    """
    __dummy_security_check(auth)
    try:
        return await workflow_manager.create_workflow_space(nextflow_script)
    except Exception:
        log.exception("error in upload_workflow_script")
        raise ResponseException(500, {"error": "internal server error"})

@router.post("/workflow/{workflow_id}", responses={"201": {"model": WorkflowJobRsrc}})
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

@router.put("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
async def update_workflow_script(
    nextflow_script: UploadFile, workflow_id: str,
    auth: HTTPBasicCredentials = Depends(security)) -> Union[None, WorkflowRsrc]:
    """
    Update or create a new workflow space. Upload a Nextflow script inside.

    curl -X PUT http://localhost:8000/workflow/{workflow_id} -F nextflow_script=@things/nextflow-simple.nf
    """
    __dummy_security_check(auth)
    try:
        return await workflow_manager.update_workflow_space(nextflow_script, workflow_id)
    except Exception:
        log.exception("error in update_workflow_script")
        raise ResponseException(500, {"error": "internal server error"})

# Not in the Web API Specification. Will be implemented if needed.
# TODO: Implement that since we have some sort of dummy security check
    """
    @router.delete("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
    async def delete_workflow_space(workflow_id: str) -> WorkflowRsrc:
        pass
    """
