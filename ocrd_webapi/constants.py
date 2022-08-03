import os
from ocrd_webapi.config import *

__all__ = [
    'SERVER_PATH',
    'WORKSPACES_DIR',
    'JOB_DIR',
    'WORKFLOWS_DIR',
]

config = read_config()

SERVER_PATH: str = config[CONFIG_SERVER_PATH]
BASE_DIR: str = config[CONFIG_STORAGE_DIR]
WORKSPACES_DIR: str = os.path.join(BASE_DIR, "workspaces")
JOB_DIR: str = os.path.join(BASE_DIR, "jobs")
WORKFLOWS_DIR: str = os.path.join(BASE_DIR, "workflows")