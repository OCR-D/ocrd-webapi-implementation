from ocrd_webapi.models.base import Resource


class WorkspaceRsrc(Resource):
    # Local variables:
    # id: (str)          - inherited from Resource
    # description: (str) - inherited from Resource

    @staticmethod
    def create(workspace_url, description="Workspace"):
        return WorkspaceRsrc(id=workspace_url, description=description)
