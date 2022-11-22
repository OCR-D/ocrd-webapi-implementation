from pydantic import BaseModel, Field
from typing import Union


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
