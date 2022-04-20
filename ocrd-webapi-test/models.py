from pydantic import BaseModel, Field


class DiscoveryResponse(BaseModel):
    ram: int | None = Field(None, description='All available RAM in bytes')
    cpu_cores: int | None = Field(None, description='Number of available CPU cores')
    has_cuda: bool | None = Field(
        None, description="Whether deployment supports NVIDIA's CUDA"
    )
    cuda_version: str | None = Field(None, description='Major/minor version of CUDA')
    has_ocrd_all: bool | None = Field(
        None, description='Whether deployment is based on ocrd_all'
    )
    ocrd_all_version: str | None = Field(
        None, description='Git tag of the ocrd_all version implemented'
    )
    has_docker: bool | None = Field(
        None, description='Whether the OCR-D executables run in a Docker container'
    )


class Resource(BaseModel):
    id: str = Field(..., alias='@id', description='URL of this thing')
    description: str | None = Field(None, description='Description of the thing')

    class Config:
        allow_population_by_field_name = True


class Workspace(Resource):
    pass
