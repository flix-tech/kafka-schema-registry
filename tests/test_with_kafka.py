import json
import uuid
import socket

import pytest
import responses
from kafka.errors import UnknownTopicOrPartitionError

from kafka_schema_registry import publish_schemas
from kafka_schema_registry import prepare_producer
from kafka_schema_registry import create_topic, delete_topic


def has_kafka():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 9092))
    sock.close()
    return True if result == 0 else False


SAMPLE_SCHEMA = {
  "type": "record",
  "name": "TestType",
  "fields": [
    {"name": "age", "type": "int"},
    {"name": "name", "type": ["null", "string"]}
  ]
}


def test_check_schema_presence():
    with pytest.raises(ValueError) as exc:
        publish_schemas(
            'not-really-used',
            'http://schemaregistry',
        )
    assert str(exc.value) == 'No key nor value schema was given'


@responses.activate
def test_publish_value_schema():
    topic_name = f'test-topic-{uuid.uuid4()}'
    schema = dict(bla=42)
    responses.add(
        responses.POST,
        f'http://schemaregistry/subjects/{topic_name}-value/versions',
        json=dict(id=2),
        status=200)

    (k_id, v_id) = publish_schemas(
        topic_name,
        'http://schemaregistry',
        value_schema=schema,
    )
    assert json.loads(responses.calls[0].request.body) == dict(schema=schema)
    assert (k_id, v_id) == (None, 2)


@responses.activate
def test_publish_key_schema():
    topic_name = f'test-topic-{uuid.uuid4()}'
    schema = dict(bla=42)
    responses.add(
        responses.POST,
        f'http://schemaregistry/subjects/{topic_name}-key/versions',
        json=dict(id=2),
        status=200)

    (k_id, v_id) = publish_schemas(
        topic_name,
        'http://schemaregistry',
        key_schema=schema,
    )
    assert json.loads(responses.calls[0].request.body) == dict(schema=schema)
    assert (k_id, v_id) == (2, None)


@pytest.mark.skipif(not has_kafka(), reason="No Kafka Cluster running")
@responses.activate
def test_publish_messages():
    topic_name = f'test-topic-{uuid.uuid4()}'
    responses.add(
        responses.POST,
        f'http://schemaregistry/subjects/{topic_name}-value/versions',
        json=dict(id=2),
        status=200)
    producer = prepare_producer(
        ['localhost:9092'],
        'http://schemaregistry',
        topic_name,
        1,
        1,
        value_schema=SAMPLE_SCHEMA,
    )
    # the message does not match
    with pytest.raises(ValueError):
        producer.send(topic_name, {'e': 34})

    producer.send(topic_name, {'age': 34})
    producer.send(topic_name, {'age': 9000, 'name': 'john'})


@pytest.mark.skipif(not has_kafka(), reason="No Kafka Cluster running")
def test_topic_creation_deletion():
    topic_name = f'test-topic-{uuid.uuid4()}'
    with pytest.raises(UnknownTopicOrPartitionError):
        delete_topic(topic_name, bootstrap_servers=['localhost:9092'])
    create_topic(['localhost:9092'], topic_name, 1, 1)
    delete_topic(topic_name, bootstrap_servers=['localhost:9092'])
    with pytest.raises(UnknownTopicOrPartitionError):
        delete_topic(topic_name, bootstrap_servers=['localhost:9092'])


@pytest.mark.skipif(not has_kafka(), reason="No Kafka Cluster running")
@responses.activate
def test_correct_config_params():
    """ prepare_producer() uses two API's:
         1) KafkaAdminClient -> Creates topics
         2) KafkaProducer -> sends events to kafka topic
     Both the above API's config params are not equivalent, this
     test makes sure correct configs are passed to the respective API's
     without raising any errors.
    """

    request_timeout_ms = 30000                      # Common config param
    batch_size = 16384                              # Producer specific config
    topic_config = {'cleanup.policy': 'compact'}    # Topic specific config
    topic_name = f'test-topic-{uuid.uuid4()}'
    responses.add(
        responses.POST,
        f'http://schemaregistry/subjects/{topic_name}-value/versions',
        json=dict(id=2),
        status=200)
    producer = prepare_producer(
        ['localhost:9092'],
        'http://schemaregistry',
        topic_name,
        1,
        1,
        value_schema=SAMPLE_SCHEMA,
        request_timeout_ms=request_timeout_ms,
        batch_size=batch_size,
        topic_config=topic_config,
        )

    producer.send(topic_name, {'age': 34})
    producer.send(topic_name, {'age': 9000, 'name': 'john'})


@pytest.mark.skipif(not has_kafka(), reason="No Kafka Cluster running")
@responses.activate
def test_incorrect_config_params():
    """ If invalid config parameters are passed then AssertionError is raised.
        Currently there is no way to check the valid topic configurations,
        hence skipped and depends on the user to provide valid configs.
    """
    invalid_param = 'dummy'
    topic_name = f'test-topic-{uuid.uuid4()}'
    responses.add(
        responses.POST,
        f'http://schemaregistry/subjects/{topic_name}-value/versions',
        json=dict(id=2),
        status=200)
    with pytest.raises(AssertionError):
        prepare_producer(
            ['localhost:9092'],
            'http://schemaregistry',
            topic_name,
            1,
            1,
            value_schema=SAMPLE_SCHEMA,
            invalid_param=invalid_param
            )
