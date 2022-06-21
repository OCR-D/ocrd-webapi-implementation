import os

__all__ = [
    'SERVER_PATH',
    'WORKSPACES_DIR',
    'JOB_DIR',
    'WORKSPACE_ZIPNAME',
]

SERVER_PATH: str = "http://localhost:8000"

BASE_DIR: str = f"{os.getenv('HOME')}/zeugs-ohne-backup/ocrd_webapi"
WORKSPACES_DIR: str = os.path.join(BASE_DIR, "workspaces")
JOB_DIR: str = os.path.join(BASE_DIR, "jobs")
WORKSPACE_ZIPNAME: str = "workspace.zip"
