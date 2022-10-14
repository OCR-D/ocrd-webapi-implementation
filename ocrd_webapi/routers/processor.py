from fastapi import APIRouter
import yaml
import os
import httpx
from fastapi.responses import (
    JSONResponse,
)

from typing import (
    Union,
    Dict,
    List,
)

from ocrd_webapi.constants import (
    PROCESSOR_CONFIG_PATH,
    PROCESSOR_WORKSPACES_PATH,
)
from ocrd_webapi.utils import (
    ResponseException,
    to_workspace_dir,
    safe_init_logging,
)
from ocrd_webapi.models import (
    ProcessorArgs,
    ProcessorJobRsrc,
)
from ocrd_utils import getLogger

router = APIRouter(
    tags=["processor"],
)
with open(PROCESSOR_CONFIG_PATH) as fin:
    processor_config = yaml.safe_load(fin)
safe_init_logging()
log = getLogger('ocrd_webapi.processor')


@router.post("/processor/{processor}")
async def run_processor(processor: str, p_args: ProcessorArgs) -> Union[None, ProcessorJobRsrc]:
    """
    run a processor. Delegate call to fitting processing server
    """
    if processor not in processor_config:
        raise ResponseException(404, {"error": "Processor not available"})
    workspace_id = p_args.workspace_id
    if not workspace_id:
        raise ResponseException(422, {"error": "workspace_id missing"})
    if not os.path.exists(to_workspace_dir(p_args.workspace_id)):
        raise ResponseException(500, {"error": f"Workspace not existing. Id: {workspace_id}"})
    if not p_args.input_file_grps:
        raise ResponseException(422, {"error": "input_file_grps missing"})
    if not p_args.output_file_grps:
        raise ResponseException(422, {"error": "output_file_grps missing"})

    url = processor_config[processor]
    # TODO: consider different mets name
    ws_path = os.path.join(PROCESSOR_WORKSPACES_PATH, p_args.workspace_id, "mets.xml")
    data = {
        "path": ws_path,
        "input_file_grps": p_args.input_file_grps.split(","),
        "output_file_grps": p_args.output_file_grps.split(","),
    }
    if p_args.parameters:
        data["parameters"] = p_args.parameters.copy()
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers={"Content-Type": "application/json"}, json=data)

    if not r.is_success:
        log.error(f"error delegating processor-request. Response({r.status_code}): {r.text}")
        raise ResponseException(500, {"error": "delegating processor-request failed"})
    x = r.json()
    job_id, job_state = x["_id"], x["state"]

    return ProcessorJobRsrc.create(job_id, processor, workspace_id, job_state)


@router.get("/processor/{processor}")
async def get_processor(processor: str) -> Union[None, Dict]:
    """
    return processors ocrd-tool.json. Delegates to respective processing server
    """
    if processor not in processor_config:
        raise ResponseException(404, {"error": "Processor not available"})

    url = processor_config[processor]
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers={"Content-Type": "application/json"})

    return JSONResponse(content=r.json())


@router.get("/processor/")
async def list_processors() -> List:
    """
    list all available processors. Delegates to all available processing servers and returs a
    summary of their ocrd-tool.json
    """
    # TODO: maybe use caching unless this should be used to test if processors available
    res = []
    for processor in processor_config:
        url = processor_config[processor]
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(url, headers={"Content-Type": "application/json"})
                res.append(r.json())
            except httpx.ConnectError:
                log.warn(f"Error while listing processors: '{processor}' - '{url}' not responding")

    return JSONResponse(content=res)