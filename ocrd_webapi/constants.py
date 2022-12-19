import os
from dotenv import load_dotenv
load_dotenv()

__all__ = [
    'BASE_DIR',
    'DB_NAME',
    'DB_URL',
    'JOB_DIR',
    'MONGO_TESTDB',
    'SERVER_URL',
    'WORKFLOWS_DIR',
    'WORKSPACES_DIR',
]

# variables for local testing are read from .env in base-dir with `load_dotenv()`
SERVER_URL: str = os.getenv("OCRD_WEBAPI_SERVER_PATH", "http://localhost:8000")
DB_NAME: str = os.getenv("OCRD_WEBAPI_DB_NAME", "ocrd-webapi-db")
# TODO: This constant value takes a lot of different values based on the environment
#  that it is almost impossible to know it's value. Figured out after spending hours on the code.
#  This must be configurable in a better way...
#  consider: https://fastapi.tiangolo.com/advanced/settings/
DB_URL: str = os.getenv("OCRD_WEBAPI_DB_URL", "mongodb://localhost:27018")

# TODO: This is also confusing. This value has to match exactly with the
#  value inside pyproject.toml -> OCRD_WEBAPI_DB_URL = mongodb://localhost:6701/test-ocrd-webapi
#  Moreover, test related constants should not be here but rather somewhere under tests/
MONGO_TESTDB: str = "test-ocrd-webapi"

BASE_DIR: str = os.getenv("OCRD_WEBAPI_STORAGE_DIR", "/tmp/ocrd-webapi-data")
# TODO: `JOB_DIR` is not used anywhere, reconsider this decision.
#  It will be useful, jobs must not be related to workflows folder.
JOB_DIR: str = os.path.join(BASE_DIR, "jobs")
# Warning: Don't change these 2 defaults
# till everything is configured properly
WORKFLOWS_DIR: str = os.path.join(BASE_DIR, "workflows")
WORKSPACES_DIR: str = os.path.join(BASE_DIR, "workspaces")
