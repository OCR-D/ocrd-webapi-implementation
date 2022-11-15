"""
module for functionality regarding the workspace section of the api
"""
import os
import uuid
from typing import Union

import aiofiles
from ocrd_webapi.models import WorkspaceRsrc
from ocrd.workspace_bagger import WorkspaceBagger
from ocrd.workspace import Workspace
from ocrd_validators.ocrd_zip_validator import OcrdZipValidator
from ocrd import Resolver
from ocrd_utils import getLogger

from ocrd_webapi.utils import (
    WorkspaceNotValidException,
    WorkspaceException,
    read_baginfos_from_zip,
    WorkspaceGoneException,
)
from ocrd_webapi.models import WorkspaceDb
from ocrd_webapi.database import (
    save_workspace,
    mark_deleted_workspace,
    get_workspace,
)

from ocrd_webapi.constants import SERVER_PATH, WORKSPACES_DIR
from ocrd_webapi.resource_manager import ResourceManager


class WorkspaceManager(ResourceManager):
    """Class to handle workspace related tasks"""
    def __init__(self, 
        workspaces_dir=WORKSPACES_DIR, 
        resource_url=SERVER_PATH, 
        resource_router='workspace', 
        logger_label='ocrd_webapi.workspace_manager'):
        super().__init__(workspaces_dir, resource_url, resource_router, logger_label)
        self.__workspaces_dir = workspaces_dir
        self._initiate_resource_dir(self.__workspaces_dir)

    def get_workspaces(self):
        """
        Get a list of all available workspaces.
        """
        ws_resources = self._get_all_resource_dirs(self.__workspaces_dir)
        res = []
        for ws in ws_resources:
            ws_rsrc_url = self._to_resource_url(ws.name)
            res.append(WorkspaceRsrc(id=ws_rsrc_url, description="Workspace"))

        return res

    async def create_workspace_from_zip(self, file: str, uid=None):
        """
        create a workspace from an ocrd-zipfile

        Args:
            file: ocrd-zip of workspace
            uid (str): the uid is used as workspace-directory. If `None`, an uuid is created for
                this. If corresponding dir already existing, None is returned

        Returns:
            'WorkspaceRsrc' or None
        """
        workspace_id, workspace_dir = self._create_resource_dir(uid)
        zip_dest = os.path.join(self.__workspaces_dir, workspace_id + ".zip")
        await self._receive_resource(file, zip_dest)
        bag_infos = self.extract_bag_infos(zip_dest, workspace_dir)
        
        # TODO: Provide a functionality to enable/disable writing to/reading from a DB
        await save_workspace(workspace_id, bag_infos)

        os.remove(zip_dest)
        return WorkspaceRsrc.from_id(workspace_id)

    async def update_workspace(self, file: str, workspace_id):
        """
        Update a workspace

        Delete the workspace if existing and then delegate to
        :py:func:`ocrd_webapi.workspace_manager.WorkspaceManager.create_workspace_from_zip
        """
        self._delete_resource_dir(workspace_id)
        return await self.create_workspace_from_zip(file, workspace_id)

    def get_workspace_rsrc(self, workspace_id):
        """
        Get workspace available on disk as Resource via it's id
        Returns:
            `WorkspaceRsrc` if `workspace_id` is available else `None`
        """
        if self._is_resource_dir_available(workspace_id):
            ws_rsrc_url = self._to_resource_url(workspace_id)
            return WorkspaceRsrc(id=ws_rsrc_url, description="Workspace")
        else:
            return None

    async def get_workspace_bag(self, workspace_id):
        """
        Create workspace bag.

        The resulting zip is stored in the workspaces_dir (`self.__workspaces_dir`). The Workspace
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
        if self._is_resource_dir_available(workspace_id):
            workspace_db = await get_workspace(workspace_id)
            workspace_dir = self._to_resource_dir(workspace_id)
            bag_dest = self.extract_bag_dest(workspace_db, workspace_dir)
            return bag_dest   
        else:
            return None

    async def delete_workspace(self, workspace_id):
        """
        Delete a workspace
        """
        workspace_dir = self._to_resource_dir(workspace_id)
        if not os.path.isdir(workspace_dir):
            ws = await WorkspaceDb.get(workspace_id)
            if ws and ws.deleted:
                raise WorkspaceGoneException("workspace already deleted")
            raise WorkspaceException(f"workspace with id {workspace_id} not existing")

        self._delete_resource_dir(workspace_dir)
        await mark_deleted_workspace(workspace_id)

        ws_rsrc_url = self._to_resource_url(workspace_id)
        return WorkspaceRsrc(id=ws_rsrc_url, description="Workspace")

    # TODO: Should probably go inside utils.py
    def extract_bag_infos(self, zip_dest, workspace_dir):
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

        return bag_infos

    def extract_bag_dest(self, workspace_db, workspace_dir):
        bag_dest = os.path.join(self.__workspaces_dir, str(uuid.uuid4()) + ".zip")
        
        mets = workspace_db.ocrd_mets or "mets.xml"
        identifier = workspace_db.ocrd_identifier
        resolver = Resolver()
        WorkspaceBagger(resolver).bag(
            Workspace(resolver, directory=workspace_dir, mets_basename=mets),
            dest=bag_dest,
            ocrd_identifier=identifier,
            ocrd_mets=mets,
        )

        return bag_dest
