from pydantic import BaseModel, Field
from typing import Optional, Union

from ocrd_webapi.models.base import Job, JobState, Resource
from ocrd_webapi.models.workspace import WorkspaceRsrc


# TODO: ProcessorRsrc must inherit Resource, not BaseModel
# in order to preserver the consistency
class ProcessorRsrc(BaseModel):
    description: Union[str, None] = Field(None, description='Description of the thing')
    ref: str = Field(..., description='link to ocrd-tool.json')

    @staticmethod
    def create(processor_name):
        # TODO: How to to get a link to the ocrd-tool.json ?
        # Running `ocrd-.* --dump-json`
        # returns the ocrd-tool.json of a processor
        return ProcessorRsrc(
            ref=f"TODO: find a way to get a link to {processor_name}'s ocrd-tool.json",
            description="Processor")

    class Config:
        allow_population_by_field_name = True


class ProcessorJobRsrc(Job):
    # Local variables:
    # id: (str)          - inherited from Resource -> Job
    # description: (str) - inherited from Resource -> Job
    # job_state: (JobState)  - inherited from Job
    processor: Optional[ProcessorRsrc] = None
    workspace: Optional[WorkspaceRsrc] = None

    @staticmethod
    def create(job_url, processor_name, workspace_url, job_state: JobState, description="Processor-Job"):
        processor_rsrc = ProcessorRsrc.create(processor_name)
        workspace_rsrc = WorkspaceRsrc.create(workspace_url)
        return ProcessorJobRsrc(
            id=job_url,
            description=description,
            job_state=job_state,
            processor=processor_rsrc,
            workspace=workspace_rsrc,
        )
