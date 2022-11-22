"""
module for implementing the discovery section of the api
"""
import os
import psutil
from ocrd_webapi.models.discovery import DiscoveryResponse


class Discovery:
    @staticmethod
    def discovery() -> DiscoveryResponse:
        """
        Discovery of capabilities of the server
        """
        # TODO: what is the meaning of `has_ocrd_all` and `has_docker`? If docker is used,
        #       (I plan to use docker `ocrd/all:medium` container) does this mean has_docker and
        #       has_ocrd_all  must both be true?
        res = DiscoveryResponse()
        res.ram = psutil.virtual_memory().total / (1024.0 ** 3)
        res.cpu_cores = os.cpu_count()
        res.has_cuda = False
        res.has_ocrd_all = True
        res.has_docker = True
        return res
