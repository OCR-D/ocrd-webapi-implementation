from fastapi import FastAPI, UploadFile, File
from pydantic import BaseSettings
import datetime
import os
import psutil
from typing import List, Optional
import aiofiles
import uuid
import subprocess

from .models import (
    DiscoveryResponse,
    Workspace,
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
    res.ram = psutil.virtual_memory().total / (1024.0**3)
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
