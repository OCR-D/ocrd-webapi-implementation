import os
from dotenv import load_dotenv
load_dotenv()

__all__ = [
    'BASE_DIR',
    'DB_URL',
    'JOB_DIR',
    'MONGO_TESTDB',
    'SERVER_URL',
    'WORKFLOWS_DIR',
    'WORKSPACES_DIR',
    'PROCESSOR_CONFIG_PATH',
    'PROCESSOR_WORKSPACES_PATH',
]

# variables for local testing are read from .env in base-dir with `load_dotenv()`
SERVER_URL: str = os.getenv("OCRD_WEBAPI_SERVER_PATH", "http://localhost:8000")
DB_URL: str = os.getenv("OCRD_WEBAPI_DB_URL", "mongodb://localhost:27018")
MONGO_TESTDB = "test-ocrd-webapi"

BASE_DIR: str = os.getenv("OCRD_WEBAPI_STORAGE_DIR", "/tmp/ocrd-webapi-data")
# TODO: `JOB_DIR` is not used anywhere, reconsider this decision
JOB_DIR: str = os.path.join(BASE_DIR, "jobs")
WORKFLOWS_DIR: str = os.path.join(BASE_DIR, "workflows")
WORKSPACES_DIR: str = os.path.join(BASE_DIR, "workspaces")

# path to config file for processing servers
PROCESSOR_CONFIG_PATH: str = os.getenv("OCRD_PROCESSOR_CONFIG_PATH", "processor_config.yml")
# path where workspaces are available on a processing server
PROCESSOR_WORKSPACES_PATH: str = os.getenv("OCRD_PROCESSOR_WORKSPACES_PATH", "/workspaces")
