import re
from pydantic import BaseModel, Field, constr
from typing import Any, Dict, Optional, Union

from ocrd_webapi.utils import (
    to_processor_job_url,
    to_workflow_job_url,
    to_workflow_url,
    to_workspace_url,
)


class DiscoveryResponse(BaseModel):
    ram: Union[int, None] = Field(
        None, description='All available RAM in bytes'
    )
    cpu_cores: Union[int, None] = Field(
        None, description='Number of available CPU cores'
    )
    has_cuda: Union[bool, None] = Field(
        None, description="Whether deployment supports NVIDIA's CUDA"
    )
    cuda_version: Union[str, None] = Field(
        None, description='Major/minor version of CUDA'
    )
    has_ocrd_all: Union[bool, None] = Field(
        None, description='Whether deployment is based on ocrd_all'
    )
    ocrd_all_version: Union[str, None] = Field(
        None, description='Git tag of the ocrd_all version implemented'
    )
    has_docker: Union[bool, None] = Field(
        None, description='Whether the OCR-D executables run in a Docker container'
    )


class ProcessorArgs(BaseModel):
    workspace_id: str = None
    input_file_grps: str = None
    output_file_grps: str = None
    page_id: str = None
    parameters: Optional[Dict[str, Any]] = {}


class WorkflowArgs(BaseModel):
    workspace_id: str = None
    workflow_parameters: Optional[Dict[str, Any]] = {}


class JobState(BaseModel):
    __root__: constr(regex=r'^(QUEUED|RUNNING|STOPPED|SUCCESS)')


class ProcessorRsrc(BaseModel):
    description: Union[str, None] = Field(None, description='Description of the thing')
    ref: str = Field(..., description='link to ocrd-tool.json')

    @staticmethod
    def from_name(processor_name):
        # TODO: How to to get a link to the ocrd-tool.json ?
        # Running `ocrd-.* --dump-json`
        # returns the ocrd-tool.json of a processor
        return ProcessorRsrc(
            ref=f"TODO: find a way to get a link to {processor_name}'s ocrd-tool.json",
            description="Processor")

    class Config:
        allow_population_by_field_name = True


class Resource(BaseModel):
    id: str = Field(..., alias='@id', description='URL of this thing')
    description: Union[str, None] = Field(None, description='Description of the thing')

    class Config:
        allow_population_by_field_name = True


class WorkspaceRsrc(Resource):
    @staticmethod
    def from_id(uid) -> 'WorkspaceRsrc':
        return WorkspaceRsrc(id=to_workspace_url(uid), description="Workspace")


class WorkflowRsrc(Resource):
    @staticmethod
    def from_id(uid) -> 'WorkflowRsrc':
        return WorkflowRsrc(id=to_workflow_url(uid), description="Workflow")

    def get_workflow_id(self) -> str:
        """
        get uid from a WorkflowRsrc's workflow-url
        """
        return re.search(r".*/([^/]+)/?$", self.id).group(1)


class Job(Resource):
    state: Optional[JobState] = None

    class Config:
        allow_population_by_field_name = True


class ProcessorJobRsrc(Job):
    processor: Optional[ProcessorRsrc] = None
    workspace: Optional[WorkspaceRsrc] = None

    @staticmethod
    def create(job_id, processor_name, workspace_id, state: JobState = None) -> 'ProcessorJobRsrc':
        processor = ProcessorRsrc.from_name(processor_name)
        workspace = WorkspaceRsrc.from_id(workspace_id)
        return ProcessorJobRsrc(
            id=to_processor_job_url(processor_name, job_id), processor=processor,
            workspace=workspace, state=state, description="Processor-Job"
        )


class WorkflowJobRsrc(Job):
    workflow: Optional[WorkflowRsrc]
    workspace: Optional[WorkspaceRsrc]

    @staticmethod
    def create(uid, workflow=WorkflowRsrc, workspace=WorkspaceRsrc, state: JobState = None) -> 'WorkflowJobRsrc':
        workflow_id = workflow.get_workflow_id()
        job_url = to_workflow_job_url(workflow_id, uid)
        return WorkflowJobRsrc(id=job_url, workflow=workflow, workspace=workspace, state=state,
                               description="Workflow-Job")
