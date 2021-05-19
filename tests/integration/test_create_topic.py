import uuid

import pytest
from kafka.errors import UnknownTopicOrPartitionError

from kafka_schema_registry import create_topic, delete_topic

def test_topic_creation_deletion():
    topic_name = f'test-topic-{uuid.uuid4()}' 
    with pytest.raises(UnknownTopicOrPartitionError):
        delete_topic(['localhost:9092'], topic_name)
    create_topic(['localhost:9092'], topic_name, 1, 1)
    delete_topic(['localhost:9092'], topic_name)
    with pytest.raises(UnknownTopicOrPartitionError):
        delete_topic(['localhost:9092'], topic_name)
