import os


def allocate_asset(name):
    return open(to_asset_path(name), 'rb')


def to_asset_path(name):
    path_to_module = os.path.dirname(__file__)
    return os.path.join(os.path.abspath(path_to_module), "assets", name)


def parse_resource_id(response):
    try:
        return response.json()['resource_id']
    except (AttributeError, KeyError):
        return None


def parse_job_state(response):
    try:
        return response.json()['job_state'].split("/")[-1]
    except (AttributeError, KeyError):
        return None
