import os
from typing import List, Union, Tuple

from ocrd_webapi import database as db
from ocrd_webapi.constants import WORKSPACES_ROUTER
from ocrd_webapi.exceptions import (
    WorkspaceException,
    WorkspaceGoneException,
)
from ocrd_webapi.managers.resource_manager import ResourceManager
from ocrd_webapi.utils import (
    extract_bag_dest,
    extract_bag_info,
    generate_id,
)


class WorkspaceManager(ResourceManager):
    # Warning: Don't change these defaults
    # till everything is configured properly
    def __init__(
            self,
            resource_router: str = WORKSPACES_ROUTER,
            logger_label: str = 'ocrd_webapi.workspace_manager'
    ):
        super().__init__(
            logger_label=logger_label,
            resource_router=resource_router
        )

    def get_workspaces(self) -> List[str]:
        """
        Get a list of all available workspace urls.
        """
        workspace_urls = self.get_all_resources(local=False)
        return workspace_urls

    async def create_workspace_from_mets_dir(
            self,
            mets_dir: str,
            uid: str = None
    ) -> Tuple[Union[str, None], str]:
        workspace_id, workspace_dir = self._create_resource_dir(uid)
        os.symlink(mets_dir, workspace_dir)
        workspace_url = self.get_resource(workspace_id, local=False)
        return workspace_url, workspace_id

    async def create_workspace_from_zip(
            self,
            file,
            uid: str = None,
            file_stream: bool = True
    ) -> Tuple[Union[str, None], str]:
        """
        create a workspace from an ocrd-zipfile

        Args:
            file: ocrd-zip of workspace
            file_stream: Whether the received file is UploadFile type
            uid (str): the uid is used as workspace-directory. If `None`, an uuid is created for
                this. If corresponding dir already existing, None is returned
        """
        # TODO: Separate the local storage from DB cases
        workspace_id, workspace_dir = self._create_resource_dir(uid)
        # TODO: Get rid of this low level os.path access,
        #  should happen inside the Resource manager
        zip_dest = os.path.join(self._resource_dir, workspace_id + ".zip")
        # TODO: Must be a more optimal way to achieve this
        if file_stream:
            # Handles the UploadFile type file
            await self._receive_resource(file=file, resource_dest=zip_dest)
        else:
            # Handles the file paths
            await self._receive_resource2(file_path=file, resource_dest=zip_dest)

        bag_info = extract_bag_info(zip_dest, workspace_dir)

        # TODO: Provide a functionality to enable/disable writing to/reading from a DB
        await db.save_workspace(workspace_id, bag_info)

        os.remove(zip_dest)
        workspace_url = self.get_resource(workspace_id, local=False)
        return workspace_url, workspace_id

    async def update_workspace(
            self,
            file,
            workspace_id: str
    ) -> Union[str, None]:
        """
        Update a workspace

        Delete the workspace if existing and then delegate to
        :py:func:`ocrd_webapi.workspace_manager.WorkspaceManager.create_workspace_from_zip
        """
        self._delete_resource_dir(workspace_id)
        ws_url, ws_id = await self.create_workspace_from_zip(file=file, uid=workspace_id)
        return ws_url

    # TODO: Refine this and get rid of the low level os.path bullshits
    async def get_workspace_bag(
            self,
            workspace_id: str
    ) -> Union[str, None]:
        """
        Create workspace bag.

        The resulting zip is stored in the workspaces' directory (`self._resource_dir`).
        The Workspace could have been changed so recreation of bag-files is necessary.
        Simply zipping is not sufficient.

        Args:
             workspace_id (str): id of workspace to bag
        Returns:
            path to created bag
        """
        # TODO: Separate the local storage from DB cases
        # TODO: workspace-bagging must be revised:
        #     - ocrd_identifier is stored in mongodb. use that for bagging. Write method in
        #       database.py to read it from mongodb
        #     - write tests for this cases
        if self._has_dir(workspace_id):
            workspace_db = await db.get_workspace(workspace_id)
            workspace_dir = self.get_resource(workspace_id, local=True)
            # TODO: Get rid of this low level os.path access,
            #  should happen inside the Resource manager
            generated_id = generate_id(file_ext=".zip")
            bag_dest = os.path.join(self._resource_dir, generated_id)
            extract_bag_dest(workspace_db, workspace_dir, bag_dest)
            return bag_dest
        return None

    async def delete_workspace(
            self,
            workspace_id: str
    ) -> Union[str, None]:
        """
        Delete a workspace
        """
        # TODO: Separate the local storage from DB cases
        workspace_dir = self.get_resource(workspace_id, local=True)
        if not workspace_dir:
            ws = await db.get_workspace(workspace_id)
            if ws and ws.deleted:
                raise WorkspaceGoneException("workspace already deleted")
            raise WorkspaceException(f"workspace with id {workspace_id} not existing")

        deleted_workspace_url = self.get_resource(workspace_id, local=False)
        self._delete_resource_dir(workspace_id)
        await db.mark_deleted_workspace(workspace_id)

        return deleted_workspace_url

    @staticmethod
    # TODO: Consider static singleton implementation
    # 1. This is needed inside the Workflow router where we
    # avoid giving access to the full WorkspaceManager
    # 2. Probably making the managers to be
    # static singletons is the right approach here
    def static_get_resource(
            resource_id: str,
            local: bool
    ) -> Union[str, None]:
        workspace_manager = WorkspaceManager()
        return workspace_manager.get_resource(
            resource_id=resource_id,
            local=local
        )
