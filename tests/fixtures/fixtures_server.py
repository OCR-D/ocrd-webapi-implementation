from pytest import fixture
from fastapi.testclient import TestClient
from ocrd_webapi.main import app

from ..constants import (
    OCRD_WEBAPI_USERNAME,
    OCRD_WEBAPI_PASSWORD,
)


@fixture(scope='session', name='client')
def fixture_fastapi_client(start_mongo_docker):
    with TestClient(app) as c:
        yield c


# Dummy authentication
@fixture(name='auth')
def fixture_auth():
    yield OCRD_WEBAPI_USERNAME, OCRD_WEBAPI_PASSWORD
