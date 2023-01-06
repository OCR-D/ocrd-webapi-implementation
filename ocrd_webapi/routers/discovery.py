"""
module for implementing the discovery section of the api
"""
from os import cpu_count
from psutil import virtual_memory
from fastapi import APIRouter
from ocrd_webapi.models.discovery import DiscoveryResponse

router = APIRouter(
    tags=["Discovery"],
)


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
        res.ram = virtual_memory().total / (1024.0 ** 3)
        res.cpu_cores = cpu_count()
        # TODO: Whether cuda is available or not
        res.has_cuda = False
        res.cuda_version = "Default: Cuda not available"
        # TODO: Whether ocrd-all (maximum) image is available or not
        res.has_ocrd_all = False
        res.ocrd_all_version = "Default: OCR-D not available"
        # TODO: Whether docker is installed or not
        res.has_docker = False
        return res


@router.get("/discovery", responses={"200": {"model": DiscoveryResponse}})
async def discovery() -> DiscoveryResponse:
    return Discovery.discovery()
