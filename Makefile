.PHONY: install run lint format typecheck test ci clean

install:
	pip install -r requirements-dev.txt

run:
	streamlit run app.py

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy --python-version 3.12 app.py etl ai ui tests

test:
	pytest --cov=etl --cov=ai --cov=ui --junitxml=artifacts/junit.xml

ci:
	ruff check .
	ruff format --check .
	mypy --python-version 3.12 app.py etl ai ui tests
	pytest --cov=etl --cov=ai --cov=ui --junitxml=artifacts/junit.xml

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov artifacts build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
