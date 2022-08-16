from pydantic import BaseModel, Field, constr
from typing import Any, Dict, Optional, Union
from beanie import Document
from uuid import UUID, uuid4


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


class WorkspaceRsrc(Resource):
    pass


class WorkflowRsrc(Resource):
    pass


class ProcessorArgs(BaseModel):
    workspace: Optional[WorkspaceRsrc] = None
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
    workspace: Optional[WorkspaceRsrc] = None

    def __init__(self, processor: Optional[Processor] = None,
                 workspace: Optional[WorkspaceRsrc] = None):

        # TODO: Id must be the path to the Processor Job
        id = "dummy-1"
        super().__init__(id=id, description="ProcessorJob")
        self.state = JobState(__root__="RUNNING")
        self.processor = processor
        self.workspace = workspace

    class Config:
        allow_population_by_field_name = True


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
    id: UUID = Field(default_factory=uuid4)
    ocrd_identifier: str
    bagit_profile_identifier: str
    ocrd_base_version_checksum: Optional[str]
    ocrd_mets: Optional[str]
    bag_info_adds: Optional[dict]
    deleted: bool = False

    class Settings:
        name = "workspace"
