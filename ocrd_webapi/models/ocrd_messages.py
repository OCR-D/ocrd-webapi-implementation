# Check here for more details: https://github.com/OCR-D/spec/pull/222/files

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List


class OcrdProcessingMessageModel(BaseModel):
    job_id: str = Field(
        default=None,
        description="ID of the job",
        format="UUID"
    )
    processor_name: str = Field(
        default=None,
        regex="^ocrd-.*$",
        description="Name of the OCR-D processor"
    )
    # Either of the two below must be available
    path_to_mets: Optional[str] = Field(
        default=None,
        description="Path to a METS file"
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description="ID of the workspace",
        format="UUID"
    )
    input_file_grps: List[str] = Field(
        default=None,
        description="List of input file groups"
    )
    output_file_grps: Optional[List[str]] = Field(
        default=None,
        description="List of output file groups"
    )
    page_id: Optional[str] = Field(
        default=None,
        description="Page IDs to be processed",
        example_usage='PHYS_0001..PHYS_0005,PHYS_0007,PHYS_0009'
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description='Parameters passed to the OCR-D processor'
    )
    result_queue_name: Optional[str] = Field(
        default=None,
        description='Name of the queue to which result is published'
    )
    created_time: int = Field(
        default=None,
        description='Unix timestamp of message creation time'
    )

    # TODO: Implement the validator that checks if
    #  either of the path_to_mets or workspace_id is set


class OcrdResultMessageModel(BaseModel):
    job_id: str = Field(
        default=None,
        description="ID of the job",
        format="UUID"
    )
    status: str = Field(
        default=None,
        # TODO: There should be a consistency between here
        #  and the models inside processor.py
        regex='^(SUCCESS|RUNNING|FAILED)$',
        description='Current status of the job'
    )
    # Either of the two below must be available
    path_to_mets: Optional[str] = Field(
        default=None,
        description="Path to a METS file"
    )
    workspace_id: Optional[str] = Field(
        default=None,
        description="ID of the workspace",
        format="UUID"
    )
