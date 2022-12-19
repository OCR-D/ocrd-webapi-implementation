import os

from ocrd_webapi import database as db
from ocrd_webapi.constants import SERVER_URL, WORKFLOWS_DIR
from ocrd_webapi.exceptions import (
    WorkflowJobException,
)
from ocrd_webapi.managers.nextflow_manager import NextflowManager
from ocrd_webapi.managers.resource_manager import ResourceManager
from ocrd_webapi.managers.workspace_manager import WorkspaceManager
from ocrd_webapi.utils import generate_id


class WorkflowManager(ResourceManager):
    # Warning: Don't change these defaults
    # till everything is configured properly
    def __init__(self,
                 workflows_dir=WORKFLOWS_DIR,
                 resource_url=SERVER_URL,
                 resource_router='workflow',
                 logger_label='ocrd_webapi.workflow_manager'):
        super().__init__(workflows_dir, resource_url, resource_router, logger_label)
        self._nextflow_executor = NextflowManager()
        self.__workflows_dir = workflows_dir

    def get_workflows(self):
        """
        Get a list of all available workflow urls.
        """
        workflow_urls = self.get_all_resources(local=False)
        return workflow_urls

    async def create_workflow_space(self, file, uid=None):
        """
        Create a new workflow space. Upload a Nextflow script inside.

        Args:
            file: A Nextflow script
            uid (str): The uid is used as workflow_space-directory. If `None`, an uuid is created.
            If the corresponding dir is already existing, `None` is returned,

        """
        workflow_id, workflow_dir = self._create_resource_dir(uid)
        os.mkdir(workflow_dir)
        nf_script_dest = os.path.join(workflow_dir, file.filename)
        await self._receive_resource(file, nf_script_dest)
        await db.save_workflow(workflow_id)

        workflow_url = self.get_resource(workflow_id, local=False)
        return workflow_url

    async def update_workflow_space(self, file, workflow_id):
        """
        Update a workflow space

        Delete the workflow space if existing and then delegate to
        :py:func:`ocrd_webapi.workflow_manager.WorkflowManager.create_workflow_space
        """
        self._delete_resource_dir(workflow_id)
        return await self.create_workflow_space(file, workflow_id)

    def create_workflow_execution_space(self, workflow_id):
        job_id = generate_id()
        job_dir = self.get_resource_job(workflow_id, job_id, local=True)
        os.mkdir(job_dir)
        return job_id, job_dir

    async def start_nf_workflow(self, workflow_id, workspace_id):
        # TODO: mets-name can differ from mets.xml. The name of the mets is stored in the mongodb
        #       (ocrd_webapi.models.WorkspaceDb.ocrd_mets). Try to make it possible to tell nextflow the
        #       name of the mets if it is not mets.xml.        

        # nf_script is the path to the Nextflow script inside workflow_id
        nf_script_path = self.get_resource_file(workflow_id, file_ext='.nf')
        workspace_dir = WorkspaceManager.static_get_resource(workspace_id, local=True)

        # TODO: These checks must happen inside the Resource Manager, not here
        if not nf_script_path:
            raise WorkflowJobException(f"Workflow not existing. Id: {workflow_id}")
        if not workspace_dir:
            raise WorkflowJobException(f"Workspace not existing. Id: {workspace_id}")

        job_id, job_dir = self.create_workflow_execution_space(workflow_id)
        self._nextflow_executor.execute_workflow(nf_script_path, workspace_dir, job_dir)

        status = 'RUNNING'
        await db.save_workflow_job(job_id, workflow_id, workspace_id, status)

        parameters = []
        # Job URL
        parameters.append(self.get_resource_job(workflow_id, job_id, local=False))
        parameters.append(status)
        # Workflow URL
        parameters.append(self.get_resource(workflow_id, local=False))
        # Workspace URL
        parameters.append(WorkspaceManager.static_get_resource(workspace_id, local=False))

        return parameters

    async def get_workflow_job(self, workflow_id, job_id):
        # We do not need the result,
        # perform check to set a new job status if required
        await self.is_job_finished(workflow_id, job_id)
        wf_job_db = await db.get_workflow_job(job_id)
        return wf_job_db

    async def is_job_finished(self, workflow_id, job_id):
        """
        Tests if the file `WORKFLOW_DIR/{workflow_id}/{job_id}/report.html` exists.

        I assume that the report will be created after the job has finished.

        returns:
            true: file exists
            false: file doesn't exist
            None: workflow_id or job_id (path to file) don't exist
        """
        job_dir = self.get_resource_job(workflow_id, job_id, local=True)
        if job_dir and self._nextflow_executor.is_nf_report(job_dir):
            await db.set_workflow_job_state(job_id, 'STOPPED')
            return True
        return False
