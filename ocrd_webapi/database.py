from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from ocrd_webapi.utils import (
    safe_init_logging,
)
from ocrd_utils import getLogger

from ocrd_webapi.database_models import (
    WorkflowJobDb,
    WorkspaceDb,
)


safe_init_logging()


async def initiate_database(db_url: str):
    client = AsyncIOMotorClient(db_url)
    # Documentation: https://beanie-odm.dev/
    await init_beanie(
        database=client.get_default_database(default='ocrd-webapi'),
        document_models=[WorkspaceDb, WorkflowJobDb]
    )


async def save_workspace(uid: str, bag_infos: dict):
    """
    save a workspace to the database. Can also be used to update a workspace

    Arguments:
         uid: uid of the workspace which must be available on disk
         bag_infos: dict with key-value-pairs from bag-info.txt
    """
    bag_infos = dict(bag_infos)
    ocrd_mets, ocrd_base_version_checksum = None, None
    ocrd_identifier = bag_infos.pop("Ocrd-Identifier")
    bagit_profile_identifier = bag_infos.pop("BagIt-Profile-Identifier")
    if "Ocrd-Mets" in bag_infos:
        ocrd_mets = bag_infos.pop("Ocrd-Mets")
    if "Ocrd-Base-Version-Checksum" in bag_infos:
        ocrd_base_version_checksum = bag_infos.pop("Ocrd-Base-Version-Checksum")

    workspace_db = WorkspaceDb(
        _id=uid, ocrd_mets=ocrd_mets, ocrd_identifier=ocrd_identifier,
        bagit_profile_identifier=bagit_profile_identifier,
        ocrd_base_version_checksum=ocrd_base_version_checksum, bag_info_adds=bag_infos
    )
    await workspace_db.save()


async def mark_deleted_workspace(uid: str):
    """
    set 'WorkspaceDb.deleted' to True

    The api should keep track of deleted workspaces according to the specs. This is done with this
    function and the deleted-property
    """
    ws = await WorkspaceDb.get(uid)
    if ws:
        ws.deleted = True
        await ws.save()
    else:
        getLogger("ocrd_webapi.database").warn("Trying to flag not existing workspace as deleted")


async def get_workspace(uid: str):
    return await WorkspaceDb.get(uid)


async def save_workflow_job(uid: str, workflow_id, workspace_id, state):
    """
    save a workflow_job to the database

    Arguments:
        uid: id of the job
        workflow_id: id of the workflow the job is/was executing
        workspace_id: id of the workspace the job runs on
        state: current state of the job
    """
    job = WorkflowJobDb(
        _id=uid,
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        state=state
    )
    await job.save()


async def get_workflow_job(uid: str):
    return await WorkflowJobDb.get(uid)


async def set_workflow_job_finished(uid: str):
    """
    set state of job to 'STOPPED'
    """
    job = await WorkflowJobDb.get(uid)
    if job:
        job.state = 'STOPPED'
    await job.save()
