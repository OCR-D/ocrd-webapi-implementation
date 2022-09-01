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
from ocrd_webapi.models import (
    WorkflowRsrc,
    WorkflowArgs,
    WorkflowJobRsrc,
    WorkspaceRsrc,
)
from ocrd_webapi.constants import (
    SERVER_PATH,
    WORKSPACES_DIR,
)
from ocrd_webapi.utils import (
    to_workspace_dir,
    WorkflowJobException,
    to_workflow_job_dir,
)
from ocrd_utils import getLogger
from pathlib import Path
from ocrd_webapi.database import save_workflow_job


class WorkflowManager:

    def __init__(self, workflows_dir):
        self.log = getLogger('ocrd_webapi.workflow_manager')
        if not os.path.exists(workflows_dir):
            Path(workflows_dir).mkdir(parents=True, exist_ok=True)
            self.log.info("Created non-existing workflows-directory: %s" % workflows_dir)
        else:
            self.log.info("Workflows-directory is '%s'" % workflows_dir)
        self.workflows_dir = workflows_dir

    def get_workflows(self) -> List[WorkflowRsrc]:
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
        nf_script_path = os.path.join(workflow_dir, file.filename)
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

    def get_workflow_script_rsrc(self, workflow_id: str) -> Union[WorkflowRsrc, None]:
        """
        Get a workflow script available on disk as a Resource via its workflow_id
        Returns:
            `WorkflowRsrc` if `workflow_id` is available else `None`.
        """
        nf_script_path = self.to_workflow_script(workflow_id)
        if not os.path.isfile(nf_script_path):
            return None

        return WorkflowRsrc(id=nf_script_path, description="Workflow nextflow script")

    def to_workflow_script(self, workflow_id: str) -> Union[str, None]:
        workflow_path = self.to_workflow_dir(workflow_id)

        script_name = None
        for file in os.listdir(workflow_path):
            if file.endswith(".nf"):
                script_name = file

        if not script_name:
            return None

        """
        Return the local path to Nextflow script of `workflow_id`. No check if existing.
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

    def create_workflow_execution_space(self, workflow_id) -> [str, str]:
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

    async def start_nf_workflow(self, workflow_id: str, workflow_args: WorkflowArgs) -> Union[WorkflowJobRsrc, None]:
        # Check if Nextflow is installed
        # If installed, get the version
        nf_version = self.is_nf_available()
        if not nf_version:
            raise WorkflowJobException("Nextflow not available")

        self.log.info(f"Using Nextflow version: {nf_version}")

        # nf_script is the path to the Nextflow script inside workflow_id
        nf_script_path = self.to_workflow_script(workflow_id)

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
            # TODO: after the process has finished the state has to be set to STOPPED. Therefore
            #       it may be better to start a background-job and set the state in the end.
            #       Another possibility would be to have a regularly running job which queries all
            #       not stopped jobs in the db and requests its state and changes the state in the
            #       db accordingly:
            #       https://fastapi-utils.davidmontague.xyz/user-guide/repeated-tasks/
        except Exception as error:
            self.log.exception(f"start_nf_workflow: \n{error}")
            raise error
        await save_workflow_job(job_id, workflow_id, workflow_args.workspace_id, 'RUNNING')
        return WorkflowJobRsrc.create(job_id, state='RUNNING',
                                      workflow=WorkflowRsrc.from_id(workflow_id),
                                      workspace=WorkspaceRsrc.from_id(workflow_args.workspace_id))

    def is_job_finished(self, workflow_id, job_id) -> Union[bool, None]:
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
