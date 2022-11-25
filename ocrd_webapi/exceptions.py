

# TODO: This needs a better organization and inheritance structure
class ResponseException(Exception):
    """
    Exception to return a response
    """

    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self.body = body


class WorkspaceException(Exception):
    """
    Exception to indicate something is wrong with the workspace
    """
    pass


class WorkflowException(Exception):
    """
    Exception to indicate something is wrong with the workflow
    """
    pass


class WorkspaceNotValidException(WorkspaceException):
    pass


class WorkspaceGoneException(WorkspaceException):
    pass


class WorkflowJobException(WorkflowException):
    """
    Exception to indicate something is wrong with a workflow-job
    """
    pass
