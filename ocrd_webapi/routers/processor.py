from fastapi import APIRouter
import yaml
import os

from ocrd_webapi.constants import (
    PROCESSOR_CONFIG_PATH,
    PROCESSOR_WORKSPACES_PATH,
)
from ocrd_webapi.utils import (
    ResponseException,
)
from ocrd_webapi.models import (
    ProcessorArgs
)

router = APIRouter(
    tags=["processor"],
)
with open(PROCESSOR_CONFIG_PATH) as fin:
    processor_config = yaml.safe_load(fin)


@router.get("/processor/{processor}")
async def run_processor(processor: str, processor_args: ProcessorArgs):
    if processor not in processor_config:
        raise ResponseException(404, "Processor not available")
    url = processor_config[processor]
    workspace_path = os.path.join(PROCESSOR_WORKSPACES_PATH, processor_args.workspace_id)

    # TODO: create call to run processor and execute it



    return f"url: {url}"
