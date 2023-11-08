lint:
	@black --diff -l 99 --check *.py
	isort --diff --multi-line 3 --trailing-comma .

fmt:
	black -l 99 *.py
	isort --multi-line 3 --trailing-comma .
