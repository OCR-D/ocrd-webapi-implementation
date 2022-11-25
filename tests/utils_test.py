import os


def allocate_asset(name):
    return open(to_asset_path(name), 'rb')


def to_asset_path(name):
    path_to_module = os.path.dirname(__file__)
    return os.path.join(os.path.abspath(path_to_module), "assets", name)


def assert_status_code(status_code, expected_floor):
    status_floor = status_code // 100
    assert expected_floor == status_floor, \
        f"Response status code expected:{expected_floor}xx, got: {status_code}."


def assert_resources_len(resource_router, resources_len, expected_len):
    assert resources_len == expected_len, \
        f"Amount of {resource_router} resources expected: {expected_len}, got: {resources_len}."


def parse_resource_id(response):
    try:
        return response.json()['@id'].split("/")[-1]
    except (AttributeError, KeyError):
        return None


def parse_job_state(response):
    try:
        return response.json()['job_state'].split("/")[-1]
    except (AttributeError, KeyError):
        return None
