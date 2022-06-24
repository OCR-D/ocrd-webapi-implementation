"""
module for functionality regarding the workspace section of the api
"""
import datetime
import os
import subprocess
import uuid
import asyncio
import functools
import shutil
from typing import List, Union

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
from ocrd.workspace_bagger import WorkspaceBagger
from ocrd.workspace import Workspace

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
from ocrd_utils import getLogger

log = getLogger('ocrd_webapi_test.workspace_manager')
# noinspection PyMethodMayBeStatic TODO: remove
# TODO: add types to all method-declarations
class WorkspaceManager:
    def get_workspace(self):
        res: List = [
            WorkspaceRsrc(id=to_workspace_url(f), description="Workspace")
            for f in os.listdir(WORKSPACES_DIR)
            if os.path.isdir(to_workspace_dir(f))
        ]
        return res

    async def create_workspace_from_zip(self, file, uid=None):
        if uid:
            workspace_dir = to_workspace_dir(uid)
            if not os.path.exists(workspace_dir):
                log.warn("can not update: workspace still existing")
                return None
        else:
            uid = str(uuid.uuid4())
            workspace_dir = to_workspace_dir(uid)
        os.mkdir(workspace_dir)
        zip_dest = os.path.join(workspace_dir, WORKSPACE_ZIPNAME)

        async with aiofiles.open(zip_dest, "wb") as fpt:
            content = await file.read(1024)
            while content:
                await fpt.write(content)
                content = await file.read(1024)

        resolver = Resolver()
        valid = OcrdZipValidator(resolver, workspace_dir).validate().is_valid()
        if not valid:
            # TODO: raise custom Exception, catch in main and return appropriate error-code
            raise  Exception("zip is not valid")

        workspace_bagger = WorkspaceBagger(resolver)
        workspace_bagger.spill(zip_dest, workspace_dir)

        return WorkspaceRsrc(id=to_workspace_url(uid), description="Workspace")

    def get_workspace_rsrc(self, workspace_id):
        """
        Get workspace available on disk as Resource via it's id
        Returns:
            `WorkspaceRsrc` if `workspace_id` is available else `None`
        """
        possible_dir = to_workspace_dir(workspace_id)
        if not os.path.isdir(possible_dir):
            return None
        return WorkspaceRsrc(id=to_workspace_url(workspace_id), description="Workspace")

    def get_workspace_bag(self, workspace_id: str) -> Union[str, None]:
        """
        Create workspace bag.

        Workspace could have been changed so recreation of bag-files is necessary. Simply zipping
        is not sufficient

        Args:
             workspace_id (str): id of workspace to bag
        Returns:
            path to created bag
        """
        workspace_dir = to_workspace_dir(workspace_id)
        if not os.path.isdir(workspace_dir):
            return None
        # hier ocr-d verwenden: workspace_bagger.bag()
        # beispielaufruf ist in cli/zip.py zu finden
        # uuid holen
        # zippen und unter der uuid speichern
        # pfad zu uuid zurückgeben
        # wie kann ich das testen:
        #   TODO: write test for this method:
        #         - create workspace from bag
        #         - call dummy-processor on workspace
        #         - create bag
        #         - verify new outpu-file grp existing and files are in bag-info.txt (don't remember
        #           the bag-file-name wher checksums are stored, maybe has other name)

        # TODO: mets-location can be changed in bag. I think this fails in that case. Write a test
        #       for that and change accordingly if neccessary. a way to get mets_basename has to be
        #       found
        mets_basename = "mets.xml"
        dest = generate_bag_dest()
        mets = "mets.xml"
        # TODO: what happens to the identifier of unpacked bag. I think it is removed. So maybe
        #       it is neccesarry to store bag-info.txt before deleting bag somewehere to keep
        #       important information
        identifier = "TODO-identifier"
        resolver = Resolver()
        workspace = Workspace(resolver, directory=workspace_dir, mets_basename=mets)
        workspace_bagger = WorkspaceBagger(resolver)
        workspace_bagger.bag(
            workspace,
            dest=dest,
            ocrd_identifier=identifier,
            ocrd_mets=mets,
        )
        return dest

    def delete_workspace_bag(self, workspace_bag_path):
        """
        Delete a workspace bag after dispatch
        """
        pass

    def get_workspaces(self):
        """
        Get a list of all available workspaces
        """
        res = []
        for f in os.scandir(WORKSPACES_DIR):
            if f.is_dir():
                res.append(WorkspaceRsrc(id=to_workspace_url(f.name), description="Workspace"))
        res

    def delete_workspace(self, workspace_id):
        """
        Delete a workspace
        """
        workspace_dir = to_workspace_dir(workspace_id)
        if not os.path.isdir(workspace_dir):
            return None
        os.remove(workspace_dir)
        return WorkspaceRsrc(id=to_workspace_url(workspace_id), description="Workspace")

    async def put_workspace(self, workspace_id):
        """
        Update a workspace
        """
        workspace_dir = to_workspace_dir(workspace_id)
        if not os.path.isdir(workspace_dir):
            return None
        os.remove(workspace_dir)
        return await self.create_workspace_from_zip(workspace_id)


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

def generate_bag_dest() -> str:
    """
    return a unique path to store a bag of a workspace at
    """
    return os.path.join(WORKSPACES_DIR, str(uuid.uuid4()) + ".zip")
