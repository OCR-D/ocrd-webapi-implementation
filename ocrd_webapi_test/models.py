from pydantic import BaseModel, Field, constr
from typing import Any, Dict, Optional, Union


class DiscoveryResponse(BaseModel):
    ram: Union[int, None] = Field(None, description='All available RAM in bytes')
    cpu_cores: Union[int, None] = Field(None, description='Number of available CPU cores')
    has_cuda: Union[bool, None] = Field(
        None, description="Whether deployment supports NVIDIA's CUDA"
    )
    cuda_version: Union[str, None] = Field(None, description='Major/minor version of CUDA')
    has_ocrd_all: Union[bool, None] = Field(
        None, description='Whether deployment is based on ocrd_all'
    )
    ocrd_all_version: Union[str, None] = Field(
        None, description='Git tag of the ocrd_all version implemented'
    )
    has_docker: Union[bool, None] = Field(
        None, description='Whether the OCR-D executables run in a Docker container'
    )


class Resource(BaseModel):
    id: str = Field(..., alias='@id', description='URL of this thing')
    description: Union[str, None] = Field(None, description='Description of the thing')

    class Config:
        allow_population_by_field_name = True


class Workspace(Resource):
    pass


class ProcessorArgs(BaseModel):
    workspace: Optional[Workspace] = None
    input_file_grps: Optional[str] = None
    output_file_grps: Optional[str] = None
    page_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = {}


class JobState(BaseModel):
    __root__: constr(regex=r'^(QUEUED|RUNNING|STOPPED)')


class Job(Resource):
    state: Optional[JobState] = None

    class Config:
        allow_population_by_field_name = True


class Processor(BaseModel):
    __root__: Any = Field(..., description='The ocrd-tool.json for a specific tool')


class ProcessorJob(Job):
    processor: Optional[Processor] = None
    workspace: Optional[Workspace] = None

    def __init__(self, processor: Optional[Processor] = None, workspace: Optional[Workspace] = None):

        # TODO: Id must be the path to the Processor Job
        id="dummy-1"
        super().__init__(id=id, description="ProcessorJob")
        self.state = JobState(__root__="RUNNING")
        self.processor = processor
        self.workspace = workspace

    class Config:
        allow_population_by_field_name = True
