from .constants import (
    DEFAULT_QUEUE
)
from .message_exchanger import MessageExchanger


class Producer:
    """
    Producer class
    """
    def __init__(self, username, password, rabbit_mq_host, rabbit_mq_port):
        self.__messageExchanger = MessageExchanger(username,
                                                   password,
                                                   rabbit_mq_host,
                                                   rabbit_mq_port)

        # It is enough to configure them once, however, to avoid
        # any module dependencies, i.e. which module to start first,
        # defaults are configured both in the Producer and the Consumer
        self.__messageExchanger.configure_default_queue()

    def publish_message_to_queue(self, body, queue_name=DEFAULT_QUEUE):
        self.__messageExchanger.send_to_queue(queue_name=queue_name, message=body)
