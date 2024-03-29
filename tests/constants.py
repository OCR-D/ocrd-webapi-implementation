from os import getenv
from os.path import join

__all__ = [
    'DB_NAME',
    'DB_URL',
    'OCRD_WEBAPI_PASSWORD',
    'OCRD_WEBAPI_USERNAME',
    'WORKFLOWS_DIR',
    'WORKSPACES_DIR'
]

# This value has to match exactly with the value inside pyproject.toml
# -> OCRD_WEBAPI_DB_URL = mongodb://localhost:6701/ocrd_webapi_test
DB_NAME: str = getenv("OCRD_WEBAPI_DB_NAME", "ocrd_webapi_test")
DB_URL: str = getenv("OCRD_WEBAPI_DB_URL", "mongodb://localhost:6701")

OCRD_WEBAPI_USERNAME = getenv("OCRD_WEBAPI_USERNAME", "test")
OCRD_WEBAPI_PASSWORD = getenv("OCRD_WEBAPI_PASSWORD", "test")

SERVER_URL: str = getenv("OCRD_WEBAPI_SERVER_PATH", "http://localhost:8000")

BASE_DIR: str = getenv("OCRD_WEBAPI_BASE_DIR", "/tmp/ocrd_webapi_test")
JOBS_ROUTER: str = getenv("OCRD_WEBAPI_JOBS_ROUTER", "jobs")
WORKFLOWS_ROUTER: str = getenv("OCRD_WEBAPI_WORKFLOWS_ROUTER", "workflow")
WORKSPACES_ROUTER: str = getenv("OCRD_WEBAPI_WORKSPACES_ROUTER", "workspace")

WORKFLOWS_DIR = join(BASE_DIR, WORKFLOWS_ROUTER)
WORKSPACES_DIR = join(BASE_DIR, WORKSPACES_ROUTER)
