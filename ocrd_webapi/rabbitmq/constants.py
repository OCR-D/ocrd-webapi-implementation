from pkg_resources import resource_filename
import tomli

__all__ = [
    "DEFAULT_EXCHANGER_NAME",
    "DEFAULT_EXCHANGER_TYPE",
    "DEFAULT_QUEUE",
    "RABBIT_MQ_HOST",
    "RABBIT_MQ_PORT",
]

TOML_FILENAME: str = resource_filename(__name__, 'config.toml')
TOML_FD = open(TOML_FILENAME, mode='rb')
TOML_CONFIG = tomli.load(TOML_FD)
TOML_FD.close()

DEFAULT_EXCHANGER_NAME: str = TOML_CONFIG["default_exchange_name"]
DEFAULT_EXCHANGER_TYPE: str = TOML_CONFIG["default_exchange_type"]
DEFAULT_QUEUE: str = TOML_CONFIG["default_queue"]

# "rabbit-mq-host" when Dockerized
RABBIT_MQ_HOST: str = TOML_CONFIG["rabbit_mq_host"]
RABBIT_MQ_PORT: int = TOML_CONFIG["rabbit_mq_port"]
