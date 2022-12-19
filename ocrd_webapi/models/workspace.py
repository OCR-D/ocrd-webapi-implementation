from ocrd_webapi.models.base import Resource


class WorkspaceRsrc(Resource):
    # Local variables:
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource

    @staticmethod
    def create(workspace_url, description=None):
        if not description:
            description = "Workspace"
        return WorkspaceRsrc(resource_url=workspace_url, description=description)
