make:
	python -m pip install virtualenv
	virtualenv venv
	source venv/bin/activate;
	pip install --upgrade pip;
	pip install -r ./requirements.txt;
