from beanie import Document
from typing import Optional


# NOTE: Database models must not reuse any
# response models [discovery, processor, workflow, workspace]
# Database models are supposed to be low level models
class WorkspaceDB(Document):
    """
    Model to store a workspace in the mongo-database.

    Information to handle workspaces and from bag-info.txt are stored here.

    Attributes:
        ocrd_identifier             Ocrd-Identifier (mandatory)
        bagit_profile_identifier    BagIt-Profile-Identifier (mandatory)
        ocrd_base_version_checksum  Ocrd-Base-Version-Checksum (mandatory)
        ocrd_mets                   Ocrd-Mets (optional)
        bag_info_adds               bag-info.txt can also (optionally) contain additional
                                    key-value-pairs which are saved here
    """
    workspace_id: str
    workspace_path: str
    workspace_mets_path: str
    ocrd_identifier: str
    bagit_profile_identifier: str
    ocrd_base_version_checksum: Optional[str]
    ocrd_mets: Optional[str]
    bag_info_adds: Optional[dict]
    deleted: bool = False

    class Settings:
        name = "workspace"


class WorkflowDB(Document):
    """
    Model to store a workflow in the mongo-database.
    """
    id: str
    workflow_path: str
    workflow_script_path: str
    deleted: bool = False

    class Settings:
        name = "workflow"


class WorkflowJobDB(Document):
    """
    Model to store a Workflow-Job in the mongo-database.

    Attributes:
        id            the job's id
        workspace_id  id of the workspace on which this job is running
        workflow_id   id of the workflow the job is executing
        job_path      the path of the workflow job
        job_state     current state of the workflow job
    """
    id: str
    workspace_id: str
    workflow_id: str
    job_path: str
    job_state: str

    class Settings:
        name = "workflow_job"
