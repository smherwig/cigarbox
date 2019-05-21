build:
	python setup.py build

install:
	pip install --user .

devinstall:
	pip install -e .

uninstall:
	pip uninstall mbx 

clean:
	rm -rf build

sdist:
	python setup.py sdist

wheel:
	python setup.py bdist_wheel

.PHONEY: build install devinstall uninstall clean sdist wheel

