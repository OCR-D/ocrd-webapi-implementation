from .constants import SERVER_PATH


class Empty404Exception(Exception):
    """
    Exception to return a 404 with empty json body
    """
    pass


def to_workspace_path(workspace_id: str) -> str:
    """
    create url where workspace is available
    """
    return f"{SERVER_PATH}/workspace/{workspace_id}"
