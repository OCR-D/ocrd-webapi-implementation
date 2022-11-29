import os
from pathlib import Path
import aiofiles
import shutil

from ocrd_utils import getLogger
from ocrd_webapi.utils import generate_id


class ResourceManager:
    # Warning: Don't change the defaults
    # till everything is configured properly
    def __init__(self, resource_dir, resource_url, resource_router, logger_label):
        self.log = getLogger(logger_label)
        self._resource_dir = resource_dir  # Base directory of this manager
        self._resource_url = resource_url  # Server URL
        self._resource_router = resource_router  # Routing key of this manager

        log_msg = f"{self._resource_router}s base directory: {self._resource_dir}"
        if not os.path.exists(self._resource_dir):
            Path(self._resource_dir).mkdir(parents=True, exist_ok=True)
            self.log.info(f"Created non-existing {log_msg}")
        else:
            self.log.info(f"Using the existing {log_msg}")

    def get_all_resources(self, local):
        resources = []
        for res in os.scandir(self._resource_dir):
            if res.is_dir():
                if local:
                    resources.append(res)
                else:
                    url = self._to_resource(res.name, local=False)
                    resources.append(url)
        return resources

    def get_resource(self, resource_id, local):
        """
        Returns the local path of the dir or
        the URL of the `resource_id`
        """
        res_path = self._has_dir(resource_id)
        if res_path:
            if local:
                return res_path
            url = self._to_resource(resource_id, local=False)
            return url
        return None

    def get_resource_job(self, resource_id, job_id, local):
        # Wrapper, in case the underlying
        # implementation has to change
        return self._to_resource_job(resource_id, job_id, local)

    def get_resource_file(self, resource_id, file_ext=None):
        # Wrapper, in case the underlying
        # implementation has to change
        return self._has_file(resource_id, file_ext=file_ext)

    def _has_dir(self, resource_id):
        """
        Returns the local path of the dir
        identified with `resource_id` or None
        """
        resource_dir = self._to_resource(resource_id, local=True)
        if os.path.exists(resource_dir) and os.path.isdir(resource_dir):
            return resource_dir
        return None

    def _has_file(self, resource_id, file_ext=None):
        """
        Returns the local path of the file identified
        with `resource_id` or None
        """
        resource_dir = self._to_resource(resource_id, local=True)
        for file in os.listdir(resource_dir):
            if file_ext and file.endswith(file_ext):
                return os.path.join(resource_dir, file)
        return None

    def _to_resource(self, resource_id, local):
        """
        Returns the built local path or URL of the
        `resource_id` without any checks
        """
        if local:
            return os.path.join(self._resource_dir, resource_id)
        return f"{self._resource_url}/{self._resource_router}/{resource_id}"

    def _to_resource_job(self, resource_id, job_id, local):
        if self._has_dir(resource_id):
            resource_base = self._to_resource(resource_id, local)
            if local:
                return os.path.join(resource_base, job_id)
            return resource_base + f'/{job_id}'
        return None

    def _create_resource_dir(self, resource_id):
        if resource_id is None:
            resource_id = generate_id()
        resource_dir = self._to_resource(resource_id, local=True)
        if os.path.exists(resource_dir):
            self.log.error("Cannot create: {resource_id}. Resource already exists!")
            # TODO: Raise an Exception here
        return resource_id, resource_dir

    def _delete_resource_dir(self, resource_id):
        resource_dir = self._to_resource(resource_id, local=True)
        if os.path.isdir(resource_dir):
            shutil.rmtree(resource_dir)
        return resource_id, resource_dir

    @staticmethod
    async def _receive_resource(file, resource_dest):
        async with aiofiles.open(resource_dest, "wb") as fpt:
            content = await file.read(1024)
            while content:
                await fpt.write(content)
                content = await file.read(1024)
