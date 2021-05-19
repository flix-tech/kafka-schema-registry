import json
import uuid

import pytest
import responses

from kafka_schema_registry import publish_schemas

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