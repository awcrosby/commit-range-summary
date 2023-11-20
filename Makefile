lint:  # Display short output only if fails linter
	-@isort --multi-line 3 --trailing-comma . --check --quiet
	-@ruff check .
	-@ruff format . --line-length 99 --check --quiet
	-@mypy . --no-error-summary

format-diff:  # Display changes formatter would make
	-isort --multi-line 3 --trailing-comma . --diff
	-ruff check .
	-ruff format . --line-length 99 --diff

format:  # Format code
	-isort --multi-line 3 --trailing-comma .
	-ruff check . --fix
	-ruff format . --line-length 99

test:
	pytest --cov=. --cov-branch test_*.py

test/annotate:
	pytest --cov=. --cov-branch test_*.py --cov-report annotate

test/annotate/clean:
	find . -type f -name '*,cover' -delete
