"""
module for implementing the discovery section of the api
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
from ocrd_webapi_test.models import (
    DiscoveryResponse,
    WorkspaceRsrc,
    Processor,
    ProcessorJob,
    ProcessorArgs,
)
from ocrd_webapi_test.utils import (
    ResponseException,
    validate_workspace
)
from ocrd_webapi_test.constants import (
    SERVER_PATH,
    WORKSPACES_DIR,
    JOB_DIR,
    WORKSPACE_ZIPNAME,
)


class Discovery:
    def discovery(self) -> DiscoveryResponse:
        """
        Discovery of capabilities of the server
        """
        # TODO: what is the meaning of `has_ocrd_all` and `has_docker`? If docker is used,
        #       (I plan to use docker `ocrd/all:medium` container) does this mean has_docker and
        #       has_ocrd_all  must both be true?
        res = DiscoveryResponse()
        res.ram = psutil.virtual_memory().total / (1024.0 ** 3)
        res.cpu_cores = os.cpu_count()
        res.has_cuda = False
        res.has_ocrd_all = True
        res.has_docker = True
        return res
