from os.path import exists, join
from ocrd_webapi.constants import (
    BASE_DIR,
    WORKFLOWS_ROUTER,
    WORKSPACES_ROUTER
)

# TODO: Utilize the Workflow manager instead of this
WORKFLOWS_DIR = join(BASE_DIR, WORKFLOWS_ROUTER)
# TODO: Utilize the Workspace manager instead of this
WORKSPACES_DIR = join(BASE_DIR, WORKSPACES_ROUTER)


def assert_db_entry_created(resource_from_db, resource_id, db_key):
    assert resource_from_db, \
        "Resource entry was not created in mongodb"
    db_id = resource_from_db[db_key]
    assert db_id == resource_id, \
        f"Wrong resource id. Expected: {resource_id}, found {db_id}"


def assert_db_entry_deleted(resource_from_db, db_key="deleted"):
    assert resource_from_db, \
        "Resource entry should exist, but does not"
    assert resource_from_db[db_key], \
        "Delete flag of the resource should be set to true"


def assert_resources_len(resource_router, resources_len, expected_len):
    assert resources_len == expected_len, \
        f"Amount of {resource_router} resources expected: {expected_len}, got: {resources_len}."


def assert_status_code(status_code, expected_floor):
    status_floor = status_code // 100
    assert expected_floor == status_floor, \
        f"Response status code expected:{expected_floor}xx, got: {status_code}."


def assert_workflow_dir(workflow_id):
    assert exists(join(WORKFLOWS_DIR, workflow_id)), "workflow-dir not existing"


def assert_not_workflow_dir(workflow_id):
    assert not exists(join(WORKFLOWS_DIR, workflow_id)), "workflow-dir existing"


def assert_workspace_dir(workspace_id):
    assert exists(join(WORKSPACES_DIR, workspace_id)), "workspace-dir not existing"


def assert_not_workspace_dir(workspace_id):
    assert not exists(join(WORKSPACES_DIR, workspace_id)), "workspace-dir existing"
