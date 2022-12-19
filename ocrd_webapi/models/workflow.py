from typing import Optional

from ocrd_webapi.models.base import Job, JobState, Resource
from ocrd_webapi.models.workspace import WorkspaceRsrc


class WorkflowRsrc(Resource):
    # Local variables:
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource

    @staticmethod
    def create(workflow_url: str, description: str = None):
        if not description:
            description = "Workflow"
        return WorkflowRsrc(
            resource_url=workflow_url,
            description=description
        )


class WorkflowJobRsrc(Job):
    # Local variables:
    # resource_url: (str) - inherited from Resource -> Job
    # description: (str) - inherited from Resource -> Job
    # job_state: (JobState)  - inherited from Job
    workflow_rsrc: Optional[WorkflowRsrc]
    workspace_rsrc: Optional[WorkspaceRsrc]

    @staticmethod
    def create(job_url: str,
               workflow_url: str,
               workspace_url: str,
               job_state: JobState,
               description: str = None):
        if not description:
            description = "Workflow-Job"
        workflow_rsrc = WorkflowRsrc.create(workflow_url=workflow_url)
        workspace_rsrc = WorkspaceRsrc.create(workspace_url=workspace_url)

        return WorkflowJobRsrc(
            resource_url=job_url,
            description=description,
            job_state=job_state,
            workflow_rsrc=workflow_rsrc,
            workspace_rsrc=workspace_rsrc,
        )
