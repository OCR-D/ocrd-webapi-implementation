import pika
from .conftest import (
    RABBITMQ_TEST_DEFAULT
)


def test_publish_message_to_rabbitmq(rabbitmq_publisher):
    test_headers = {
        'OCR-D WebApi Test Header': 'OCR-D WebApi Test Value'
    }
    test_properties = pika.BasicProperties(
        app_id='webapi-processing-broker',
        content_type='application/json',
        headers=test_headers
    )
    rabbitmq_publisher.publish_to_queue(
        queue_name=RABBITMQ_TEST_DEFAULT,
        message="RabbitMQ test 123",
        exchange_name=RABBITMQ_TEST_DEFAULT,
        properties=test_properties
    )
    rabbitmq_publisher.publish_to_queue(
        queue_name=RABBITMQ_TEST_DEFAULT,
        message="RabbitMQ test 456",
        exchange_name=RABBITMQ_TEST_DEFAULT,
        properties=test_properties
    )
    assert rabbitmq_publisher.message_counter == 2


def test_consume_2_messages_from_rabbitmq(rabbitmq_consumer):
    # Consume the 1st message
    method_frame, header_frame, message = rabbitmq_consumer.get_one_message(
        queue_name=RABBITMQ_TEST_DEFAULT,
        auto_ack=True
    )
    assert method_frame.delivery_tag == 1
    assert method_frame.message_count == 1  # messages left in the queue
    assert method_frame.redelivered is False
    assert method_frame.exchange == RABBITMQ_TEST_DEFAULT
    assert method_frame.routing_key == RABBITMQ_TEST_DEFAULT
    # It's possible to assert header_frame the same way
    assert message.decode() == '"RabbitMQ test 123"'

    # Consume the 2nd message
    method_frame, header_frame, message = rabbitmq_consumer.get_one_message(
        queue_name=RABBITMQ_TEST_DEFAULT,
        auto_ack=True
    )
    assert method_frame.delivery_tag == 2
    assert method_frame.message_count == 0  # messages left in the queue
    assert method_frame.redelivered is False
    assert method_frame.exchange == RABBITMQ_TEST_DEFAULT
    assert method_frame.routing_key == RABBITMQ_TEST_DEFAULT
    # It's possible to assert header_frame the same way
    assert message.decode() == '"RabbitMQ test 456"'
