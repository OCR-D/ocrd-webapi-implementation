import os
from pathlib import Path
from typing import List, Union, Tuple

import aiofiles
import shutil

from ocrd_utils import getLogger
from ocrd_webapi.constants import (
    BASE_DIR,
    SERVER_URL,
)
from ocrd_webapi.utils import generate_id


class ResourceManager:
    # Warning: Don't change the defaults
    # till everything is configured properly
    def __init__(
            self,
            logger_label: str,
            resource_router: str,
            resources_base: str = BASE_DIR,
            resources_url: str = SERVER_URL,
    ):
        self.log = getLogger(logger_label)
        # Server URL
        self._resources_url = resources_url
        # Base directory for all resource managers
        self._resources_base = resources_base
        # Routing key of this manager
        self._resource_router = resource_router

        # Base directory of this manager - BASE_DIR/resource_router
        self._resource_dir = os.path.join(self._resources_base, self._resource_router)
        # self._resource_dir = resource_dir

        log_msg = f"{self._resource_router}s base directory: {self._resource_dir}"
        if not os.path.exists(self._resource_dir):
            Path(self._resource_dir).mkdir(parents=True, exist_ok=True)
            self.log.info(f"Created non-existing {log_msg}")
        else:
            self.log.info(f"Using the existing {log_msg}")

    def get_all_resources(self, local: bool) -> List[str]:
        resources = []
        for res in os.scandir(self._resource_dir):
            if res.is_dir():
                if local:
                    resources.append(res)
                else:
                    url = self._to_resource(res.name, local=False)
                    resources.append(url)
        return resources

    def get_resource(self, resource_id: str, local: bool) -> Union[str, None]:
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

    def get_resource_job(self, resource_id: str, job_id: str, local: bool) -> Union[str, None]:
        # Wrapper, in case the underlying
        # implementation has to change
        return self._to_resource_job(resource_id, job_id, local)

    def get_resource_file(self, resource_id: str, file_ext=None) -> Union[str, None]:
        # Wrapper, in case the underlying
        # implementation has to change
        return self._has_file(resource_id, file_ext=file_ext)

    def _has_dir(self, resource_id: str) -> Union[str, None]:
        """
        Returns the local path of the dir
        identified with `resource_id` or None
        """
        resource_dir = self._to_resource(resource_id, local=True)
        if os.path.exists(resource_dir) and os.path.isdir(resource_dir):
            return resource_dir
        return None

    def _has_file(self, resource_id: str, file_ext=None) -> Union[str, None]:
        """
        Returns the local path of the file identified
        with `resource_id` or None
        """
        resource_dir = self._to_resource(resource_id, local=True)
        for file in os.listdir(resource_dir):
            if file_ext and file.endswith(file_ext):
                return os.path.join(resource_dir, file)
        return None

    def _to_resource(self, resource_id: str, local: bool) -> str:
        """
        Returns the built local path or URL of the
        `resource_id` without any checks
        """
        if local:
            return os.path.join(self._resource_dir, resource_id)
        return f"{self._resources_url}/{self._resource_router}/{resource_id}"

    def _to_resource_job(self, resource_id: str, job_id: str, local: bool) -> Union[str, None]:
        if self._has_dir(resource_id):
            resource_base = self._to_resource(resource_id, local)
            if local:
                return os.path.join(resource_base, job_id)
            return resource_base + f'/{job_id}'
        return None

    def _create_resource_dir(self, resource_id: str) -> Tuple[str, str]:
        if resource_id is None:
            resource_id = generate_id()
        resource_dir = self._to_resource(resource_id, local=True)
        if os.path.exists(resource_dir):
            self.log.error("Cannot create: {resource_id}. Resource already exists!")
            # TODO: Raise an Exception here
        return resource_id, resource_dir

    def _delete_resource_dir(self, resource_id: str) -> Tuple[str, str]:
        resource_dir = self._to_resource(resource_id, local=True)
        if os.path.isdir(resource_dir):
            shutil.rmtree(resource_dir)
        return resource_id, resource_dir

    # TODO: Get rid of the duplication by
    #  implementing a single method
    @staticmethod
    async def _receive_resource(file, resource_dest):
        async with aiofiles.open(resource_dest, "wb") as fpt:
            content = await file.read(1024)
            while content:
                await fpt.write(content)
                content = await file.read(1024)

    @staticmethod
    async def _receive_resource2(file_path, resource_dest):
        with open(file_path, "rb") as fin:
            with open(resource_dest, "wb") as fout:
                content = fin.read(1024)
                while content:
                    fout.write(content)
                    content = fin.read(1024)
