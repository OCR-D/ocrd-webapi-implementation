from typing import Dict
from pathlib import Path
import yaml
import os

__all__ = [
    'CONFIG_SERVER_PATH',
    'CONFIG_STORAGE_DIR',
    'read_config'
]


CONFIG_SERVER_PATH = "server_path"
CONFIG_STORAGE_DIR = "data_path"


def read_config() -> Dict:
    """
    read config from file
    """
    config_path = Path(__file__).parent.parent / "config.yml"
    config = {
        CONFIG_SERVER_PATH: "http://localhost:8000",
        CONFIG_STORAGE_DIR: Path.home() / "ocrd-webapi-data",
    }
    if os.path.exists(config_path):
        with open(config_path) as fin:
            config.update(yaml.safe_load(fin))
    return config
