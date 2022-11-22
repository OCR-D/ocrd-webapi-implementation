import os
import uuid
from pathlib import Path
import aiofiles
import shutil

from ocrd_utils import getLogger


class ResourceManager:
    def __init__(self, resource_dir, resource_url, resource_router, logger_label):
        self.log = getLogger(logger_label)
        self._resource_dir = resource_dir
        self._resource_url = resource_url
        self._resource_router = resource_router

    def _initiate_resource_dir(self, resource_base_dir):
        if not os.path.exists(resource_base_dir):
            Path(resource_base_dir).mkdir(parents=True, exist_ok=True)
            self.log.info(f"Created non-existing {self._resource_router}s base directory: {resource_base_dir}")
        else:
            self.log.info(f"Using the existing {self._resource_router}s base directory: {resource_base_dir}")

        return resource_base_dir

    def _is_resource_dir_available(self, resource_id):
        resource_dir = self._to_resource_dir(resource_id)
        if os.path.exists(resource_dir) and os.path.isdir(resource_dir):
            return resource_dir
        return None

    def _is_resource_file_available(self, resource_id, file_ext=None):
        resource_dir = self._to_resource_dir(resource_id)
        for file in os.listdir(resource_dir):
            if file_ext and file.endswith(file_ext):
                return os.path.join(resource_dir, file)

        return None

    def _to_resource_dir(self, resource_id):
        return os.path.join(self._resource_dir, resource_id)

    def _to_resource_job_dir(self, resource_id, job_id):
        return os.path.join(self._to_resource_dir(resource_id), job_id)

    def _to_resource_url(self, resource_id):
        return f"{self._resource_url}/{self._resource_router}/{resource_id}"

    def _to_resource_job_url(self, resource_id, job_id):
        return self._to_resource_url(resource_id) + f"/{job_id}"

    def _get_all_resource_dirs(self):
        resource_dirs = []
        for f in os.scandir(self._resource_dir):
            if f.is_dir():
                resource_dirs.append(f)

        return resource_dirs

    def _get_all_resource_urls(self):
        resource_urls = []
        for f in os.scandir(self._resource_dir):
            if f.is_dir():
                resource_urls.append(self._to_resource_url(f.name))

        return resource_urls

    def _create_resource_dir(self, resource_id):
        if resource_id is None:
            # assign a randomly generated resource id
            resource_id = str(uuid.uuid4())

        resource_dir = self._to_resource_dir(resource_id)
        if os.path.exists(resource_dir):
            self.log.error("Cannot create a new resource with id: {resource_id}. Resource already exists!")
            # TODO: Raise an Exception here

        return resource_id, resource_dir

    def _delete_resource_dir(self, resource_id):
        resource_dir = self._to_resource_dir(resource_id)
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