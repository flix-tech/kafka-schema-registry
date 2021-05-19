import json
import uuid

import pytest
import responses

from kafka_schema_registry import prepare_producer

SAMPLE_SCHEMA = {
  "type": "record",
  "name": "TestType",
  "fields" : [
    {"name": "age", "type": "int"},
    {"name": "name", "type": ["null", "string"]}
  ]
}

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
        f'http://schemaregistry',
        topic_name,
        1,
        1,
        value_schema=SAMPLE_SCHEMA,
    )
    # the message does not match
    with pytest.raises(ValueError) as exc:
        producer.send(topic_name, {'e': 34})
    
    producer.send(topic_name, {'age': 34})
    producer.send(topic_name, {'age': 9000, 'name': 'john'})

