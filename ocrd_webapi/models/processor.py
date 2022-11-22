from pydantic import BaseModel, Field
from typing import Optional, Union

from ocrd_webapi.utils import (
    to_processor_job_url
)
from ocrd_webapi.models.base import Job, JobState
from ocrd_webapi.models.workspace import WorkspaceRsrc


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
