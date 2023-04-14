import pytest
import requests
from fastapi.testclient import TestClient
from ocrd_webapi.main import app
from pymongo import MongoClient

from .constants import (
    DB_URL,
    OCRD_WEBAPI_USERNAME,
    OCRD_WEBAPI_PASSWORD,
)


# Fixtures related to the FastAPI
@pytest.fixture(scope='session')
def client(start_mongo_docker):
    with TestClient(app) as c:
        yield c


# Dummy authentication
@pytest.fixture(name='auth')
def _fixture_auth():
    yield OCRD_WEBAPI_USERNAME, OCRD_WEBAPI_PASSWORD


# Fixtures related to the Mongo DB
@pytest.fixture(scope="session")
def start_mongo_docker(docker_ip, docker_services, do_before_all_tests):
    # This returns 6701, the port configured inside tests/docker-compose.yml
    port = docker_services.port_for("mongo", 27017)
    url = f"http://{docker_ip}:{port}"
    docker_services.wait_until_responsive(
        timeout=10.0,
        pause=0.1,
        check=lambda: is_url_responsive(url, retries=10)
    )


def is_url_responsive(url, retries: int = 0):
    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except Exception:
            if retries <= 0:
                return False
            retries -= 1


@pytest.fixture(scope="session", name='mongo_client')
def _fixture_mongo_client(start_mongo_docker):
    mongo_client = MongoClient(DB_URL, serverSelectionTimeoutMS=3000)
    yield mongo_client


@pytest.fixture(scope="session")
def docker_compose_project_name(docker_compose_project_name):
    return "ocrd_webapi_test_image"
