"""
The source code in this file is adapted by reusing
some part of the source code from the official
RabbitMQ documentation.
"""

import functools
import logging
import time

from ocrd_webapi.rabbitmq.constants import (
    DEFAULT_QUEUE,
    LOG_FORMAT,
    LOG_LEVEL
)
from ocrd_webapi.rabbitmq.connector import RMQConnector


class RMQConsumer(RMQConnector):
    def __init__(self, url, logger=None):
        if logger is None:
            logger = logging.getLogger(__name__)
        logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
        super().__init__(url, logger)

        self._consumer_tag = None
        self._consuming = False
        self._was_consuming = False
        self._closing = False

        self._reconnect_delay = 0

    def example_run(self):
        while True:
            try:
                self._connection = self._open_connection()
                self._connection.ioloop.start()
            except KeyboardInterrupt:
                self.stop()
                break
            if self._try_reconnecting:
                self.stop()
                reconnect_delay = self._get_reconnect_delay()
                self._logger.info(f'Reconnecting after {reconnect_delay} seconds')
                time.sleep(reconnect_delay)
            else:
                break

    def stop(self):
        if not self._closing:
            self._closing = True
            self._logger.info('Stopping the consumer')
            if self._consuming:
                self.stop_consuming()
                self._connection.ioloop.start()
            else:
                self._connection.ioloop.stop()
            self._logger.info('The consumer has stopped')

    def start_consuming(self, queue_name=None):
        self._logger.info('Issuing consumer related RPC commands')
        self._logger.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self._on_consumer_cancelled)
        if queue_name is None:
            queue_name = DEFAULT_QUEUE
        self._consumer_tag = self._channel.basic_consume(
            queue_name,
            self._on_message_received
        )
        self._was_consuming = True
        self._consuming = True

    def stop_consuming(self):
        if self._channel:
            self._logger.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            callback = functools.partial(
                self._on_cancelok,
                consumer_id=self._consumer_tag
            )
            self._channel.basic_cancel(self._consumer_tag, callback)

    def _on_cancelok(self, frame, consumer_id):
        self._consuming = False
        self._logger.info(f'RabbitMQ acked the cancellation of: {consumer_id}')
        self._logger.debug(f'Cancellation on frame: {frame}')
        self._close_channel()

    def _on_consumer_cancelled(self, frame):
        self._logger.info(f'The consumer was cancelled remotely in frame: {frame}')
        if self._channel:
            self._channel.close()

    def _on_message_received(self, channel, basic_deliver, properties, body):
        tag = basic_deliver.delivery_tag
        app_id = properties.app_id
        message = body
        self._logger.info(f'Received message #{tag} from {app_id}: {message}')
        self._logger.debug(f'Received message on channel: {channel}')
        self._ack_message(tag)

    def _ack_message(self, delivery_tag):
        self._logger.info(f'Acknowledging message {delivery_tag}')
        self._channel.basic_ack(delivery_tag)

    def reconnect(self):
        """Will be invoked if the connection can't be opened or is
        closed. Indicates that a reconnect is necessary then stops the
        ioloop.
        """
        self._try_reconnecting = True
        self.stop()

    def _get_reconnect_delay(self):
        if self._was_consuming:
            self._reconnect_delay = 0
        else:
            self._reconnect_delay += 1
        if self._reconnect_delay > 30:
            self._reconnect_delay = 30
        return self._reconnect_delay

    def _start_own(self):
        self.start_consuming()


def main():
    username = "default-consumer"
    password = "default-consumer"
    host = "localhost"
    port = "5672"
    # The default virtual host /
    vhost = "%2F"
    connection_attempts = 3
    heartbeat = 3600
    amqp = f"amqp://{username}:{password}@{host}:{port}/{vhost}"
    amqp_parameters = f"connection_attempts={connection_attempts}&heartbeat={heartbeat}"
    amqp_url = f"{amqp}?{amqp_parameters}"

    # Connect to localhost:5672 with username and
    # password by using the virtual host "/" (%2F)
    consumer = RMQConsumer(amqp_url)
    consumer.example_run()


if __name__ == '__main__':
    main()
