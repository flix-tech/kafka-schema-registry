
.PHONY: start-redpanda
start-redpanda:
	docker run --name=redpanda-1 --rm \
		-p 9092:9092 \
		vectorized/redpanda:latest \
		start \
		--overprovisioned \
		--smp 1  \
		--memory 128M \
		--reserve-memory 0M \
		--node-id 0 \
		--check=false

.PHONY: test
test:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pytest --cov=kafka_schema_registry --cov-report html
