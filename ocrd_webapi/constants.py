import os
from dotenv import load_dotenv
load_dotenv()

__all__ = [
    'SERVER_PATH',
    'WORKSPACES_DIR',
    'JOB_DIR',
    'WORKFLOWS_DIR',
    'DB_URL',
]

# variables for local testing are read from .env in base-dir with `load_dotenv()`
SERVER_PATH: str = os.getenv("OCRD_WEBAPI_SERVER_PATH", "http://localhost:8000")
BASE_DIR: str = os.getenv("OCRD_WEBAPI_STORAGE_DIR", "/tmp/ocrd-webapi-data")
DB_URL: str = os.getenv("OCRD_WEBAPI_DB_URL", "mongodb://localhost:27017")

WORKSPACES_DIR: str = os.path.join(BASE_DIR, "workspaces")
JOB_DIR: str = os.path.join(BASE_DIR, "jobs")
WORKFLOWS_DIR: str = os.path.join(BASE_DIR, "workflows")
DEFAULT_NF_SCRIPT_NAME: str = "nextflow.nf"
MONGO_TESTDB = "test_operandi"
