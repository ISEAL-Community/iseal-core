# Technical Documentation
This document provides technical information about various workflows related to updating and editing the schema and documentation site.

## About This Project

The ISEAL Core Metadata Set is maintained primarily in CSV format. This decision was made to maintain a balance between being human and machine readable. Currently the project consists of:

- The ISEAL Core Metadata Set, which lives in `data/iseal-core.csv`
- The FSC<sup>®</sup> extension, which lives in `data/fsc.csv`

From the CSV we use a series of Python scripts to create the RDF ([TTL](https://en.wikipedia.org/wiki/Turtle_(syntax))) representations of the schema as well as the HTML documentation site. All of this is automated using GitHub Actions (see `.github/workflows`) whenever there is a new commit in the repository. You should only need to follow the documentation here if you want to work on the workflow locally or make larger changes. In that case, continue reading...

## Technical Requirements

- Python 3.8+ — to parse the CSV schema and generate the RDF and documentation site
- Node.js 12+ and NPM — to generate the documentation site

### Python Setup
Create a Python virtual environment and install the requirements:

```console
$ python3 -m venv virtualenv
$ source virtualenv/bin/activate
$ pip install -r requirements.txt
```

Then run the utility scripts to parse the schemas:

```console
$ python ./util/generate-hugo-content.py -i ./data/iseal-core.csv --clean -d
$ python ./util/generate-hugo-content.py -i data/fsc.csv -d
```

### Node.js Setup
To generate the HTML documentation site:

```console
$ cd site
$ npm install
$ npm run build
```
