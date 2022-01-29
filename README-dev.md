# Technical Documentation
This document provides technical information about various workflows related to updating and editing the schema and documentation site.

## General Requirements

- Python 3.7+
- Node.js 12+ and NPM

## Python Setup
Create a Python 3 (3.7+) virtual environment and install the requirements:

```console
$ python3 -m venv virtualenv
$ source virtualenv/bin/activate
$ pip install -r requirements.txt
```

Then run the utility scripts to parse the schemas:

```console
$ ./util/generate-hugo-content.py -i ./data/iseal-core.csv --clean -d
$ ./util/generate-hugo-content.py -i data/fsc.csv -d
```

## Node.js Setup
To generate the HTML documentation site:

```console
$ cd site
$ npm install
$ npm run build
```
