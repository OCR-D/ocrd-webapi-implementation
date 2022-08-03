"""
module for implementing the workflow section of the api
"""
import logging
import os
import uuid
from typing import List, Union
import shutil

import aiofiles
from ocrd_webapi.models import WorkflowRsrc
from ocrd_webapi.constants import SERVER_PATH
from ocrd_utils import getLogger
from pathlib import Path


class WorkflowManager:

    def __init__(self, workflows_dir):
        self.log = getLogger('ocrd_webapi.workflow_manager')
        if not os.path.exists(workflows_dir):
            Path(workflows_dir).mkdir(parents=True, exist_ok=True)
            self.log.info("Created non-existing workflows-directory: %s" % workflows_dir)
        else:
            self.log.info("Workflows-directory is '%s'" % workflows_dir)
        self.workflows_dir = workflows_dir

    def get_workflows(self):
        """
        Get a list of all available workflows.
        """
        res = []
        for f in os.scandir(self.workflows_dir):
            if f.is_dir():
                res.append(WorkflowRsrc(id=self.to_workflow_url(f.name), description="Workflow"))
        return res

    async def create_workflow_space(self, file, uid=None) -> Union[WorkflowRsrc, None]:
        """
        Create a new workflow space. Upload a Nextflow script inside.

        Args:
            file: A Nextflow script
            uid (str): The uid is used as workflow_space-directory. If `None`, an uuid is created. 
            If the corresponding dir is already existing, `None` is returned,

        Returns:

        """
        if uid:
            workflow_dir = self.to_workflow_dir(uid)
            if os.path.exists(workflow_dir):
                self.log.warning("cannot create: workflow already existing. Id: %s" % uid)
                return None
        else:
            uid = str(uuid.uuid4())
            workflow_dir = self.to_workflow_dir(uid)
            os.mkdir(workflow_dir)

        nextflow_script = os.path.join(workflow_dir, "nextflow.nf")
        async with aiofiles.open(nextflow_script, "wb") as fpt:
            content = await file.read(1024)
            while content:
                await fpt.write(content)
                content = await file.read(1024)

        # TODO: 
        # 1. Check if the uploaded file is in fact a Nextflow script
        # 2. Validate the Nextflow script

        return WorkflowRsrc(id=self.to_workflow_url(uid), description="Workflow")

    async def update_workflow_space(self, file, workflow_id):
        """
        Update a workflow space

        Delete the workflow space if existing and then delegate to
        :py:func:`ocrd_webapi.workflow_manager.WorkflowManager.create_workflow_space
        """
        workflow_dir = self.to_workflow_dir(workflow_id)
        if os.path.isdir(workflow_dir):
            shutil.rmtree(workflow_dir)
        return await self.create_workflow_space(file, workflow_id)

    def get_workflow_script_rsrc(self, workflow_id):
        """
        Get a workflow script available on disk as a Resource via its id
        Returns:
            `WorkflowRsrc` if `workflow_id` is available else `None`.
        """
        possible_dir = self.to_workflow_dir(workflow_id)
        if not os.path.isdir(possible_dir):
            return None
        
        script_name = "nextflow.nf"
        nextflow_script = self.to_workflow_script(possible_dir, script_name)
        
        return WorkflowRsrc(id=nextflow_script, description="Workflow")

    def to_workflow_script(self, workflow_path: str, script_name: str) -> str:
        """
        Return the local path to workflow with id `workflow_id`. No check if existing.
        """
        return os.path.join(workflow_path, script_name)

    def to_workflow_dir(self, workflow_id: str) -> str:
        """
        Return the local path to workflow with id `workflow_id`. No check if existing.
        """
        return os.path.join(self.workflows_dir, workflow_id)

    def to_workflow_url(self, workflow_id: str) -> str:
        """
        Create the url where the workflow with id `workflow_id` is available.
        """
        return f"{SERVER_PATH}/workflow/{workflow_id}"
