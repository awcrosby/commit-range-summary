lint:
	@black --diff -l 99 --check *.py
	isort --diff .

fmt:
	black -l 99 *.py
	isort .
