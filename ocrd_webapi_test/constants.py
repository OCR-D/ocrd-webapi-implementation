import os

__all__ = [
    'SERVER_PATH',
    'WORKSPACES_DIR',
    'JOB_DIR',
]

SERVER_PATH: str = "http://localhost:8000"

BASE_DIR: str = f"{os.getenv('HOME')}/zeugs-ohne-backup/ocrd_webapi"
WORKSPACES_DIR: str = os.path.join(BASE_DIR, "workspaces")
JOB_DIR: str = os.path.join(BASE_DIR, "jobs")
