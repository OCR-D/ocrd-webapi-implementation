from ocrd_webapi.utils import (
    to_workspace_url
)
from ocrd_webapi.models.base import Resource


class WorkspaceRsrc(Resource):
    @staticmethod
    def from_id(uid) -> 'WorkspaceRsrc':
        return WorkspaceRsrc(id=to_workspace_url(uid), description="Workspace")
