import re
from typing import Optional

from ocrd_webapi.utils import (
    to_workflow_url,
    to_workflow_job_url,
)
from ocrd_webapi.models.base import Resource
from ocrd_webapi.models.base import Job, JobState
from ocrd_webapi.models.workspace import WorkspaceRsrc


class WorkflowRsrc(Resource):
    @staticmethod
    def from_id(uid) -> 'WorkflowRsrc':
        return WorkflowRsrc(id=to_workflow_url(uid), description="Workflow")

    def get_workflow_id(self) -> str:
        """
        get uid from a WorkflowRsrc's workflow-url
        """
        return re.search(r".*/([^/]+)/?$", self.id).group(1)


class WorkflowJobRsrc(Job):
    workflow: Optional[WorkflowRsrc]
    workspace: Optional[WorkspaceRsrc]

    @staticmethod
    def create(uid,
               workflow=WorkflowRsrc,
               workspace=WorkspaceRsrc,
               state: JobState = None
               ) -> 'WorkflowJobRsrc':

        workflow_id = workflow.get_workflow_id()
        job_url = to_workflow_job_url(workflow_id, uid)
        return WorkflowJobRsrc(id=job_url,
                               workflow=workflow,
                               workspace=workspace,
                               state=state,
                               description="Workflow-Job")

