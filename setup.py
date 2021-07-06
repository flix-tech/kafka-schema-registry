from setuptools import setup

meta = {}
exec(open('./kafka_schema_registry/version.py').read(), meta)
meta['long_description'] = open('./README.md').read()


setup(
    name='kafka-schema-registry',
    version=meta['__VERSION__'],
    description='Kafka and schema registry integration',
    long_description=meta['long_description'],
    long_description_content_type='text/markdown',
    keywords='kafka schema-registry',
    author='FlixTech',
    author_email="open-source@flixbus.com",
    url='https://github.com/flix-tech/kafka-schema-registry',
    project_urls={
        "Changelog": "https://github.com/flix-tech/kafka-schema-registry/blob/master/CHANGELOG.md",  # noqa
        "Source": 'https://github.com/flix-tech/kafka-schema-registry',
    },
    python_requires='>=3.7',
    install_requires=[
        'fastavro',
        'kafka-python',
        'requests',
    ],
    packages=['kafka_schema_registry'],
    license='MIT',
)
