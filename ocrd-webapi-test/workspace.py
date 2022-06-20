"""
module for implementing the workspace section of the api
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
import psutil
from .models import (
    DiscoveryResponse,
    Workspace,
    Processor,
    ProcessorJob,
    ProcessorArgs,
)
from .utils import (
    to_workspace_url,
    to_workspace_dir,
    ResponseException,
    validate_workspace
)
from .constants import (
    SERVER_PATH,
    WORKSPACES_DIR,
    JOB_DIR,
    WORKSPACE_ZIPNAME,
)

class Workspace:
    def get_workspace(self):
        res: List = [
            Workspace(id=to_workspace_url(f), description="Workspace")
            for f in os.listdir(WORKSPACES_DIR)
            if os.path.isdir(to_workspace_dir(f))
        ]
        return res
