# system python interpreter. used only to create virtual environment
PY = python3
VENV = venv
BIN=$(VENV)/bin


ifeq ($(OS), Windows_NT)
	BIN=$(VENV)/Scripts
	PY=python
endif

all: lint test

$(VENV): requirements.txt requirements-dev.txt setup.py
	$(PY) -m venv $(VENV)
	# required since Python 3.12
	$(BIN)/pip install setuptools
	$(BIN)/pip install --upgrade -r requirements.txt
	$(BIN)/pip install --upgrade -r requirements-dev.txt
	$(BIN)/pip install -e .
	touch $(VENV)


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
test: $(VENV)
	$(BIN)/pytest

.PHONY: lint
lint: $(VENV)
	$(BIN)/flake8

.PHONY: release
release: $(VENV)
	rm -rf dist
	$(BIN)/python setup.py sdist bdist_wheel
	$(BIN)/twine upload dist/*

.PHONY: clean
clean:
	rm -rf build dist *.egg-info
	rm -rf $(VENV)
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete
	# coverage
	rm -rf htmlcov .coverage
