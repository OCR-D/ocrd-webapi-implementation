from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from ocrd_utils import getLogger
from ocrd_webapi.models.database import (
    WorkflowJobDB,
    WorkspaceDB,
)
from ocrd_webapi.utils import safe_init_logging

safe_init_logging()


async def initiate_database(db_url: str, db_name='ocrd-webapi', doc_models=None):
    if doc_models is None:
        doc_models = [WorkspaceDB, WorkflowJobDB]
    client = AsyncIOMotorClient(db_url)
    # Documentation: https://beanie-odm.dev/
    await init_beanie(
        database=client.get_default_database(default=db_name),
        document_models=doc_models
    )


async def get_workspace(uid):
    return await WorkspaceDB.get(uid)


async def save_workspace(uid: str, bag_info: dict):
    """
    save a workspace to the database. Can also be used to update a workspace

    Arguments:
         uid: uid of the workspace which must be available on disk
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
        _id=uid,
        ocrd_mets=ocrd_mets,
        ocrd_identifier=ocrd_identifier,
        bagit_profile_identifier=bagit_profile_identifier,
        ocrd_base_version_checksum=ocrd_base_version_checksum,
        bag_info_adds=bag_info
    )
    await workspace_db.save()


async def mark_deleted_workspace(uid):
    """
    set 'WorkspaceDb.deleted' to True

    The api should keep track of deleted workspaces according to the specs. This is done with this
    function and the deleted-property
    """
    ws = await WorkspaceDB.get(uid)
    if ws:
        ws.deleted = True
        await ws.save()
    else:
        getLogger("ocrd_webapi.database").warn("Trying to flag not existing workspace as deleted")


async def get_workflow_job(uid):
    return await WorkflowJobDB.get(uid)


async def save_workflow_job(uid: str, workflow_id, workspace_id, state):
    """
    save a workflow_job to the database

    Arguments:
        uid: id of the job
        workflow_id: id of the workflow the job is/was executing
        workspace_id: id of the workspace the job runs on
        state: current state of the job
    """
    job = WorkflowJobDB(
        _id=uid,
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        state=state
    )
    await job.save()


async def set_workflow_job_state(uid, state):
    """
    set state of job to 'state'
    """
    job = await WorkflowJobDB.get(uid)
    if job:
        job.state = state
        await job.save()
