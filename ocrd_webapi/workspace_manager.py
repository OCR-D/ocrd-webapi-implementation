"""
module for functionality regarding the workspace section of the api
"""
import os
import uuid
from typing import Union
import shutil

import aiofiles
from ocrd_webapi.models import WorkspaceRsrc
from ocrd.workspace_bagger import WorkspaceBagger
from ocrd.workspace import Workspace
from ocrd_validators.ocrd_zip_validator import OcrdZipValidator
from ocrd import Resolver
from ocrd_utils import getLogger
from pathlib import Path
from ocrd_webapi.utils import (
    WorkspaceNotValidException,
    WorkspaceException,
    read_baginfos_from_zip,
    WorkspaceGoneException,
    to_workspace_url,
    to_workspace_dir,
)
from ocrd_webapi.models import WorkspaceDb
from ocrd_webapi.database import (
    save_workspace,
    mark_deleted_workspace,
    get_workspace,
)
from ocrd_webapi.constants import WORKSPACES_DIR


class WorkspaceManager:
    """Class to handle workspace related tasks"""

    def __init__(self):
        self.log = getLogger('ocrd_webapi.workspace_manager')
        if not os.path.exists(WORKSPACES_DIR):
            Path(WORKSPACES_DIR).mkdir(parents=True, exist_ok=True)
            self.log.info("createt not existing workspaces-directory: %s" % WORKSPACES_DIR)
        else:
            self.log.info("workspaces-directory is '%s'" % WORKSPACES_DIR)

    async def create_workspace_from_zip(self, file: str, uid: Union[str, None] = None) -> Union[WorkspaceRsrc]:
        """
        create a workspace from an ocrd-zipfile

        Args:
            file: ocrd-zip of workspace
            uid (str): the uid is used as workspace-directory. If `None`, an uuid is created for
                this. If corresponding dir already existing, None is returned

        Returns:
            'WorkspaceRsrc' or None
        """
        if uid:
            workspace_dir = to_workspace_dir(uid)
            if os.path.exists(workspace_dir):
                self.log.warning("can not update: workspace still/already exists. Id: %s" % uid)
                raise WorkspaceException(f"workspace with id: '{uid}' already exists")
        else:
            uid = str(uuid.uuid4())
            workspace_dir = to_workspace_dir(uid)
        zip_dest = os.path.join(WORKSPACES_DIR, uid + ".zip")

        async with aiofiles.open(zip_dest, "wb") as fpt:
            content = await file.read(1024)
            while content:
                await fpt.write(content)
                content = await file.read(1024)

        try:
            resolver = Resolver()
            valid_report = OcrdZipValidator(resolver, zip_dest).validate()
        except Exception as e:
            raise WorkspaceNotValidException(f"Error during workspace validation: {str(e)}") from e
        if valid_report is not None and not valid_report.is_valid:
            raise WorkspaceNotValidException(valid_report.to_xml())

        workspace_bagger = WorkspaceBagger(resolver)
        workspace_bagger.spill(zip_dest, workspace_dir)

        # TODO: work is done twice here: spill already extracts the bag-info.txt but throws it away.
        # maybe workspace_bagger.spill can be changed to deliver the bag-info.txt here
        bag_infos = read_baginfos_from_zip(zip_dest)
        await save_workspace(uid, bag_infos)
        os.remove(zip_dest)

        return WorkspaceRsrc.from_id(uid)

    async def update_workspace(self, file: str, workspace_id: str):
        """
        Update a workspace

        Delete the workspace if existing and then delegate to
        :py:func:`ocrd_webapi.workspace_manager.WorkspaceManager.create_workspace_from_zip
        """
        workspace_dir = to_workspace_dir(workspace_id)
        if os.path.isdir(workspace_dir):
            shutil.rmtree(workspace_dir)
        return await self.create_workspace_from_zip(file, workspace_id)

    def get_workspace_rsrc(self, workspace_id: str):
        """
        Get workspace available on disk as Resource via it's id
        Returns:
            `WorkspaceRsrc` if `workspace_id` is available else `None`
        """
        possible_dir = to_workspace_dir(workspace_id)
        if not os.path.isdir(possible_dir):
            return None
        return WorkspaceRsrc(id=to_workspace_url(workspace_id), description="Workspace")

    async def get_workspace_bag(self, workspace_id: str) -> Union[str, None]:
        """
        Create workspace bag.

        The resulting zip is stored in the workspaces_dir (`WORKSPACES_DIR`). The Workspace
        could have been changed so recreation of bag-files is necessary. Simply zipping
        is not sufficient.

        Args:
             workspace_id (str): id of workspace to bag
        Returns:
            path to created bag
        """
        # TODO: workspace-bagging must be revised:
        #     - ocrd_identifier is stored in mongodb. use that for bagging. Write method in
        #       database.py to read it from mongdb
        #     - write tests for this cases
        workspace_dir = to_workspace_dir(workspace_id)
        if not os.path.isdir(workspace_dir):
            return None

        dest = self.generate_bag_dest()
        workspace_db = await get_workspace(workspace_id)
        mets = workspace_db.ocrd_mets or "mets.xml"
        identifier = workspace_db.ocrd_identifier
        resolver = Resolver()
        WorkspaceBagger(resolver).bag(
            Workspace(resolver, directory=workspace_dir, mets_basename=mets),
            dest=dest,
            ocrd_identifier=identifier,
            ocrd_mets=mets,
        )
        return dest

    def get_workspaces(self):
        """
        Get a list of all available workspaces
        """
        res = []
        for f in os.scandir(WORKSPACES_DIR):
            if f.is_dir():
                res.append(WorkspaceRsrc(id=to_workspace_url(f.name), description="Workspace"))
        return res

    async def delete_workspace(self, workspace_id: str) -> WorkspaceRsrc:
        """
        Delete a workspace
        """
        workspace_dir = to_workspace_dir(workspace_id)
        if not os.path.isdir(workspace_dir):
            ws = await WorkspaceDb.get(workspace_id)
            if ws and ws.deleted:
                raise WorkspaceGoneException("workspace already deleted")
            raise WorkspaceException(f"workspace with id {workspace_id} not existing")

        shutil.rmtree(workspace_dir)
        await mark_deleted_workspace(workspace_id)

        return WorkspaceRsrc(id=to_workspace_url(workspace_id), description="Workspace")

    def generate_bag_dest(self) -> str:
        """
        return a unique path to store a bag of a workspace at
        """
        return os.path.join(WORKSPACES_DIR, str(uuid.uuid4()) + ".zip")
