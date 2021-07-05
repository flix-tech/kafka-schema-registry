from setuptools import setup, find_packages


setup(
    name='kafka_schema_registry',

    version='0.0.1',
    description='Kafka and schema registry integration',
    long_description=open('./README.md').read(),
    author='Flixbus',
    url='https://github.com/flix-tech/kafka-schema-registry',

    python_requires='>=3.7',

    packages=find_packages(),

    install_requires=[
        'fastavro',
        'kafka-python',
        'requests',
    ],
    license='MIT',
)
