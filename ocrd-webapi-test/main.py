import datetime
import os
import subprocess
import uuid
from typing import List

import aiofiles
import psutil
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseSettings

from .models import (
    DiscoveryResponse,
    Workspace,
    Processor,
    ProcessorJob,
    ProcessorArgs,
)


class Settings(BaseSettings):
    workspaces_dir: str = f"{os.getenv('HOME')}/zeugs-ohne-backup/ocrd_webapi/workspaces"
    workspace_zipname: str = "workspace.zip"


settings = Settings()
app = FastAPI(
    title="OCR-D Web API",
    description="HTTP API for offering OCR-D processing",
    contact={"email": "test@example.com"},  # TODO: update if needed
    license={
        "name": "Apache 2.0",
        "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
    },
    version="0.0.1",
    servers=[
        {
            "url": "http://localhost:8000",  # TODO: update if needed
            "description": "The URL of your server offering the OCR-D API.",
        }
    ],
)


@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.workspaces_dir, exist_ok=True)


@app.get("/")
async def test():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


@app.get("/discovery", response_model=DiscoveryResponse)
async def discovery() -> DiscoveryResponse:
    # TODO: ask someone: what is the meaning of `has_ocrd_all` and `has_docker`? If docker is used,
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

    TODO: right now id is just the id. I don't understand this `@` correctly but maybe it must be
          an URL where this workspace is available
    """
    wd: str = settings.workspaces_dir
    res: List = [
        Workspace(id=f, description="Workspace")
        for f in os.listdir(wd)
        if os.path.isdir(os.path.join(wd, f))
    ]
    return res


@app.post("/workspace", response_model=None, responses={"201": {"model": Workspace}})
async def post_workspace(file: UploadFile = File(...)) -> None | Workspace:
    """
    Create a new workspace

    TODO: @id might be wrongly set, because URL could be expected
    """
    uid = str(uuid.uuid4())
    workspace_dir = os.path.join(settings.workspaces_dir, uid)
    os.mkdir(workspace_dir)
    dest = os.path.join(workspace_dir, settings.workspace_zipname)

    async with aiofiles.open(dest, "wb") as f:
        while content := await file.read(1024):
            await f.write(content)

    # TODO: async?!
    subprocess.run(["unzip", dest, "-d", workspace_dir], stdout=subprocess.DEVNULL)
    # TODO: validate workspace with ocrd-all
    os.remove(dest)

    return Workspace(id=uid, description="Workspace")


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
    user_id = subprocess.run(["id", "-u"], capture_output=True).stdout.decode().strip()
    # TODO: verify provided workspace exists
    workspace_dir = os.path.join(settings.workspaces_dir, body.workspace.id)

    # TODO: add -O and -I only if necessary, depending on if present in body
    pcall = ["docker", "run", "--user", user_id, "--workdir", "/data", "--volume", f"{workspace_dir}/data:/data",
             "--", "ocrd/all:medium", executable, "-I", body.input_file_grps, "-O", body.output_file_grps]
    p = subprocess.run(pcall, capture_output=True)
    if p.returncode > 0:
        print(f"error executing docker-command: {p.stderr.decode().strip()}")
        # TODO: if request fails caller must be informed? Or start process in background and users have to inform
        # themselfs
    # TODO: get ocrd-tools.json somehow and insert as __root__ somehow
    proc = Processor(__root__="doch")
    proc.__root__ = "nein"
    ws = Workspace(id=body.workspace.id, description="Workspace")
    res = ProcessorJob(proc, ws)
    # TODO: ProcessorJob must be saved somewhere. Database?
    return res
