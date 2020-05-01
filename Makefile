pack:
	python3 setup.py sdist bdist_wheel

upload:
	twine upload dist/*

release: clean pack upload

clean:
	rm -rf dist

.PHONY: pack upload clean release