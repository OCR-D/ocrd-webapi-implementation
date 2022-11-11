import sys

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
import re
from ocrd_webapi import utils

router = APIRouter(
    tags=["processor"],
)

try:
    with open(utils.find_upwards(PROCESSOR_CONFIG_PATH)) as fin:
        processor_config = yaml.safe_load(fin)
except TypeError:
    print(f"Processor config file not found: {PROCESSOR_CONFIG_PATH}", file=sys.stderr)
    exit(1)

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
        "parameters": p_args.parameters.copy if p_args.parameters else {}
    }
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, headers={"Content-Type": "application/json"}, json=data)
        except (httpx.ConnectError, httpx.ReadError):
            log.error(f"Error while listing processors: '{processor}' - '{url}' not responding")
            return ResponseException(500, {"error": f"Processing-Server not available: {processor}"})

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


@router.get("/processor/{processor}/{job_id}", responses={"201": {"model": ProcessorJobRsrc}})
async def get_processor_job(processor: str, job_id: str) -> ProcessorJobRsrc:
    """
    deliver infos about a procossor job to client. Delegates to Processong-Server exstracts
    job-state and workspace and returns results
    """
    # TODO: when Pull-Request is merged to core: fetch Job from mongodb via beanie and Job-Model
    #       from ocr-d core
    if processor not in processor_config:
        raise ResponseException(404, {"error": "Processor not available"})
    if not job_id:
        raise ResponseException(422, {"error": "job_id missing"})

    url = processor_config[processor]
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{url}/{job_id}", headers={"Content-Type": "application/json"})

    if not r.is_success:
        raise ResponseException(422, {"error": f"no job found for job_id: '{job_id}"})

    job_infos = r.json()
    job_state = job_infos['state']
    workspace_id = re.match(r".*[/]([^/]+)/[^/]+$", job_infos['path']).group(1)
    return ProcessorJobRsrc.create(job_id, processor, workspace_id, job_state)