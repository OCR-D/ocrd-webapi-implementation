"""
Test-implementation of ocrd webApi: https://github.com/OCR-D/spec/blob/master/openapi.yml
"""
import datetime
import os
import subprocess
import uuid
from typing import List, Union

from fastapi import FastAPI, UploadFile, File, Path, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseSettings
import aiofiles
import psutil
from .models import (
    DiscoveryResponse,
    Workspace,
    Processor,
    ProcessorJob,
    ProcessorArgs,
)
from .utils import (
    to_workspace_path,
    Empty404Exception,
)
from .constants import SERVER_PATH


class Settings(BaseSettings):
    """
    fast-API way to create constants: https://fastapi.tiangolo.com/advanced/settings/
    """
    base_dir: str = f"{os.getenv('HOME')}/zeugs-ohne-backup/ocrd_webapi"
    workspaces_dir: str = f"{base_dir}/workspaces"
    job_dir: str = f"{base_dir}/jobs"
    workspace_zipname: str = "workspace.zip"


settings = Settings()
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


@app.exception_handler(Empty404Exception)
async def empty404_exception_handler(request: Request, exc: Empty404Exception):
    return JSONResponse(status_code=404, content={})


@app.on_event("startup")
async def startup_event():
    """
    Executed once on startup
    """
    os.makedirs(settings.workspaces_dir, exist_ok=True)
    os.makedirs(settings.job_dir, exist_ok=True)


@app.get("/")
async def test():
    """
    to test if server is running on root-path
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


@app.get("/discovery", response_model=DiscoveryResponse)
async def discovery() -> DiscoveryResponse:
    """
    Discovery of capabilities of the server
    """
    # TODO: what is the meaning of `has_ocrd_all` and `has_docker`? If docker is used,
    #       (I plan to use docker `ocrd/all` container) does this mean has_docker and has_ocrd_all
    #       must both be true?
    res = DiscoveryResponse()
    res.ram = psutil.virtual_memory().total / (1024.0 ** 3)
    res.cpu_cores = os.cpu_count()
    res.has_cuda = False
    res.has_ocrd_all = True
    res.has_docker = True
    return res


@app.get("/workspace", response_model=List[Workspace])
def get_workspaces() -> List[Workspace]:
    """
    Return a list of all existing workspaces
    """
    wsd: str = settings.workspaces_dir
    res: List = [
        Workspace(id=to_workspace_path(f), description="Workspace")
        for f in os.listdir(wsd)
        if os.path.isdir(os.path.join(wsd, f))
    ]
    return res


@app.get('/workspace/{workspace_id}', response_model=Workspace)
def get_workspace(workspace_id: str) -> Workspace:
    """
    Test if workspace exists
    """
    if not os.path.exists(os.path.join(settings.workspaces_dir, workspace_id)):
        raise Empty404Exception()
    return Workspace(id=to_workspace_path(workspace_id), description="Workspace")


@app.post("/workspace", response_model=None, responses={"201": {"model": Workspace}})
async def post_workspace(file: UploadFile = File(...)) -> None | Workspace:
    """
    Create a new workspace
    """
    uid = str(uuid.uuid4())
    workspace_dir = os.path.join(settings.workspaces_dir, uid)
    os.mkdir(workspace_dir)
    dest = os.path.join(workspace_dir, settings.workspace_zipname)

    async with aiofiles.open(dest, "wb") as fpt:
        while content := await file.read(1024):
            await fpt.write(content)

    # TODO: async?!
    subprocess.run(["unzip", dest, "-d", workspace_dir], stdout=subprocess.DEVNULL, check=True)
    # TODO: validate workspace with ocrd-all
    os.remove(dest)
    return Workspace(id=to_workspace_path(uid), description="Workspace")


# TODO: had to disable RespnoseModel. Try to fix and activate again?!
# @app.post('/processor/{executable}', response_model=ProcessorJob)
@app.post('/processor/{executable}')
async def run_processor(executable: str, body: ProcessorArgs = ...) -> ProcessorJob:
    """
    Run an OCR-D-Processor on a workspace

    Args:
        executable (str): Name of ocr-d processor. For example `ocrd-tesserocr-segment-region`
        body (ProcessorArgs): json-object with necessary args to call processor
    Returns:
        ProcessorJob: Properties for running job like workspace, ocrd-tool.json.
    """
    # TODO: try to execute command on running container. Is this even possible?
    # TODO: verify that executeable is valid before invoking docker
    user_id = subprocess.run(["id", "-u"], capture_output=True, check=True).stdout.decode().strip()
    # TODO: verify provided workspace exists
    workspace_dir = os.path.join(settings.workspaces_dir, body.workspace.id)

    # TODO: add -O and -I only if necessary, depending on if present in body
    pcall = ["docker", "run", "--user", user_id, "--rm", "--workdir", "/data", "--volume",
             f"{workspace_dir}/data:/data", "--", "ocrd/all:medium", executable, "-I",
             body.input_file_grps, "-O", body.output_file_grps]
    proc = subprocess.run(pcall, capture_output=True, check=False)
    if proc.returncode > 0:
        print(f"error executing docker-command: {proc.stderr.decode().strip()}")
        # TODO: if request fails caller must be informed? Or start process in background and users
        #       have to inform themselfs via ProcessorJob-Interface?
    # TODO: get ocrd-tools.json somehow and insert as __root__ somehow
    proc = Processor(__root__='{"TODO": "deliver ocrd-tool.json"}')
    workspace = Workspace(id=body.workspace.id, description="Workspace")
    res = ProcessorJob(proc, workspace)
    # TODO: ProcessorJob must be saved somewhere. Create dir on disc with jobs
    return res
