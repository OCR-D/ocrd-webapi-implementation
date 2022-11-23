from typing import Optional

from ocrd_webapi.models.base import Job, JobState, Resource
from ocrd_webapi.models.workspace import WorkspaceRsrc


class WorkflowRsrc(Resource):
    # Local variables:
    # id: (str)          - inherited from Resource
    # description: (str) - inherited from Resource

    @staticmethod
    def create(workflow_url, description="Workflow"):
        return WorkflowRsrc(id=workflow_url, description=description)


class WorkflowJobRsrc(Job):
    # Local variables:
    # id: (str)          - inherited from Resource -> Job
    # description: (str) - inherited from Resource -> Job
    # state: (JobState)  - inherited from Job
    workflow: Optional[WorkflowRsrc]
    workspace: Optional[WorkspaceRsrc]

    @staticmethod
    def create(job_url, workflow_rsrc, workspace_rsrc, job_state: JobState):
        return WorkflowJobRsrc(id=job_url,
                               workflow=workflow_rsrc,
                               workspace=workspace_rsrc,
                               state=job_state,
                               description="Workflow-Job")
