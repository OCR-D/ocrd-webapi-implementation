"""
The source code in this file is adapted by reusing
some part of the source code from the official
RabbitMQ documentation.
"""

import json
import logging
import pika

from ocrd_webapi.rabbitmq.constants import (
    DEFAULT_EXCHANGER_NAME,
    DEFAULT_ROUTER,
    LOG_FORMAT,
    LOG_LEVEL
)
from ocrd_webapi.rabbitmq.connector import RMQConnector


class RMQPublisher(RMQConnector):
    def __init__(self, url, logger=None):
        if logger is None:
            logger = logging.getLogger(__name__)
        logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
        super().__init__(url, logger)
        self._message_counter = None
        self._acked_counter = None
        self._nacked_counter = None
        self._deliveries = None
        self._running = True

    def example_run(self):
        while self._running:
            self._connection = None
            self._deliveries = {}
            self._acked_counter = 0
            self._nacked_counter = 0
            self._message_counter = 0

            try:
                self._connection = self._open_connection()
                self._connection.ioloop.start()
            except KeyboardInterrupt:
                self.stop()
                if self._connection is not None:
                    if not self._connection.is_closed:
                        self._connection.ioloop.start()

        self._logger.info('Publisher has stopped')

    def stop(self):
        self._logger.info('Stopping the publisher')
        self._running = False
        self._close_channel()
        # TODO: We may not want to close the connection here
        #  consider different scenarios
        self._close_connection()

    def publish_message(self):
        if self._channel is None or not self._channel.is_open:
            return

        app_id = 'webapi-publisher'
        content_type = 'application/json'
        headers = {'Header1': 'Value1',
                   'Header2': 'Value2',
                   'Header3': 'Value3'
                   }

        properties = pika.BasicProperties(
            app_id=app_id,
            content_type=content_type,
            headers=headers
        )

        message = f'Example message #{self._message_counter}'
        self._channel.basic_publish(
            DEFAULT_EXCHANGER_NAME,
            DEFAULT_ROUTER,
            json.dumps(message, ensure_ascii=False),
            properties
        )

        self._message_counter += 1
        self._deliveries[self._message_counter] = True
        self._logger.info(f'Published message #{self._message_counter}')

    def _enable_delivery_confirmations(self, callback=None):
        self._logger.debug('Enabling delivery confirmations (Confirm.Select RPC)')
        if callback is None:
            callback = self._on_delivery_confirmation
        self._channel.confirm_delivery(callback)

    def _on_delivery_confirmation(self, frame):
        confirmation_type = frame.method.NAME.split('.')[1].lower()
        delivery_tag: int = frame.method.delivery_tag
        ack_multiple = frame.method.multiple

        self._logger.info(f'Received: {confirmation_type} '
                          f'for tag: {delivery_tag} '
                          f'(multiple: {ack_multiple})')

        if confirmation_type == 'ack':
            self._acked_counter += 1
        elif confirmation_type == 'nack':
            self._nacked_counter += 1

        del self._deliveries[delivery_tag]

        if ack_multiple:
            for tmp_tag in list(self._deliveries.keys()):
                if tmp_tag <= delivery_tag:
                    self._acked_counter += 1
                    del self._deliveries[tmp_tag]

        # TODO: Check here for stale entries inside the _deliveries
        #  and attempt to re-delivery with max amount of tries (not defined yet)

        self._logger.info(
            'Published %i messages, %i have yet to be confirmed, '
            '%i were acked and %i were nacked', self._message_counter,
            len(self._deliveries), self._acked_counter, self._nacked_counter)

    def _start_own(self):
        self._enable_delivery_confirmations()
        messages = 5
        while messages > 0:
            self.publish_message()
            messages -= 1


def main():
    username = "default-publisher"
    password = "default-publisher"
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
    publisher = RMQPublisher(amqp_url)
    publisher.example_run()


if __name__ == '__main__':
    main()
