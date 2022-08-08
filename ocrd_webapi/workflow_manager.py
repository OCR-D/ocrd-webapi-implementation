"""
module for implementing the workflow section of the api
"""
import logging
import os
import uuid
from typing import List, Union
import shutil
import subprocess
import shlex
from re import search as regex_search

import aiofiles
from ocrd_webapi.models import WorkflowRsrc
from ocrd_webapi.constants import (
    SERVER_PATH, 
    WORKSPACES_DIR,
    DEFAULT_NF_SCRIPT_NAME,
)
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

        nf_script_path = os.path.join(workflow_dir, DEFAULT_NF_SCRIPT_NAME)
        async with aiofiles.open(nf_script_path, "wb") as fpt:
            content = await file.read(1024)
            while content:
                await fpt.write(content)
                content = await file.read(1024)

        # TODO: 
        # 1. Check if the uploaded file is in fact a Nextflow script
        # 2. Validate the Nextflow script

        return WorkflowRsrc(id=self.to_workflow_url(uid), description="Workflow")

    async def update_workflow_space(self, file, workflow_id: str):
        """
        Update a workflow space

        Delete the workflow space if existing and then delegate to
        :py:func:`ocrd_webapi.workflow_manager.WorkflowManager.create_workflow_space
        """
        workflow_dir = self.to_workflow_dir(workflow_id)
        if os.path.isdir(workflow_dir):
            shutil.rmtree(workflow_dir)
        return await self.create_workflow_space(file, workflow_id)

    def get_workflow_script_rsrc(self, workflow_id: str):
        """
        Get a workflow script available on disk as a Resource via its workflow_id
        Returns:
            `WorkflowRsrc` if `workflow_id` is available else `None`.
        """
        nf_script_path = self.to_workflow_script(workflow_id)
        if not os.path.isfile(nf_script_path):
            return None
        
        return WorkflowRsrc(id=nf_script_path, description="Workflow nextflow script")

    def to_workflow_script(self, workflow_id: str) -> str:
        workflow_path = self.to_workflow_dir(workflow_id)

        """
        Return the local path to Nextflow script of `workflow_id`. No check if existing.
        """
        return os.path.join(workflow_path, DEFAULT_NF_SCRIPT_NAME)

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

    def parse_nf_version(self, version_string: str) -> Union[str, None]:
        regex_pattern = r"nextflow version\s*([\d.]+)"
        nf_version = regex_search(regex_pattern, version_string).group(1)

        if not nf_version:
            return None

        return nf_version

    def is_nf_available(self) -> Union[str, None]:
        # The path to Nextflow must be in $PATH
        # Otherwise, the full path must be provided

        # TODO: May be a good idea to define 
        # the path to Nextflow somewhere else 
        # (as a config or const parameter)
        ver_cmd = "nextflow -v"

        try: 
            # Raises an exception if the subprocess fails
            ver_process = subprocess.run(shlex.split(ver_cmd),
                                        shell=False,
                                        check=True,
                                        stdout=subprocess.PIPE,
                                        universal_newlines=True)
        except Exception:
            self.log.exception("error in is_nextflow_available. \
                Nextflow installation not found!")
            return None

        nf_version = self.parse_nf_version(ver_process.stdout)

        return nf_version

    def create_workflow_execution_space(self) -> [str, str]:
        job_id = str(uuid.uuid4())
        workflow_dir = self.to_workflow_dir(workflow_id)
        job_dir = os.path.join(workflow_dir, job_id)
        os.mkdir(job_dir)

        return job_id, job_dir

    def build_nf_command(self, nf_script_path: str, ws_dir: str) -> str:
        nf_command = "nextflow -bg"
        nf_command += f" run {nf_script_path}"
        nf_command += f" --workspace {ws_dir}/"
        nf_command += f" --mets {ws_dir}/mets.xml"
        nf_command += " -with-report"

        return nf_command

    def get_nf_out_err_paths(self, job_dir: str) -> [str, str]:
        nf_out = f'{job_dir}/nextflow_out.txt'
        nf_err = f'{job_dir}/nextflow_err.txt'

        return nf_out, nf_err

    def start_nf_workflow(self, workflow_id: str, workspace_id: str) -> Union[WorkflowRsrc, None]:
        # Check if Nextflow is installed
        # If installed, get the version
        nf_version = self.is_nf_available()
        if not nf_version:
            return None

        self.log.info(f"Using Nextflow version: {nf_version}")

        # nf_script is the path to the Nextflow script inside workflow_id
        nf_script_path = self.to_workflow_script(workflow_id)

        # TODO: There should be a better way to achieve this
        # Similar to to_workspace_dir() inside WorkspaceManager
        workspace_dir = f"{WORKSPACES_DIR}/{workspace_id}"

        # TODO: Existence check must be performed here, 
        # both for the script and the ocr-d workspace

        job_id, job_dir = self.create_workflow_execution_space()   
        nf_out, nf_err = self.get_nf_out_err_paths(job_dir)
        nf_command = self.build_nf_command(nf_script_path, workspace_dir)
        try: 
            with open(nf_out,'w+') as nf_out_file:
                with open(nf_err,'w+') as nf_err_file:
                    # Raises an exception if the subprocess fails
                    nf_process = subprocess.run(shlex.split(nf_command),
                                                    shell=False,
                                                    check=True,
                                                    cwd=job_dir,
                                                    stdout=nf_out_file,
                                                    stderr=nf_err_file,
                                                    universal_newlines=True)
        except Exception:
            self.log.exception("error in start_nf_workflow")
            return None        

        return WorkflowRsrc(id=job_id, description=f"Nextflow instance of {workflow_id}")
