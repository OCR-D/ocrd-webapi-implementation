from .constants import (
    DEFAULT_QUEUE
)
from .message_exchanger import MessageExchanger


class Consumer:
    """
    Consumer class
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

    def define_queue_listener(self, callback_method, queue_name=DEFAULT_QUEUE):
        self.__messageExchanger.receive_from_queue(
            queue_name=queue_name,
            callback=callback_method,
            # acks must be sent manually
            auto_ack=False
        )
        self.__messageExchanger.channel.start_consuming()
