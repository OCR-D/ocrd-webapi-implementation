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
    WorkspaceRsrc,
    Processor,
    ProcessorJob,
    ProcessorArgs,
)
from ocrd_webapi_test.utils import (
    ResponseException,
)
from ocrd_webapi_test.constants import (
    SERVER_PATH,
    WORKSPACES_DIR,
    JOB_DIR,
    WORKSPACE_ZIPNAME,
)
from ocrd_utils import (
    unzip_file_to_dir
)
from ocrd_validators.ocrd_zip_validator import (
    OcrdZipValidator
)

from ocrd import Resolver


# noinspection PyMethodMayBeStatic TODO: remove
class WorkspaceManager:
    def get_workspace(self):
        res: List = [
            WorkspaceRsrc(id=to_workspace_url(f), description="Workspace")
            for f in os.listdir(WORKSPACES_DIR)
            if os.path.isdir(to_workspace_dir(f))
        ]
        return res

    async def create_workspace_from_zip(self, file):
        uid = str(uuid.uuid4())
        workspace_dir = to_workspace_dir(uid)
        os.mkdir(workspace_dir)
        zip_dest = os.path.join(workspace_dir, WORKSPACE_ZIPNAME)

        async with aiofiles.open(zip_dest, "wb") as fpt:
            content = await file.read(1024)
            while content:
                await fpt.write(content)
                content = await file.read(1024)

        unzip_file_to_dir(zip_dest, workspace_dir)
        os.remove(zip_dest)

        resolver = Resolver()
        validator = OcrdZipValidator(resolver, workspace_dir)
        validator.validate(skip_unzip=True, skip_delete=True)

        return WorkspaceRsrc(id=to_workspace_url(uid), description="Workspace")

    def get_workspace_rsrc(self, workspace_id):
        """
        # TODO:
        1. create workspace pfad
        2. test if existing
        3. if existing return workspaceRsrc
        4. if not return None
        """
        return WorkspaceRsrc(id=to_workspace_url(workspace_id), description="Workspace")


def to_workspace_url(workspace_id: str) -> str:
    """
    create url where workspace is available
    """
    return f"{SERVER_PATH}/workspace/{workspace_id}"


def to_workspace_dir(workspace_id: str) -> str:
    """
    return path to workspace with id `workspace_id`. No check if existing
    """
    return os.path.join(WORKSPACES_DIR, workspace_id)
