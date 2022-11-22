import os
from pathlib import Path
from typing import Union
import zipfile
import bagit
import tempfile

from ocrd import Resolver
from ocrd_utils import initLogging
from ocrd_validators.ocrd_zip_validator import OcrdZipValidator
from ocrd.workspace import Workspace
from ocrd.workspace_bagger import WorkspaceBagger

from ocrd_webapi.constants import (
    SERVER_URL,
    WORKSPACES_DIR,
    WORKFLOWS_DIR,
)

__all__ = [
    "ResponseException",
    "extract_bag_dest",
    "extract_bag_info",
    "find_upwards",
    "read_bag_info_from_zip",
    "safe_init_logging",
    "to_processor_job_url",
    "to_workflow_job_dir",
    "to_workflow_job_url",
    "to_workflow_dir",
    "to_workflow_url",
    "to_workspace_url",
    "to_workspace_dir",
    "WorkflowJobException",
    "WorkspaceException",
    "WorkspaceGoneException",
    "WorkspaceNotValidException",
]


class ResponseException(Exception):
    """
    Exception to return a response
    """

    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self.body = body


class WorkspaceException(Exception):
    """
    Exception to indicate something is wrong with the workspace
    """
    pass


class WorkspaceNotValidException(WorkspaceException):
    pass


class WorkspaceGoneException(WorkspaceException):
    pass


class WorkflowJobException(Exception):
    """
    Exception to indicate something is wrong with a workflow-job
    """
    pass


def to_workflow_job_dir(workflow_id, job_id) -> str:
    """
    returns path to workflow-job directory
    """
    return os.path.join(WORKFLOWS_DIR, workflow_id, job_id)


def to_workflow_job_url(workflow_id: str, job_id: str) -> str:
    """
    returns path to job-id of the workflow-id
    """
    return f"{SERVER_URL}/workflow/{workflow_id}/{job_id}"


def to_workflow_script(workflow_id: str) -> Union[str, None]:
    workflow_path = to_workflow_dir(workflow_id)

    script_name = None
    for file in os.listdir(workflow_path):
        if file.endswith(".nf"):
            script_name = file

    if not script_name:
        return None

    """
    Return the local path to Nextflow script of `workflow_id`. No check if existing.
    """
    return os.path.join(workflow_path, script_name)


def to_workflow_dir(workflow_id: str) -> str:
    """
    Return the local path to workflow with id `workflow_id`. No check if existing.
    """
    return os.path.join(WORKFLOWS_DIR, workflow_id)


def to_workflow_url(workflow_id: str) -> str:
    """
    create the url where a workflow is available e.g. http://localhost:8000/workflow/{workflow_id}

    does not verify that the workflow_id exists
    """
    return f"{SERVER_URL}/workflow/{workflow_id}"


def to_workspace_url(workspace_id: str) -> str:
    """
    create the url where workspace is available e.g. http://localhost:8000/workspace/{workspace_id}

    does not verify that the workspace_id exists
    """
    return f"{SERVER_URL}/workspace/{workspace_id}"


def to_workspace_dir(workspace_id: str) -> str:
    """
    return path to workspace with id `workspace_id`. No check if existing
    """
    return os.path.join(WORKSPACES_DIR, workspace_id)


def to_processor_job_url(processor_name: str, job_id: str) -> str:
    """
    create the url where the processor job is available e.g. http://localhost:8000/processor/ocrd-dummy/{job_id}

    does not verify that the processor or/and the processor-job exists
    """
    return f"{SERVER_URL}/processor/{processor_name}/{job_id}"


logging_initialized = False


def safe_init_logging() -> None:
    """
    wrapper around ocrd_utils.initLogging. It assures that ocrd_utils.initLogging is only called
    once. This function may be called multiple times
    """
    global logging_initialized
    if not logging_initialized:
        logging_initialized = True
        initLogging()


def extract_bag_info(zip_dest, workspace_dir):
    try:
        resolver = Resolver()
        valid_report = OcrdZipValidator(resolver, zip_dest).validate()
    except Exception as e:
        raise WorkspaceNotValidException(f"Error during workspace validation: {str(e)}") from e

    if valid_report is not None and not valid_report.is_valid:
        raise WorkspaceNotValidException(valid_report.to_xml())

    workspace_bagger = WorkspaceBagger(resolver)
    workspace_bagger.spill(zip_dest, workspace_dir)

    # TODO: work is done twice here: spill already extracts the bag-info.txt but throws it away.
    # maybe workspace_bagger.spill can be changed to deliver the bag-info.txt here
    bag_info = read_bag_info_from_zip(zip_dest)

    return bag_info


def extract_bag_dest(workspace_db, workspace_dir, bag_dest):
    mets = workspace_db.ocrd_mets or "mets.xml"
    identifier = workspace_db.ocrd_identifier
    resolver = Resolver()
    WorkspaceBagger(resolver).bag(
        Workspace(resolver, directory=workspace_dir, mets_basename=mets),
        dest=bag_dest,
        ocrd_identifier=identifier,
        ocrd_mets=mets,
    )


def read_bag_info_from_zip(path_to_zip) -> dict:
    """
    Extracts bag-info.txt from bagit-file and turns it into a dict

    Args:
        path_to_zip: path to bagit-file

    Returns:
        bag-info.txt from bagit as a dict
    """
    with zipfile.ZipFile(path_to_zip, 'r') as z:
        bag_info_bytes = z.read("bag-info.txt")
        with tempfile.NamedTemporaryFile() as tmp:
            with open(tmp.name, 'wb') as f:
                f.write(bag_info_bytes)
            return bagit._load_tag_file(tmp.name)


def find_upwards(filename, cwd: Path = None) -> Union[Path, None]:
    """
    search in current directory and all directories above for 'filename'
    """
    if cwd is None:
        cwd = Path.cwd()
    if cwd == Path(cwd.root) or cwd == cwd.parent:
        return None

    fullpath = cwd / filename
    return fullpath if fullpath.exists() else find_upwards(filename, cwd.parent)
