"""
Test-implementation of ocrd webApi: https://github.com/OCR-D/spec/blob/master/openapi.yml
"""
import datetime
import os
from ocrd_utils import initLogging, getLogger
import subprocess
import uuid
import asyncio
import functools
from typing import List, Union

from fastapi import FastAPI, UploadFile, File, Path, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseSettings
from ocrd_webapi_test.models import (
    DiscoveryResponse,
    Workspace,
    Processor,
    ProcessorJob,
    ProcessorArgs,
)
from ocrd_webapi_test.utils import (
    to_workspace_url,
    to_workspace_dir,
    ResponseException,
    validate_workspace
)
from ocrd_webapi_test.constants import (
    SERVER_PATH,
    WORKSPACES_DIR,
    JOB_DIR,
    WORKSPACE_ZIPNAME,
)
from ocrd_webapi_test.workflow import Workflow
from ocrd_webapi_test.workspace import WorkspaceManager
from ocrd_webapi_test.discovery import Discovery


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
log = getLogger('ocrd_webapi_test.main')
workspace_manager = WorkspaceManager()

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


@app.post("/workspace", response_model=None, responses={"201": {"model": Workspace}})
async def post_workspace(file: UploadFile) -> Union[None, Workspace]:
    """
    Create a new workspace
    """
    try:
        workspace_manager.create_workspace_from_zip(file)
    except Exception as e:
        log.exception("error in post_workspace")
        return None
