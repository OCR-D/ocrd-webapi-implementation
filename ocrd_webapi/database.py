from typing import List, Union
from beanie import init_beanie, Document
from motor.motor_asyncio import AsyncIOMotorClient
import logging

from ocrd_webapi.constants import DB_NAME
from ocrd_webapi.models.database import (
    WorkflowDB,
    WorkflowJobDB,
    WorkspaceDB,
)
from ocrd_webapi.utils import call_sync, safe_init_logging

# Warning: Logging blocks completely if safe init is not called in the global scope at least once...
safe_init_logging()

# Having a logger in this scope should be better
# than calling getLogger in every DB method call
logger = logging.getLogger(__name__)


async def initiate_database(db_url: str, db_name: str = None, doc_models: List[Document] = None):
    if db_name is None:
        db_name = DB_NAME
    if doc_models is None:
        doc_models = [WorkflowDB, WorkspaceDB, WorkflowJobDB]

    if db_url:
        logger.info(f"MongoDB Name: {DB_NAME}")
        logger.info(f"MongoDB URL: {db_url}")
    else:
        logger.error(f"MongoDB URL is invalid!")
    client = AsyncIOMotorClient(db_url)
    # Documentation: https://beanie-odm.dev/
    await init_beanie(
        database=client.get_default_database(default=db_name),
        document_models=doc_models
    )


@call_sync
async def sync_initiate_database(db_url: str, db_name: str = None, doc_models: List[Document] = None):
    await initiate_database(db_url, db_name, doc_models)


async def get_workflow(workflow_id) -> Union[WorkflowDB, None]:
    return await WorkflowDB.get(workflow_id)


@call_sync
async def sync_get_workflow(workflow_id) -> Union[WorkflowDB, None]:
    return await get_workflow(workflow_id)


async def get_workflow_path(workflow_id) -> Union[str, None]:
    workflow = await WorkflowDB.get(workflow_id)
    if workflow:
        return workflow.workflow_path
    logger.warning(f"Trying to get a workflow path of a non-existing workflow_id: {workflow_id}")
    return None


@call_sync
async def sync_get_workflow_path(workflow_id) -> Union[str, None]:
    return await get_workflow_path(workflow_id)


async def get_workflow_script_path(workflow_id) -> Union[str, None]:
    workflow = await WorkflowDB.get(workflow_id)
    if workflow:
        return workflow.workflow_script_path
    logger.warning(f"Trying to get a workflow script path of a non-existing workflow_id: {workflow_id}")
    return None


@call_sync
async def sync_get_workflow_script_path(workflow_id) -> Union[str, None]:
    return await get_workflow_script_path(workflow_id)


async def get_workflow_job(job_id) -> Union[WorkflowJobDB, None]:
    return await WorkflowJobDB.get(job_id)


@call_sync
async def sync_get_workflow_job(job_id) -> Union[WorkflowJobDB, None]:
    return await get_workflow_job(job_id)


async def get_workspace(workspace_id) -> Union[WorkspaceDB, None]:
    return await WorkspaceDB.get(workspace_id)


@call_sync
async def sync_get_workspace(workspace_id) -> Union[WorkspaceDB, None]:
    return await get_workspace(workspace_id)


async def get_workspace_mets_path(workspace_id) -> Union[str, None]:
    workspace = await WorkspaceDB.get(workspace_id)
    if workspace:
        return workspace.workspace_mets_path
    logger.warning(f"Trying to get a workspace path of a non-existing workspace_id: {workspace_id}")
    return None


@call_sync
async def sync_get_workspace_mets_path(workspace_id) -> Union[str, None]:
    return await get_workspace_mets_path(workspace_id)


async def mark_deleted_workflow(workflow_id) -> bool:
    wf = await WorkflowDB.get(workflow_id)
    if wf:
        wf.deleted = True
        await wf.save()
        return True
    logger.warning(f"Trying to flag non-existing workflow as deleted: {workflow_id}")
    return False


@call_sync
async def sync_mark_deleted_workflow(workflow_id) -> bool:
    return await mark_deleted_workflow(workflow_id)


async def mark_deleted_workspace(workspace_id) -> bool:
    """
    set 'WorkspaceDb.deleted' to True

    The api should keep track of deleted workspaces according to the specs.
    This is done with this function and the deleted-property
    """
    ws = await WorkspaceDB.get(workspace_id)
    if ws:
        ws.deleted = True
        await ws.save()
        return True
    logger.warning(f"Trying to flag non-existing workspace as deleted: {workspace_id}")
    return False


@call_sync
async def sync_mark_deleted_workspace(workspace_id) -> bool:
    return await mark_deleted_workspace(workspace_id)


async def save_workflow(workflow_id: str, workflow_path: str, workflow_script_path: str) -> Union[WorkflowDB, None]:
    workflow_db = WorkflowDB(_id=workflow_id, workflow_path=workflow_path, workflow_script_path=workflow_script_path)
    await workflow_db.save()
    return workflow_db


@call_sync
async def sync_save_workflow(workflow_id: str, workflow_path: str, workflow_script_path: str) -> Union[WorkflowDB, None]:
    return await sync_save_workflow(workflow_id, workflow_path, workflow_script_path)


async def save_workspace(workspace_id: str, workspace_path: str, bag_info: dict) -> Union[WorkspaceDB, None]:
    """
    save a workspace to the database. Can also be used to update a workspace

    Arguments:
         workspace_id: uid of the workspace which must be available on disk
         workspace_path: the path of the workspace directory on the local disk
         bag_info: dict with key-value-pairs from bag-info.txt
    """

    workspace_mets_path = f"{workspace_path}/mets.xml"

    bag_info = dict(bag_info)
    ocrd_mets, ocrd_base_version_checksum = None, None
    ocrd_identifier = bag_info.pop("Ocrd-Identifier")
    bagit_profile_identifier = bag_info.pop("BagIt-Profile-Identifier")
    if "Ocrd-Mets" in bag_info:
        ocrd_mets = bag_info.pop("Ocrd-Mets")
        workspace_mets_path = ocrd_mets  # Replace it with the real path
    if "Ocrd-Base-Version-Checksum" in bag_info:
        ocrd_base_version_checksum = bag_info.pop("Ocrd-Base-Version-Checksum")

    workspace_db = WorkspaceDB(
        _id=workspace_id,
        workspace_mets_path=workspace_mets_path,
        ocrd_mets=ocrd_mets,
        ocrd_identifier=ocrd_identifier,
        bagit_profile_identifier=bagit_profile_identifier,
        ocrd_base_version_checksum=ocrd_base_version_checksum,
        bag_info_adds=bag_info
    )
    await workspace_db.save()
    return workspace_db


@call_sync
async def sync_save_workspace(workspace_id: str, workspace_path: str, bag_info: dict) -> Union[WorkspaceDB, None]:
    return await save_workspace(workspace_id, workspace_path, bag_info)


async def save_workflow_job(job_id: str, workflow_id: str, workspace_id: str, job_path: str, job_state: str
) -> Union[WorkflowJobDB, None]:
    """
    save a workflow_job to the database

    Arguments:
        job_id: id of the workflow job
        workflow_id: id of the workflow the job is/was executing
        workspace_id: id of the workspace the job runs on
        job_path: the path of the workflow job
        job_state: current state of the job
    """
    workflow_job = WorkflowJobDB(
        _id=job_id,
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        job_path=job_path,
        job_state=job_state
    )
    await workflow_job.save()
    return workflow_job


@call_sync
async def sync_save_workflow_job(job_id: str, workflow_id: str, workspace_id: str, job_path: str, job_state: str
) -> Union[WorkflowJobDB, None]:
    return await save_workflow_job(job_id, workflow_id, workspace_id, job_path, job_state)


async def set_workflow_job_state(job_id, job_state: str) -> bool:
    """
    set state of job to 'state'
    """
    job = await WorkflowJobDB.get(job_id)
    if job:
        job.job_state = job_state
        await job.save()
        return True
    logger.warning(f"Trying to set a state to a non-existing workflow job: {job_id}")
    return False


@call_sync
async def sync_set_workflow_job_state(job_id, job_state: str) -> bool:
    return await set_workflow_job_state(job_id, job_state)


async def get_workflow_job_state(job_id) -> Union[str, None]:
    """
    get state of job
    """
    job = await WorkflowJobDB.get(job_id)
    if job:
        return job.job_state
    logger.warning(f"Trying to get a state of a non-existing workflow job: {job_id}")
    return None


@call_sync
async def sync_get_workflow_job_state(job_id) -> Union[str, None]:
    return await get_workflow_job_state(job_id)
