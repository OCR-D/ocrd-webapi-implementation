from beanie import Document
from pydantic import Field
from typing import Optional
from uuid import uuid4

from ocrd_webapi.models import (
    WorkflowJobRsrc,
    WorkflowRsrc,
    WorkspaceRsrc,
)
from ocrd_webapi.utils import (
    to_workflow_job_url
)


class WorkspaceDb(Document):
    """
    Model to store a workspace in the mongo-database.

    Information to handle workspaces and from bag-info.txt are stored here.

    Attributes:
        ocrd_identifier             Ocrd-Identifier (mandatory)
        bagit_profile_identifier    BagIt-Profile-Identifier (mandatory)
        ocrd_base_version_checksum  Ocrd-Base-Version-Checksum (mandatory)
        ocrd_mets                   Ocrd-Mets (optional)
        bag_info_adds               bag-info.txt can also (optionally) contain aditional
                                    key-value-pairs which are saved here
    """
    # TODO: no id is currently generated anywhere, but this might not work if the latter is changed
    id: str = Field(default_factory=uuid4)
    ocrd_identifier: str
    bagit_profile_identifier: str
    ocrd_base_version_checksum: Optional[str]
    ocrd_mets: Optional[str]
    bag_info_adds: Optional[dict]
    deleted: bool = False

    class Collection:
        name = "workspace"


class WorkflowJobDb(Document):
    """
    Model to store a Workflow-Job in the mongo-database.

    Attributes:
        id            the job's id
        workspace_id  id of the workspace on which this job is running
        workflow_id   id of the workflow the job is executing
        state         current state of the job
    """
    id: str = Field(default_factory=uuid4)
    workspace_id: str
    workflow_id: str
    state: str

    class Settings:
        name = "workflow_job"

    def to_rsrc(self) -> 'WorkflowJobRsrc':
        return WorkflowJobRsrc(id=to_workflow_job_url(self.workflow_id, self.id),
                               workflow=WorkflowRsrc.from_id(self.workflow_id),
                               workspace=WorkspaceRsrc.from_id(self.workspace_id),
                               state=self.state, description="Workflow-Job")
