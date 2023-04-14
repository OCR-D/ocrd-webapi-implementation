import pika
import pika.credentials
import pickle
import pytest
from ocrd_webapi.rabbitmq.connector import RMQConnector
from ocrd_webapi.rabbitmq.publisher import RMQPublisher
from ocrd_webapi.rabbitmq.consumer import RMQConsumer
from ocrd_webapi.rabbitmq import OcrdProcessingMessage
from .constants import RABBITMQ_TEST_DEFAULT


# NOTE: RabbitMQ docker container must be running before starting the tests
# TODO: Start the container if not running -> stop it after tests
@pytest.fixture(scope="session", name='rabbitmq_defaults')
def _fixture_configure_exchange_and_queue():
    credentials = pika.credentials.PlainCredentials("test-session", "test-session")
    temp_connection = RMQConnector.open_blocking_connection(
        credentials=credentials,
        host="localhost",
        port=5672,
        vhost="test"
    )
    temp_channel = RMQConnector.open_blocking_channel(temp_connection)
    RMQConnector.exchange_declare(
        channel=temp_channel,
        exchange_name=RABBITMQ_TEST_DEFAULT,
        exchange_type="direct",
        durable=False
    )
    RMQConnector.queue_declare(
        channel=temp_channel,
        queue_name=RABBITMQ_TEST_DEFAULT,
        durable=False
    )
    RMQConnector.queue_bind(
        channel=temp_channel,
        exchange_name=RABBITMQ_TEST_DEFAULT,
        queue_name=RABBITMQ_TEST_DEFAULT,
        routing_key=RABBITMQ_TEST_DEFAULT
    )
    # Clean all messages inside if any from previous tests
    RMQConnector.queue_purge(
        channel=temp_channel,
        queue_name=RABBITMQ_TEST_DEFAULT
    )


@pytest.fixture(name='rabbitmq_publisher')
def _fixture_rabbitmq_publisher(rabbitmq_defaults):
    publisher = RMQPublisher(host="localhost", port=5672, vhost="test")
    publisher.authenticate_and_connect("test-session", "test-session")
    publisher.enable_delivery_confirmations()
    yield publisher


@pytest.fixture(name='rabbitmq_consumer')
def _fixture_rabbitmq_consumer(rabbitmq_defaults):
    consumer = RMQConsumer(host="localhost", port=5672, vhost="test")
    consumer.authenticate_and_connect("test-session", "test-session")
    yield consumer


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
    assert method_frame.delivery_tag == 1  # 1st delivered message to this queue
    assert method_frame.message_count == 1  # messages left in the queue
    assert method_frame.redelivered is False
    assert method_frame.exchange == RABBITMQ_TEST_DEFAULT
    assert method_frame.routing_key == RABBITMQ_TEST_DEFAULT
    # It's possible to assert header_frame the same way
    assert message.decode() == 'RabbitMQ test 123'

    # Consume the 2nd message
    method_frame, header_frame, message = rabbitmq_consumer.get_one_message(
        queue_name=RABBITMQ_TEST_DEFAULT,
        auto_ack=True
    )
    assert method_frame.delivery_tag == 2  # 2nd delivered message to this queue
    assert method_frame.message_count == 0  # messages left in the queue
    assert method_frame.redelivered is False
    assert method_frame.exchange == RABBITMQ_TEST_DEFAULT
    assert method_frame.routing_key == RABBITMQ_TEST_DEFAULT
    # It's possible to assert header_frame the same way
    assert message.decode() == 'RabbitMQ test 456'


def test_publish_ocrd_message_to_rabbitmq(rabbitmq_publisher):
    ocrd_processing_message = OcrdProcessingMessage(
        job_id="Test_job_id",
        processor_name="ocrd-dummy",
        created_time=None,
        path_to_mets="/test/path/to/mets",
        workspace_id=None,
        input_file_grps=["DEFAULT"],
        output_file_grps=["DUMMY-OUTPUT"],
        parameters=None,
        result_queue_name=None,
    )
    message_bytes = pickle.dumps(ocrd_processing_message)
    rabbitmq_publisher.publish_to_queue(
        queue_name=RABBITMQ_TEST_DEFAULT,
        message=message_bytes,
        exchange_name=RABBITMQ_TEST_DEFAULT,
        properties=None
    )


def test_consume_ocrd_message_from_rabbitmq(rabbitmq_consumer):
    method_frame, header_frame, message = rabbitmq_consumer.get_one_message(
        queue_name=RABBITMQ_TEST_DEFAULT,
        auto_ack=True
    )
    assert method_frame.message_count == 0  # messages left in the queue
    decoded_message = pickle.loads(message)
    assert decoded_message.job_id == "Test_job_id"
    assert decoded_message.processor_name == "ocrd-dummy"
