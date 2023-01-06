from os import getenv
from secrets import compare_digest
from typing import List, Union

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
from ocrd_webapi.exceptions import (
    ResponseException,
)
from ocrd_webapi.managers.workflow_manager import WorkflowManager
from ocrd_webapi.managers.workspace_manager import WorkspaceManager
from ocrd_webapi.models.base import WorkflowArgs
from ocrd_webapi.models.workflow import WorkflowRsrc, WorkflowJobRsrc
from ocrd_webapi.utils import (
    safe_init_logging,
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
    expected_user = getenv("OCRD_WEBAPI_USERNAME", "test").encode("utf8")
    expected_pw = getenv("OCRD_WEBAPI_PASSWORD", "test").encode("utf8")

    user_matched = compare_digest(user, expected_user)
    pw_matched = compare_digest(pw, expected_pw)

    if not user or not pw or not user_matched or not pw_matched:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"}
        )


# TODO: Refine all the exceptions...
@router.get("/workflow")
async def list_workflows() -> List[WorkflowRsrc]:
    """
    Get a list of existing workflow space urls.
    Each workflow space has a Nextflow script inside.

    curl http://localhost:8000/workflow/
    """
    workflow_space_urls = workflow_manager.get_workflows()
    response = []
    for wf_url in workflow_space_urls:
        response.append(WorkflowRsrc.create(workflow_url=wf_url))
    return response


@router.get("/workflow/{workflow_id}")
async def get_workflow_script(
        workflow_id: str,
        accept: str = Header(...)
) -> Union[WorkflowRsrc, FileResponse, ResponseException]:
    """
    Get the Nextflow script of an existing workflow space.
    Specify your download path with --output

    When tested with FastAPI's interactive API docs / Swagger (e.g. http://127.0.0.1:8000/docs) the
    accept-header is always set to application/json (no matter what is specified in the gui) so it
    can not be used to test getting the workflow as a file. See:
    https://github.com/OCR-D/ocrd-webapi-implementation/issues/2

    curl -X GET http://localhost:8000/workflow/{workflow_id} -H "accept: text/vnd.ocrd.workflow" --output ./nextflow.nf
    curl -X GET http://localhost:8000/workflow/{workflow_id} -H "accept: application/json" --output ./nextflow.nf
    """
    if accept == "application/json":
        workflow_script_url = workflow_manager.get_resource(
            workflow_id,
            local=False
        )
        if workflow_script_url:
            return WorkflowRsrc.create(workflow_url=workflow_script_url)
        raise ResponseException(404, {})
    if accept == "text/vnd.ocrd.workflow":
        workflow_script_path = workflow_manager.get_resource_file(
            workflow_id,
            file_ext=".nf"
        )
        if workflow_script_path:
            return FileResponse(
                path=workflow_script_path,
                filename="workflow_script.nf"
            )
        raise ResponseException(404, {})
    raise HTTPException(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        "Unsupported media, expected application/json \
        or text/vnd.ocrd.workflow",
    )


@router.get("/workflow/{workflow_id}/{job_id}",
            responses={"200": {"model": WorkflowJobRsrc}})
async def get_workflow_job(
        workflow_id: str,
        job_id: str
) -> Union[WorkflowJobRsrc, ResponseException]:
    """
    Query a job from the database. Used to query if a job is finished or still running

    workflow_id is not needed in this implementation, but it is used in the specification. In this
    implementation each job-id is unique so workflow_id is not necessary. But it could be necessary
    in other implementations for example if a job_id is only unique in conjunction with a
    workflow_id.
    """
    wf_job_db = await workflow_manager.get_workflow_job(
        workflow_id,
        job_id
    )
    if not wf_job_db:
        raise ResponseException(404, {})

    # TODO: this should not use a protected function, if a separate wrapper
    #  function is provided, this would duplicate some code...
    wf_job_url = workflow_manager.get_resource_job(
        wf_job_db.workflow_id,
        wf_job_db.id,
        local=False
    )
    workflow_url = workflow_manager.get_resource(
        wf_job_db.workflow_id,
        local=False
    )
    workspace_url = WorkspaceManager.static_get_resource(
        wf_job_db.workspace_id,
        local=False
    )
    job_state = wf_job_db.job_state

    return WorkflowJobRsrc.create(job_url=wf_job_url,
                                  workflow_url=workflow_url,
                                  workspace_url=workspace_url,
                                  job_state=job_state)


@router.post("/workflow",
             responses={"201": {"model": WorkflowRsrc}})
async def upload_workflow_script(
        nextflow_script: UploadFile,
        auth: HTTPBasicCredentials = Depends(security)
) -> Union[WorkflowRsrc, ResponseException]:
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

    return WorkflowRsrc.create(workflow_url=workflow_url)


@router.post("/workflow/{workflow_id}",
             responses={"201": {"model": WorkflowJobRsrc}})
async def run_workflow(
        workflow_id: str,
        workflow_args: WorkflowArgs
) -> Union[WorkflowJobRsrc, ResponseException]:
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

    return WorkflowJobRsrc.create(job_url=job_url,
                                  job_state=job_status,
                                  workflow_url=workflow_url,
                                  workspace_url=workspace_url)


@router.put("/workflow/{workflow_id}",
            responses={"201": {"model": WorkflowRsrc}})
async def update_workflow_script(
        nextflow_script: UploadFile,
        workflow_id: str,
        auth: HTTPBasicCredentials = Depends(security)
) -> Union[WorkflowRsrc, ResponseException]:
    """
    Update or create a new workflow space. Upload a Nextflow script inside.

    curl -X PUT http://localhost:8000/workflow/{workflow_id} -F nextflow_script=@things/nextflow-simple.nf
    """

    __dummy_security_check(auth)
    try:
        updated_workflow_url = await workflow_manager.update_workflow_space(
            file=nextflow_script,
            workflow_id=workflow_id
        )
    except Exception:
        log.exception("error in update_workflow_script")
        raise ResponseException(500, {"error": "internal server error"})

    return WorkflowRsrc.create(workflow_url=updated_workflow_url)

    # Not in the Web API Specification. Will be implemented if needed.
    # TODO: Implement that since we have some sort of dummy security check
    # @router.delete("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
    # async def delete_workflow_space(workflow_id: str) -> WorkflowRsrc:
    #   pass
