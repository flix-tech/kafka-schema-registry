from io import BytesIO
import copy
import json
import logging
import struct
from typing import List

from fastavro import parse_schema, schemaless_writer
from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
from requests import request

logger = logging.getLogger(__name__)

# the log from python-kafka is absurdly verbose, reduce it
# it logs every single produced event
logging.getLogger('kafka.producer.record_accumulator').setLevel(logging.INFO)
logging.getLogger('kafka.producer.sender').setLevel(logging.INFO)
logging.getLogger('kafka.protocol.parser').setLevel(logging.INFO)
logging.getLogger('kafka.conn').setLevel(logging.INFO)
logging.getLogger('kafka.producer.kafka').setLevel(logging.INFO)


def delete_topic(topic_name: str, **kwargs):
    """Delete a topic from Kafka.

    The topic is deleted synchronously, the function returns when done.
    Notice that Lenses and other tools can take a few minutes to show
    the change.

    Parameters
    ----------
    topic_name : str
        The name of the topic to delete
    """
    admin_config = copy.copy(KafkaAdminClient.DEFAULT_CONFIG)
    for key in admin_config:
        admin_config[key] = kwargs.get(key, admin_config[key])

    admin_client = KafkaAdminClient(**admin_config)
    admin_client.delete_topics([topic_name])


def publish_schemas(
    topic_name: str,
    avro_schema_registry: str,
    value_schema: dict = None,
    key_schema: dict = None,
        ):
    """Publish the schema for a given topic.

    If the schema is already there and identical, the id is simply returned,
    so subsequent calls are idempotent.

    At least one of the schemas must be specified.

    Parameters
    ----------
    topic_name : str
        The name of the topic
    avro_schema_registry : str
        The URL of the schema registry
    value_schema : str
        The value Avro schema as a JSON-encoded string, or None
    key_schema : str
        The key Avro schema as a JSON-encoded string, or None

    Return
    ------
    tuple of int
        The ids of the published schemas as a (key_id, value_id) tuple
    """
    if value_schema is None and key_schema is None:
        raise ValueError('No key nor value schema was given')
    value_schema_id = None
    # API:
    # https://docs.confluent.io/current/schema-registry/develop/api.html
    if value_schema is not None:
        url_value = f'{avro_schema_registry}/subjects/{topic_name}-value/versions' # NOQA
        value_resp = request(
            'POST',
            url_value,
            data=json.dumps({"schema": value_schema}),
            headers={
                'Content-Type': 'application/json'
                }
            )
        if 'id' not in value_resp.json():
            logger.error(f'No id in response: {value_resp.json()}')
        value_schema_id = value_resp.json()['id']

    key_schema_id = None
    if key_schema is not None:
        url_key = f'{avro_schema_registry}/subjects/{topic_name}-key/versions' # NOQA
        key_resp = request(
            'POST',
            url_key,
            data=json.dumps({"schema": key_schema}),
            headers={
                'Content-Type': 'application/json'
                }
            )
        key_schema_id = key_resp.json()['id']

    return (key_schema_id, value_schema_id)


def create_topic(
    bootstrap_servers: List[str],
    topic_name: str,
    num_partitions: int,
    replication_factor: int,
    topic_config: dict = None,
    **kwargs,
):
    """Create a topic with the given number of partitions.

    If the topic already exists, nothing happens.

    Parameters
    ----------
    bootstrap_servers : list of str
        The list of Kafka servers
    topic_name : str
        The name of the topic
    num_partitions : int
        The number of partitions
    replication_factor : int
        The replication factor for this topic
    """
    admin_config = copy.copy(KafkaAdminClient.DEFAULT_CONFIG)
    admin_config['bootstrap_servers'] = bootstrap_servers
    # Resets configurations passed by user
    for key in admin_config:
        admin_config[key] = kwargs.get(key, admin_config[key])

    try:
        # WORKAROUND: see https://github.com/dpkp/kafka-python/pull/2048
        # when done remove this try catch
        admin_client = KafkaAdminClient(**admin_config)
    except NoBrokersAvailable:
        logger.warning('Error instantiating the client, should be solved by '
                       'https://github.com/dpkp/kafka-python/pull/2048')
        return
    try:
        admin_client.create_topics([
            NewTopic(
                name=topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
                topic_configs=topic_config,
                )
        ])
        logger.info(f'Topic created: {topic_name}')
    except TopicAlreadyExistsError:
        logger.info(f'Not recreating existing topic {topic_name}')


def prepare_producer(
    bootstrap_servers: List[str],
    avro_schema_registry: str,
    topic_name: str,
    num_partitions: int,
    replication_factor: int,
    value_schema: dict = None,
    key_schema: dict = None,
    topic_config: dict = None,
    **kwargs,
        ):
    """Ensure the topic and the schema exist and returns a producer for it.

    The function is idempotent by design, so can be called multiple times
    and it will use the schema and topic if present or create them
    the first time.

    Parameters
    ----------
    bootstrap_servers : list of str
        The list of Kafka servers
    avro_schema_registry : str
        The URL of the schema registry
    topic_name : str
        name of the topic to write to
    num_partitions : int
        The number of partitions
    replication_factor : int
        The replication factor for this topic
    value_schema : dict, optional
        The value schema, or None
    key_schema_path : str, optional
        The key schema, or None
    Returns
    -------
    KafkaProducer
        A producer ready to be used e.g. by calling send()
    """
    if value_schema is None and key_schema is None:
        raise ValueError('No key nor value schema was given')

    # Check for valid key, value pairs
    invalid_key = set(kwargs).difference(set(KafkaProducer.DEFAULT_CONFIG)) \
                             .difference(set(KafkaAdminClient.DEFAULT_CONFIG))
    assert not invalid_key, f'Unrecognized configs: {invalid_key}'

    create_topic(
        bootstrap_servers,
        topic_name,
        num_partitions,
        replication_factor,
        topic_config,
        **kwargs,
    )

    parsed_value_schema = None
    default_values = {}
    if value_schema is not None:
        parsed_value_schema = parse_schema(value_schema)
        # store the default values to remove
        # the values from the messages when identical
        default_values = {
            field['name']: field['default']
            for field in parsed_value_schema['fields']
            if 'default' in field
        }

    parsed_key_schema = None
    default_keys = {}
    if key_schema is not None:
        parsed_key_schema = parse_schema(key_schema)
        # store the default values to remove
        # the values from the messages when identical
        default_keys = {
            field['name']: field['default']
            for field in parsed_key_schema['fields']
            if 'default' in field
        }

    key_schema_id, value_schema_id = publish_schemas(
        topic_name,
        avro_schema_registry,
        value_schema=(
            json.dumps(value_schema)
            if value_schema is not None else None),
        key_schema=(
            json.dumps(key_schema)
            if key_schema is not None else None),
    )

    def avro_record_value_writer(
        record,
        schema=parsed_value_schema,
        value_schema_id=value_schema_id,
        default_values=default_values,
            ):
        buf = BytesIO()
        buf.write(struct.pack('>bI', 0, value_schema_id))
        for k, v in default_values.items():
            if record.get(k) == v and v is not None:
                del record[k]
        schemaless_writer(buf, schema, record)
        return buf.getvalue()

    def avro_record_key_writer(
        record,
        schema=parsed_key_schema,
        key_schema_id=key_schema_id,
        default_keys=default_keys,
            ):
        buf = BytesIO()
        buf.write(struct.pack('>bI', 0, key_schema_id))
        for k, v in default_keys.items():
            if record.get(k) == v and v is not None:
                del record[k]
        schemaless_writer(buf, schema, record)
        return buf.getvalue()

    producer_config = copy.copy(KafkaProducer.DEFAULT_CONFIG)
    # Default configurations
    # bootstrap servers
    producer_config['bootstrap_servers'] = bootstrap_servers
    # notice that the serializer are called even with None, hence the check
    producer_config['value_serializer'] = (
            avro_record_value_writer if value_schema else None)
    producer_config['key_serializer'] = (
            avro_record_key_writer if key_schema else None)
    # compression, note that is done on a whole batch
    producer_config['compression_type'] = 'gzip'
    # time to get an initial answer from the brokers when initializing
    # the default is 2 seconds and in case of slow network breaks the app
    producer_config['api_version_auto_timeout_ms'] = 10 * 1000
    # accumulate messages for these ms before sending them
    producer_config['linger_ms'] = 1000

    # Resets configurations passed by user
    for key in producer_config:
        producer_config[key] = kwargs.get(key, producer_config[key])

    return KafkaProducer(**producer_config)
