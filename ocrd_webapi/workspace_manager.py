"""
module for functionality regarding the workspace section of the api
"""
import os
import uuid
from typing import List, Union
import shutil

import aiofiles
from ocrd_webapi.models import WorkspaceRsrc
from ocrd.workspace_bagger import WorkspaceBagger
from ocrd.workspace import Workspace
from ocrd_webapi.constants import SERVER_PATH
from ocrd_validators.ocrd_zip_validator import OcrdZipValidator
from ocrd import Resolver
from ocrd_utils import getLogger


# noinspection PyMethodMayBeStatic TODO: remove
# TODO: add types to all method-declarations
class WorkspaceManager:

    def __init__(self, workspaces_dir):
        self.log = getLogger('ocrd_webapi.workspace_manager')
        assert os.path.exists(workspaces_dir), "workspaces dir not existing"
        self.workspaces_dir = workspaces_dir

    def get_workspaces(self):
        res: List = [
            WorkspaceRsrc(id=self.to_workspace_url(f), description="Workspace")
            for f in os.listdir(self.workspaces_dir)
            if os.path.isdir(self.to_workspace_dir(f))
        ]
        return res

    async def create_workspace_from_zip(self, file, uid=None) -> Union[WorkspaceRsrc, None]:
        """
        create a workspace from a ocrd-zipfile

        Args:
            file: ocrd-zip of workspace
            uid (str): the uid is used as workspace-directory. If `None`, an uuid is created for
                this. If corresponding dir already existing, None is returned

        Returns:

        """
        if uid:
            workspace_dir = self.to_workspace_dir(uid)
            if os.path.exists(workspace_dir):
                self.log.warning("can not update: workspace still/already existing. Id: %s" % uid)
                return None
        else:
            uid = str(uuid.uuid4())
            workspace_dir = self.to_workspace_dir(uid)
        zip_dest = os.path.join(self.workspaces_dir, uid + ".zip")

        async with aiofiles.open(zip_dest, "wb") as fpt:
            content = await file.read(1024)
            while content:
                await fpt.write(content)
                content = await file.read(1024)

        resolver = Resolver()
        valid_report = OcrdZipValidator(resolver, zip_dest).validate()
        if not valid_report.is_valid:
            # TODO: raise custom Exception, catch in main and return appropriate error-code
            raise Exception("zip is not valid")

        workspace_bagger = WorkspaceBagger(resolver)
        workspace_bagger.spill(zip_dest, workspace_dir)
        os.remove(zip_dest)

        return WorkspaceRsrc(id=self.to_workspace_url(uid), description="Workspace")

    async def update_workspace(self, file, workspace_id):
        """
        Update a workspace

        Delete the workspace if existing and then delegate to
        :py:func:`ocrd_webapi.workspace_manager.WorkspaceManager.create_workspace_from_zip
        """
        workspace_dir = self.to_workspace_dir(workspace_id)
        if os.path.isdir(workspace_dir):
            shutil.rmtree(workspace_dir)
        return await self.create_workspace_from_zip(file, workspace_id)

    def get_workspace_rsrc(self, workspace_id):
        """
        Get workspace available on disk as Resource via it's id
        Returns:
            `WorkspaceRsrc` if `workspace_id` is available else `None`
        """
        possible_dir = self.to_workspace_dir(workspace_id)
        if not os.path.isdir(possible_dir):
            return None
        return WorkspaceRsrc(id=self.to_workspace_url(workspace_id), description="Workspace")

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
        workspace_dir = self.to_workspace_dir(workspace_id)
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
        dest = self.generate_bag_dest()
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
        for f in os.scandir(self.workspaces_dir):
            if f.is_dir():
                res.append(WorkspaceRsrc(id=self.to_workspace_url(f.name), description="Workspace"))
        return res

    def delete_workspace(self, workspace_id):
        """
        Delete a workspace
        """
        workspace_dir = self.to_workspace_dir(workspace_id)
        if not os.path.isdir(workspace_dir):
            return None
        shutil.rmtree(workspace_dir)
        return WorkspaceRsrc(id=self.to_workspace_url(workspace_id), description="Workspace")

    def to_workspace_dir(self, workspace_id: str) -> str:
        """
        return path to workspace with id `workspace_id`. No check if existing
        """
        return os.path.join(self.workspaces_dir, workspace_id)

    def generate_bag_dest(self) -> str:
        """
        return a unique path to store a bag of a workspace at
        """
        return os.path.join(self.workspaces_dir, str(uuid.uuid4()) + ".zip")

    def to_workspace_url(self, workspace_id: str) -> str:
        """
        create url where workspace is available
        """
        return f"{SERVER_PATH}/workspace/{workspace_id}"
