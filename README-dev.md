# Technical Documentation
This document provides technical information about various workflows related to updating and editing the schema and documentation site.

## About This Project

The ISEAL Core Metadata Set is maintained primarily in CSV format. This decision was made to maintain a balance between being human and machine readable. Currently the project consists of:

- The ISEAL Core Metadata Set, which lives in `data/iseal-core.csv`
- The FSC<sup>®</sup> extension, which lives in `data/fsc.csv`

From the CSV we use a series of Python scripts to create the RDF ([TTL](https://en.wikipedia.org/wiki/Turtle_(syntax))) representations of the schema as well as the HTML documentation site. All of this is automated using GitHub Actions (see `.github/workflows`) whenever there is a new commit in the repository.

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