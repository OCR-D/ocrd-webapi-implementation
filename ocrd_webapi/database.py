from typing import Union

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from ocrd_utils import getLogger
from ocrd_webapi.constants import DB_NAME
from ocrd_webapi.models.database import (
    WorkflowDB,
    WorkflowJobDB,
    WorkspaceDB,
)
from ocrd_webapi.utils import safe_init_logging

safe_init_logging()


async def initiate_database(
        db_url: str,
        db_name: str = None,
        doc_models: list = None
):
    if db_name is None:
        db_name = DB_NAME
    if doc_models is None:
        doc_models = [
            WorkflowDB,
            WorkspaceDB,
            WorkflowJobDB
        ]
    client = AsyncIOMotorClient(db_url)
    # Documentation: https://beanie-odm.dev/
    await init_beanie(
        database=client.get_default_database(default=db_name),
        document_models=doc_models
    )


async def get_workflow(
        workflow_id
) -> Union[WorkflowDB, None]:
    return await WorkflowDB.get(workflow_id)


async def get_workflow_job(
        job_id
) -> Union[WorkflowJobDB, None]:
    return await WorkflowJobDB.get(job_id)


async def get_workspace(
        workspace_id
) -> Union[WorkspaceDB, None]:
    return await WorkspaceDB.get(workspace_id)


async def mark_deleted_workflow(
        workflow_id
) -> bool:
    wf = await WorkflowDB.get(workflow_id)
    if wf:
        wf.deleted = True
        await wf.save()
        return True
    getLogger("ocrd_webapi.database").warn(
        "Trying to flag not existing workflow as deleted"
    )
    return False


async def mark_deleted_workspace(
        workspace_id
) -> bool:
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
    getLogger("ocrd_webapi.database").warn(
        "Trying to flag not existing workspace as deleted"
    )
    return False


async def save_workflow(
        workflow_id: str
) -> Union[WorkflowDB, None]:
    workflow_db = WorkflowDB(
        _id=workflow_id
    )
    await workflow_db.save()
    return workflow_db


async def save_workspace(
        workspace_id: str,
        bag_info: dict
) -> Union[WorkspaceDB, None]:
    """
    save a workspace to the database. Can also be used to update a workspace

    Arguments:
         workspace_id: uid of the workspace which must be available on disk
         bag_info: dict with key-value-pairs from bag-info.txt
    """
    bag_info = dict(bag_info)
    ocrd_mets, ocrd_base_version_checksum = None, None
    ocrd_identifier = bag_info.pop("Ocrd-Identifier")
    bagit_profile_identifier = bag_info.pop("BagIt-Profile-Identifier")
    if "Ocrd-Mets" in bag_info:
        ocrd_mets = bag_info.pop("Ocrd-Mets")
    if "Ocrd-Base-Version-Checksum" in bag_info:
        ocrd_base_version_checksum = bag_info.pop("Ocrd-Base-Version-Checksum")

    workspace_db = WorkspaceDB(
        _id=workspace_id,
        ocrd_mets=ocrd_mets,
        ocrd_identifier=ocrd_identifier,
        bagit_profile_identifier=bagit_profile_identifier,
        ocrd_base_version_checksum=ocrd_base_version_checksum,
        bag_info_adds=bag_info
    )
    await workspace_db.save()
    return workspace_db


async def save_workflow_job(
        job_id: str,
        workflow_id: str,
        workspace_id: str,
        job_state: str
) -> Union[WorkflowJobDB, None]:
    """
    save a workflow_job to the database

    Arguments:
        job_id: id of the workflow job
        workflow_id: id of the workflow the job is/was executing
        workspace_id: id of the workspace the job runs on
        job_state: current state of the job
    """
    workflow_job = WorkflowJobDB(
        _id=job_id,
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        job_state=job_state
    )
    await workflow_job.save()
    return workflow_job


async def set_workflow_job_state(
        job_id,
        job_state: str
) -> bool:
    """
    set state of job to 'state'
    """
    job = await WorkflowJobDB.get(job_id)
    if job:
        job.job_state = job_state
        await job.save()
        return True
    getLogger("ocrd_webapi.database").warn(
        "Trying to set a state to a non-existing workflow job"
    )
    return False
