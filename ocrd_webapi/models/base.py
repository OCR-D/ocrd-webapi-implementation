from pydantic import BaseModel, Field, constr
from typing import Any, Dict, Optional


class Resource(BaseModel):
    resource_url: str = Field(
        ...,  # the field is required, no default set
        description='URL of this thing'
    )
    description: str = Field(
        default='Description of the thing',
        description='Description of the thing'
    )

    class Config:
        allow_population_by_field_name = True


class JobState(BaseModel):
    __root__: constr(regex=r'^(QUEUED|RUNNING|STOPPED|SUCCESS)')


class Job(Resource):
    # Local variables:
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    job_state: Optional[JobState] = None

    class Config:
        allow_population_by_field_name = True


class ProcessorArgs(BaseModel):
    workspace_id: str = None
    input_file_grps: str = None
    output_file_grps: str = None
    page_id: str = None
    parameters: Optional[Dict[str, Any]] = {}


class WorkflowArgs(BaseModel):
    workspace_id: str = None
    workflow_parameters: Optional[Dict[str, Any]] = {}
