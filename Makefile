.PHONY: test test-unit test-integration test-all

test: test-all

test-all:
	python3 -m pytest tests/ -v -o "addopts="

test-unit:
	python3 -m pytest tests/ -v

test-pintegration:
	python3 -m pytest tests/ -m integration -v
