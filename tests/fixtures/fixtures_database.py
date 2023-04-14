from pytest import fixture
from requests import get
from pymongo import MongoClient
from ..constants import DB_NAME, DB_URL


# Fixtures related to the Mongo DB
@fixture(scope="session", name="start_mongo_docker")
def fixture_start_mongo_docker(docker_ip, docker_services, do_before_all_tests):
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
            response = get(url)
            if response.status_code == 200:
                return True
        except Exception:
            if retries <= 0:
                return False
            retries -= 1


@fixture(scope="session", name='mongo_client')
def fixture_mongo_client(start_mongo_docker):
    mongo_client = MongoClient(DB_URL, serverSelectionTimeoutMS=3000)
    yield mongo_client


@fixture(scope="session", name='workflow_mongo_coll')
def fixture_workflow_mongo_coll(mongo_client):
    mydb = mongo_client[DB_NAME]
    workflow_coll = mydb["workflow"]
    yield workflow_coll
    workflow_coll.drop()


@fixture(scope="session", name='workflow_job_mongo_coll')
def fixture_workflow_job_mongo_coll(mongo_client):
    mydb = mongo_client[DB_NAME]
    workflow_job_coll = mydb["workflow_job"]
    yield workflow_job_coll
    workflow_job_coll.drop()


@fixture(scope="session", name='workspace_mongo_coll')
def fixture_workspace_mongo_coll(mongo_client):
    mydb = mongo_client[DB_NAME]
    workspace_coll = mydb["workspace"]
    yield workspace_coll
    workspace_coll.drop()
