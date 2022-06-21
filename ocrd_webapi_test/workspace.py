"""
module for functionality regarding the workspace section of the api
"""
import datetime
import os
import subprocess
import uuid
import asyncio
import functools
from typing import List

from fastapi import FastAPI, UploadFile, File, Path, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseSettings
import aiofiles
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

class WorkspaceManager:
    def get_workspace(self):
        res: List = [
            Workspace(id=to_workspace_url(f), description="Workspace")
            for f in os.listdir(WORKSPACES_DIR)
            if os.path.isdir(to_workspace_dir(f))
        ]
        return res

    def create_workspace_from_zip(self, file):
        uid = str(uuid.uuid4())
        workspace_dir = to_workspace_dir(uid)
        os.mkdir(workspace_dir)
        dest = os.path.join(workspace_dir, WORKSPACE_ZIPNAME)

        async with aiofiles.open(dest, "wb") as fpt:
            content = await file.read(1024)
            while content:
                await fpt.write(content)
                content = await file.read(1024)

        proc = await asyncio.create_subprocess_exec("unzip", dest, "-d", workspace_dir,
                                                    stdout=subprocess.DEVNULL)
        await proc.communicate()
        os.remove(dest)

        if not await validate_workspace(uid):
            raise ResponseException(400, {"description": "Invalid workspace"})

        return Workspace(id=to_workspace_url(uid), description="Workspace")
