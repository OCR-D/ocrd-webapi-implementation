"""
Test-implementation of ocrd webApi: https://github.com/OCR-D/spec/blob/master/openapi.yml
"""
import datetime
import os
import secrets
from typing import Union, List
from .routers import (
    processor,
    workflow,
    workspace,
)

from fastapi import (
    FastAPI,
    UploadFile,
    Request,
    Header,
    HTTPException,
    status,
    BackgroundTasks,
    Depends
)
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
from fastapi.security import HTTPBasic, HTTPBasicCredentials


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
app.include_router(processor.router)
app.include_router(workflow.router)
app.include_router(workspace.router)

safe_init_logging()
log = getLogger('ocrd_webapi.main')
log.info(f"DB_URL: {DB_URL}")

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
