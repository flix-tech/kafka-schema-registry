# Changelog

## [Unreleased] -- YYYY-MM-DD

## [0.2.0] -- 2024-12-09

* Update dependencies
* Show the raw response in case of JSON errors from th registry


## [0.1.2] -- 2022-07-13

* Pass per-topic config (used when created a topic) as a dedicated variable, not as part of the Client configs

## [0.1.1] -- 2022-07-12

 * Fixed API's config params
prepare_producer() uses two API's:
	 1. KafkaAdminClient -> creates topics
	 2. KafkaProducer -> sends events to kafka topic
Both the above API's config parameters are not equivalent, due to this it was not possible to set parameters which are API specific and raises (Unrecognized configs) error. This change makes sure correct configs are passed to the respective API's.

## [0.1.0] -- 2022-07-12

* Added Python 3.10 to test suite

## [0.0.4] -- 2022-01-28

* Propagate extra arguments to the Kafka library (e.g. for authentication)

## [0.0.3] -- 2021-07-06

* Fixed package name

## [0.0.2] -- 2021-07-06

* Dummy release to test gh-actions to pypi

## [0.0.1] -- 2021-07-05

* Initial Release -- you probably should not use this at this point.
