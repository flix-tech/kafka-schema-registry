# kafka-schema-registry

This library allows you to create topics on Kafka associated with a Confluent schema, and publish messages on them.

It takes care of:
* creating the topic
* publishing the associated schema (or updating an existing one)
* serializing and publishing messages to Kafka

## Usage

```python3
from kafka_schema_registry import prepare_producer

SAMPLE_SCHEMA = {
"type": "record",
"name": "TestType",
"fields" : [
    {"name": "age", "type": "int"},
    {"name": "name", "type": ["null", "string"]}
]
}


producer = prepare_producer(
        ['localhost:9092'],
        f'http://schemaregistry',
        topic_name,
        1,
        1,
        value_schema=SAMPLE_SCHEMA,
)

producer.send(topic_name, {'age': 34})
producer.send(topic_name, {'age': 9000, 'name': 'john'})
```

## Run the test

The test requires Docker in order to start a local Redpanda instance.

* `make start-redpanda` to start the server
* `make test` to configure a virtualenv and run the tests
