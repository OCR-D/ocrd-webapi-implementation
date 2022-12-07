"""
The source code in this file is adapted by reusing
some part of the source code from the official
RabbitMQ documentation.
"""

import pika

from ocrd_webapi.rabbitmq.constants import (
    DEFAULT_EXCHANGER_NAME,
    DEFAULT_EXCHANGER_TYPE,
    DEFAULT_QUEUE,
    DEFAULT_ROUTER,
    RECONNECT_WAIT,
    RECONNECT_TRIES,
    PREFETCH_COUNT,
)


class RMQConnector:
    def __init__(self, url, logger):
        self._url = url
        self._logger = logger
        self._prefetch_count = PREFETCH_COUNT

        # Should try reconnecting again
        self._try_reconnecting = False
        # If the module has been stopped with a
        # keyboard interruption, i.e., CTRL + C
        self._gracefully_stopped = False

        self._connection = None
        self._channel = None

    # Connection related methods
    def _open_connection(self):
        """
        Depending on the connection status, callbacks are invoked:
        Successful: on_connection_success
        Failed: on_connection_fail
        Closed: on_connection_closed

        Returns: pika.SelectConnection (connection handler)
        """
        self._logger.info(f'Trying to connect to: {self._url}')
        connection_parameters = pika.URLParameters(self._url)
        selected_connection = pika.SelectConnection(
            connection_parameters,
            on_open_callback=self._on_connection_success,
            on_open_error_callback=self._on_connection_fail,
            on_close_callback=self._on_connection_closed
        )
        return selected_connection

    def _on_connection_success(self, connection):
        self._logger.info('The connection is successful')
        self._logger.debug(f'Connection: {connection}')
        self._open_channel()

    def _on_connection_fail(self, connection, err):
        self._logger.error(f'Connection has failed: {err}')
        self._logger.debug(f'Connection: {connection}')
        if self._try_reconnecting:
            self._reconnect()

    def _on_connection_closed(self, connection, reason):
        self._channel = None
        if self._gracefully_stopped:
            self._connection.ioloop.stop()
        else:
            self._logger.warning(f'Connection has been lost')
            self._logger.debug(f'Connection: {connection}, Reason: {reason}')
            if self._try_reconnecting:
                self._reconnect()

    def _reconnect(self):
        tries = RECONNECT_TRIES
        while tries and self._try_reconnecting:
            self._logger.info(f'Reconnection tries left: {tries}')
            self._logger.info(f'Trying to reconnect again in {RECONNECT_WAIT} seconds.')
            self._connection.ioloop.call_later(
                RECONNECT_WAIT,
                self._connection.ioloop.stop
            )
        self._logger.info(f'Reconnection has failed')
        self._try_reconnecting = False

    def _close_connection(self):
        if self._connection is not None:
            if self._connection.is_closing or self._connection.is_closed:
                self._logger.info('The connection is already closing or closed.')
            else:
                self._logger.info("The connection is closing")
                self._connection.close()

    # Channel related methods
    def _open_channel(self):
        self._logger.info('Opening a new channel')
        self._connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        self._logger.info('Channel opened')
        self._channel = channel
        self._logger.info('Adding on close callback of channel')
        self._channel.add_on_close_callback(self._on_channel_closed)
        self._declare_exchange_agent()

    def _on_channel_closed(self, channel, reason):
        self._logger.warning(f'Channel {channel} was closed. Reason: {reason}')
        self._channel = None
        if not self._gracefully_stopped:
            self._connection.close()

    def _close_channel(self):
        if self._channel is not None:
            self._logger.info('Closing the channel')
            self._channel.close()

    def _declare_exchange_agent(self, exchange_name=None, exchange_type=None, callback=None):
        if exchange_name is None:
            exchange_name = DEFAULT_EXCHANGER_NAME
        if exchange_type is None:
            exchange_type = DEFAULT_EXCHANGER_TYPE
        if callback is None:
            callback = self._on_exchange_declared

        self._logger.info(f'Declaring exchange agent: {exchange_name}')
        self._channel.exchange_declare(exchange=exchange_name,
                                       exchange_type=exchange_type,
                                       callback=callback)

    def _on_exchange_declared(self, frame, exchange_name=None):
        if exchange_name is None:
            exchange_name = DEFAULT_EXCHANGER_NAME
        self._logger.info(f'Exchange agent declared: {exchange_name}')
        self._logger.debug(f'Exchange agent declared in frame: {frame}')
        self._declare_queue()

    def _declare_queue(self, queue_name=None, callback=None):
        if queue_name is None:
            queue_name = DEFAULT_QUEUE
        if callback is None:
            callback = self._on_queue_declared

        self._logger.info(f'Declaring queue: {queue_name}')
        self._channel.queue_declare(queue=queue_name,
                                    callback=callback)

    def _on_queue_declared(self, frame):
        self._logger.debug(f'Binding {DEFAULT_EXCHANGER_NAME} to '
                           f'{DEFAULT_QUEUE} with {DEFAULT_ROUTER} '
                           f'in frame {frame}')
        self._channel.queue_bind(DEFAULT_QUEUE,
                                 DEFAULT_EXCHANGER_NAME,
                                 routing_key=DEFAULT_ROUTER,
                                 callback=self._on_queue_bound)

    def _on_queue_bound(self, frame):
        self._logger.debug(f'Queue bounded successfully: {frame}')
        self._set_qos()

    def _set_qos(self, callback=None):
        """
        This method sets up the consumer prefetch to only be delivered
        one message at a time. The consumer must acknowledge this message
        before RabbitMQ will deliver another one.
        """
        if callback is None:
            callback = self._on_basic_qos_ok
        self._channel.basic_qos(
            prefetch_count=self._prefetch_count,
            callback=callback
        )

    def _on_basic_qos_ok(self, frame):
        self._logger.info(f'QOS set to: {self._prefetch_count}')
        self._logger.debug(f'QOS set in frame: {frame}')
        # Publisher/Consumer has to overwrite this method
        self._start_own()

    # Both the Publisher and Consumer
    # must overwrite this method
    def _start_own(self):
        pass
