"""
module for implementing the workflow section of the api
"""
import os
import uuid
from typing import List, Union
import shutil
import subprocess
import shlex
from re import search as regex_search

from ocrd_webapi.models import (
    WorkflowRsrc,
    WorkflowArgs,
    WorkflowJobRsrc,
    WorkspaceRsrc,
)
from ocrd_webapi.utils import (
    to_workflow_job_dir,
    to_workflow_job_url,
    to_workflow_script,
    to_workflow_dir,
    to_workflow_url,
    to_workspace_dir,
    WorkflowJobException,
)
from ocrd_utils import getLogger
from pathlib import Path
from ocrd_webapi.database import save_workflow_job

from ocrd_webapi.constants import SERVER_PATH, WORKFLOWS_DIR
from ocrd_webapi.resource_manager import ResourceManager


class WorkflowManager(ResourceManager):
    """Class to handle workflow related tasks"""
    def __init__(self, 
        workflows_dir=WORKFLOWS_DIR, 
        resource_url=SERVER_PATH, 
        resource_router='workflow', 
        logger_label='ocrd_webapi.workflow_manager'):
        super().__init__(workflows_dir, resource_url, resource_router, logger_label)
        self.__workflows_dir = workflows_dir
        self._initiate_resource_dir(self.__workflows_dir)

    def get_workflows(self):
        """
        Get a list of all available workflows.
        """
        wf_resources = self._get_all_resource_dirs(self.__workflows_dir)
        res = []
        for wf in wf_resources:
            wf_rsrc_url = self._to_resource_url(wf.name)
            res.append(WorkflowRsrc(id=wf_rsrc_url, description="Workflow"))

        return res

    async def create_workflow_space(self, file: str, uid=None):
        """
        Create a new workflow space. Upload a Nextflow script inside.

        Args:
            file: A Nextflow script
            uid (str): The uid is used as workflow_space-directory. If `None`, an uuid is created.
            If the corresponding dir is already existing, `None` is returned,

        Returns:

        """
        workflow_id, workflow_dir = self._create_resource_dir(uid)
        nf_script_dest = os.path.join(workflow_dir, file.filename)
        await self._receive_resource(file, nf_script_dest)

        # TODO:
        # 1. Check if the uploaded file is in fact a Nextflow script
        # 2. Validate the Nextflow script

        # 3. Provide a functionality to enable/disable writing to/reading from a DB
        # await save_workflow(workflow_id, workflow_dir)

        wf_rsrc_url = self._to_resource_url(workflow_id)
        return WorkflowRsrc(id=wf_rsrc_url, description="Workflow")

    async def update_workflow_space(self, file: str, workflow_id):
        """
        Update a workflow space

        Delete the workflow space if existing and then delegate to
        :py:func:`ocrd_webapi.workflow_manager.WorkflowManager.create_workflow_space
        """
        self._delete_resource_dir(workflow_id)
        return await self.create_workflow_space(file, workflow_id)

    def get_workflow_script_rsrc(self, workflow_id):
        """
        Get a workflow script available on disk as a Resource via its workflow_id
        Returns:
            `WorkflowRsrc` if `workflow_id` is available else `None`.
        """
        nf_script_path = self._is_resource_file_available(workflow_id, file_ext='.nf')
        if nf_script_path:
            return WorkflowRsrc(id=nf_script_path, description="Workflow nextflow script")
        
        return None

    def parse_nf_version(self, version_string):
        regex_pattern = r"nextflow version\s*([\d.]+)"
        nf_version = regex_search(regex_pattern, version_string).group(1)

        if not nf_version:
            return None

        return nf_version

    def is_nf_available(self):
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

    def create_workflow_execution_space(self, workflow_id):
        job_id = str(uuid.uuid4())
        workflow_dir = to_workflow_dir(workflow_id)
        job_dir = os.path.join(workflow_dir, job_id)
        os.mkdir(job_dir)

        return job_id, job_dir

    def build_nf_command(self, nf_script_path, ws_dir):
        nf_command = "nextflow -bg"
        nf_command += f" run {nf_script_path}"
        nf_command += f" --workspace {ws_dir}/"
        nf_command += f" --mets {ws_dir}/mets.xml"
        nf_command += " -with-report"

        return nf_command

    def get_nf_out_err_paths(self, job_dir):
        nf_out = f'{job_dir}/nextflow_out.txt'
        nf_err = f'{job_dir}/nextflow_err.txt'

        return nf_out, nf_err

    def start_nf_process(self, job_dir, nf_command):
        nf_out, nf_err = self.get_nf_out_err_paths(job_dir)

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
        # More detailed exception catches needed
        # E.g., was the exception due to IOError or subprocess.CalledProcessError
        except Exception as error:
            self.log.exception(f"Nextflow process failed to start: {error}")

    async def start_nf_workflow(self, workflow_id, workflow_args: WorkflowArgs):
        # TODO: mets-name can differ from mets.xml. The name of the mets is stored in the mongdb
        #       (ocrd_webapi.models.WorkspaceDb.ocrd_mets). Try to make it possible to tell nextflow the
        #       name of the mets if it is not mets.xml.

        # Check if Nextflow is installed
        # If installed, get the version
        nf_version = self.is_nf_available()
        if not nf_version:
            raise WorkflowJobException("Nextflow not available")

        self.log.info(f"Using Nextflow version: {nf_version}")

        # nf_script is the path to the Nextflow script inside workflow_id
        nf_script_path = to_workflow_script(workflow_id)

        workspace_id = workflow_args.workspace_id
        workspace_dir = to_workspace_dir(workspace_id)

        if not os.path.exists(workspace_dir):
            raise WorkflowJobException(f"Workspace not existing. Id: {workspace_id}")
        if not os.path.exists(nf_script_path):
            raise WorkflowJobException(f"Workflow not existing. Id: {workflow_id}")

        job_id, job_dir = self.create_workflow_execution_space(workflow_id)
        nf_command = self.build_nf_command(nf_script_path, workspace_dir)
        try:
            self.start_nf_process(job_dir, nf_command)
        except Exception as error:
            self.log.exception(f"start_nf_workflow: \n{error}")
            raise error
        await save_workflow_job(job_id, workflow_id, workflow_args.workspace_id, 'RUNNING')
        return WorkflowJobRsrc.create(job_id, state='RUNNING',
                                      workflow=WorkflowRsrc.from_id(workflow_id),
                                      workspace=WorkspaceRsrc.from_id(workflow_args.workspace_id))

    def is_job_finished(self, workflow_id, job_id):
        """
        Tests if the file `WORKFLOW_DIR/{workflow_id}/{job_id}/report.html` exists.

        I assume that the report will be created after the job has finished.

        returns:
            true: file exists
            false: file doesn't exist
            None: workflow_id or job_id (path to file) don't exist
        """
        job_dir = to_workflow_job_dir(workflow_id, job_id)
        if not os.path.exists(job_dir):
            return None
        return os.path.exists(os.path.join(job_dir, "report.html"))
