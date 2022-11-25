import os

from ocrd_webapi import database
from ocrd_webapi.constants import SERVER_URL, WORKFLOWS_DIR
from ocrd_webapi.exceptions import (
    WorkflowJobException,
)
from ocrd_webapi.managers.nextflow_manager import NextflowManager
from ocrd_webapi.managers.resource_manager import ResourceManager
from ocrd_webapi.utils import (
    generate_id,
    to_workspace_dir,
    to_workspace_url,
)


class WorkflowManager(ResourceManager):
    def __init__(self,
                 workflows_dir=WORKFLOWS_DIR,
                 resource_url=SERVER_URL,
                 resource_router='workflow',
                 logger_label='ocrd_webapi.workflow_manager'):
        super().__init__(workflows_dir, resource_url, resource_router, logger_label)
        self._nextflow_executor = NextflowManager()
        self.__workflows_dir = workflows_dir
        self._initiate_resource_dir(self.__workflows_dir)

    def get_workflows(self):
        """
        Get a list of all available workflow urls.
        """
        workflow_urls = self._get_all_resource_urls()
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

        # TODO:
        # 1. Check if the uploaded file is in fact a Nextflow script
        # 2. Validate the Nextflow script

        # 3. Provide a functionality to enable/disable writing to/reading from a DB
        # await save_workflow(workflow_id, workflow_dir)

        return self._to_resource_url(workflow_id)

    async def update_workflow_space(self, file, workflow_id):
        """
        Update a workflow space

        Delete the workflow space if existing and then delegate to
        :py:func:`ocrd_webapi.workflow_manager.WorkflowManager.create_workflow_space
        """
        self._delete_resource_dir(workflow_id)
        return await self.create_workflow_space(file, workflow_id)

    def get_workflow_url(self, workflow_id):
        """
        Get workflow available on disk as Resource via it's id
        """
        if self._is_resource_dir_available(workflow_id):
            return self._to_resource_url(workflow_id)

        return None

    # TODO: Simplify this...
    def get_workflow_script(self, workflow_id):
        """
        Get a workflow script available on disk as a Resource via its workflow_id
        """
        nf_script_path = self._is_resource_file_available(workflow_id, file_ext='.nf')
        if nf_script_path:
            return nf_script_path

        return None

    def create_workflow_execution_space(self, workflow_id):
        job_id = generate_id()
        workflow_dir = self._to_resource_dir(workflow_id)
        job_dir = os.path.join(workflow_dir, job_id)
        os.mkdir(job_dir)

        return job_id, job_dir

    async def start_nf_workflow(self, workflow_id, workspace_id):
        # TODO: mets-name can differ from mets.xml. The name of the mets is stored in the mongodb
        #       (ocrd_webapi.models.WorkspaceDb.ocrd_mets). Try to make it possible to tell nextflow the
        #       name of the mets if it is not mets.xml.        

        # nf_script is the path to the Nextflow script inside workflow_id
        nf_script_path = self._is_resource_file_available(workflow_id, file_ext='.nf')
        workspace_dir = to_workspace_dir(workspace_id)

        # TODO: These checks must happen inside the Resource Manager, not here
        if not os.path.exists(nf_script_path):
            raise WorkflowJobException(f"Workflow not existing. Id: {workflow_id}")
        if not os.path.exists(workspace_dir):
            raise WorkflowJobException(f"Workspace not existing. Id: {workspace_id}")

        job_id, job_dir = self.create_workflow_execution_space(workflow_id)
        self._nextflow_executor.execute_workflow(nf_script_path, workspace_dir, job_dir)

        status = 'RUNNING'
        await database.save_workflow_job(job_id, workflow_id, workspace_id, status)

        parameters = []
        # Job URL
        parameters.append(self._to_resource_job_url(workflow_id, job_id))
        parameters.append(status)
        # Workflow URL
        parameters.append(self._to_resource_url(workflow_id))
        # Workspace URL
        parameters.append(to_workspace_url(workspace_id))

        return parameters

    def is_job_finished(self, workflow_id, job_id):
        """
        Tests if the file `WORKFLOW_DIR/{workflow_id}/{job_id}/report.html` exists.

        I assume that the report will be created after the job has finished.

        returns:
            true: file exists
            false: file doesn't exist
            None: workflow_id or job_id (path to file) don't exist
        """
        job_dir = self._to_resource_job_dir(workflow_id, job_id)
        if not os.path.exists(job_dir):
            return None
        return os.path.exists(os.path.join(job_dir, "report.html"))
