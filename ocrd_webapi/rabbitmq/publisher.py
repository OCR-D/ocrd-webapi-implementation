"""
The source code in this file is adapted by reusing
some part of the source code from the official
RabbitMQ documentation.
"""

import json
import logging
import pika
import time

from ocrd_webapi.rabbitmq.constants import (
    DEFAULT_EXCHANGER_NAME,
    DEFAULT_ROUTER,
    LOG_FORMAT,
    LOG_LEVEL,
    RABBIT_MQ_HOST as HOST,
    RABBIT_MQ_PORT as PORT,
    RABBIT_MQ_VHOST as VHOST,
)
from ocrd_webapi.rabbitmq.connector import RMQConnector


class RMQPublisher(RMQConnector):
    def __init__(self, host=HOST, port=PORT, vhost=VHOST, logger=None):
        if logger is None:
            logger = logging.getLogger(__name__)
        logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
        super().__init__(logger=logger, host=host, port=port, vhost=vhost)

        self.message_counter = 0
        self.deliveries = {}
        self.acked_counter = 0
        self.nacked_counter = 0
        self.running = True

    def authenticate_and_connect(self, username, password):
        credentials = pika.credentials.PlainCredentials(
            username,
            password
        )
        self._connection = RMQConnector.open_blocking_connection(
            host=self._host,
            port=self._port,
            vhost=self._vhost,
            credentials=credentials,
        )
        self._channel = RMQConnector.open_blocking_channel(self._connection)

    def setup_defaults(self):
        RMQConnector.declare_and_bind_defaults(self._connection, self._channel)

    def example_run(self):
        while True:
            try:
                messages = 1
                message = f"#{messages}"
                self.publish_to_queue(queue_name=DEFAULT_ROUTER, message=message)
                messages += 1
                time.sleep(2)
            except KeyboardInterrupt:
                self._logger.info("Keyboard interruption detected. Closing down peacefully.")
                exit(0)
            # TODO: Clean leftovers here and inform the RabbitMQ
            #  server about the disconnection of the publisher
            # TODO: Implement the reconnect mechanism
            except Exception:
                reconnect_delay = 10
                self._logger.info(f'Reconnecting after {reconnect_delay} seconds')
                time.sleep(reconnect_delay)

    def publish_to_queue(self, queue_name: str, message: str, exchange_name=None, properties=None):
        if exchange_name is None:
            exchange_name = DEFAULT_EXCHANGER_NAME
        if properties is None:
            headers = {'OCR-D WebApi Header': 'OCR-D WebApi Value'}
            properties = pika.BasicProperties(
                app_id='webapi-processing-broker',
                content_type='application/json',
                headers=headers
            )

        # Note: There is no way to publish to a queue directly.
        # Publishing happens through an exchange agent with
        # a routing key - specified when binding the queue to the exchange
        RMQConnector.basic_publish(
            self._channel,
            exchange_name=exchange_name,
            # The routing key and the queue name must match!
            routing_key=queue_name,
            message_body=json.dumps(message, ensure_ascii=False),
            properties=properties
        )

        self.message_counter += 1
        self.deliveries[self.message_counter] = True
        self._logger.info(f'Published message #{self.message_counter}')

    def enable_delivery_confirmations(self):
        self._logger.info('Enabling delivery confirmations (Confirm.Select RPC)')
        RMQConnector.confirm_delivery(channel=self._channel)

    def __on_delivery_confirmation(self, frame):
        confirmation_type = frame.method.NAME.split('.')[1].lower()
        delivery_tag: int = frame.method.delivery_tag
        ack_multiple = frame.method.multiple

        self._logger.info(f'Received: {confirmation_type} '
                          f'for tag: {delivery_tag} '
                          f'(multiple: {ack_multiple})')

        if confirmation_type == 'ack':
            self.acked_counter += 1
        elif confirmation_type == 'nack':
            self.nacked_counter += 1

        del self.deliveries[delivery_tag]

        if ack_multiple:
            for tmp_tag in list(self.deliveries.keys()):
                if tmp_tag <= delivery_tag:
                    self.acked_counter += 1
                    del self.deliveries[tmp_tag]

        # TODO: Check here for stale entries inside the _deliveries
        #  and attempt to re-delivery with max amount of tries (not defined yet)

        self._logger.info(
            'Published %i messages, %i have yet to be confirmed, '
            '%i were acked and %i were nacked', self.message_counter,
            len(self.deliveries), self.acked_counter, self.nacked_counter)


def main():
    # Connect to localhost:5672 by
    # using the virtual host "/" (%2F)
    publisher = RMQPublisher(host="localhost", port=5672, vhost="/")
    # Configured with definitions.json when building the RabbitMQ image
    # Check Dockerfile-RabbitMQ
    publisher.authenticate_and_connect(
        username="default-publisher",
        password="default-publisher"
    )
    publisher.setup_defaults()
    publisher.enable_delivery_confirmations()
    publisher.example_run()


if __name__ == '__main__':
    # RabbitMQ Server must be running before starting the example
    # I.e., make start-rabbitmq
    main()
