# Technical Documentation
This document provides technical information about various workflows related to updating and editing the schema and documentation site.

## About This Project

The ISEAL Core Metadata Set is maintained primarily in CSV format. This decision was made to maintain a balance between being human and machine readable. Currently the project consists of:

- The ISEAL Core Metadata Set, which lives in `data/iseal-core.csv`
- The FSC<sup>®</sup> extension, which lives in `data/fsc.csv`

From the CSV we use a series of Python scripts to create the RDF ([TTL](https://en.wikipedia.org/wiki/Turtle_(syntax))) representations of the schema as well as the HTML documentation site. All of this is automated using GitHub Actions (see `.github/workflows`) whenever there is a new commit in the repository. You should only need to follow the documentation here if you want to work on the workflow locally or make larger changes. In that case, continue reading...

## Technical Requirements

- Python 3.8+ — to parse the CSV schemas, generate the RDF files, and populate the documentation site content
- Node.js 12+ and NPM — to generate the documentation site HTML

### Python Setup
Create a Python virtual environment and install the requirements:

```console
$ python3 -m venv virtualenv
$ source virtualenv/bin/activate
$ pip install -r requirements.txt
```

Once you have the Python environment set up you will be able to use the utility scripts:

- `./util/generate-hugo-content.py` — to parse the CSV schemas and controlled vocabularies, then populate the documentation site content
- `./util/create-rdf.py` — to parse the CSV schemas and create the RDF (TTL) files

If you have made modifications to the CSV schemas—adding elements, changing descriptions, etc—and you want to test them locally before pushing to GitHub, then you will need to re-run the utility scripts:

```console
$ python ./util/generate-hugo-content.py -i ./data/iseal-core.csv --clean -d
$ python ./util/generate-hugo-content.py -i ./data/fsc.csv -d
$ python ./util/create-rdf.py -i ./data/iseal-core.csv -ns https://iseal-community.github.io/iseal-core#
$ python ./util/create-rdf.py -i ./data/fsc.csv -ns https://iseal-community.github.io/iseal-core/fsc#
```

Assuming these scripts ran without crashing, you can check your `git status` to see if anything was updated and then proceed to regenerating the documentation site HTML.

### Node.js Setup
Install the web tooling and dependencies required to build the site:

```console
$ cd site
$ npm install
```

The Python scripts above only populated the *content* for the documentation site. To regenerate the actual HTML for the documentation site you must run the `npm build` script:

```console
$ npm run build
```

Alternatively, you can view the site locally using the `npm run server` command:

```console
$ npm run server
```

The site will be built in memory and available at: http://localhost:1313/iseal-core/

## Workflows
These are some common, basic workflows:

- Add new metadata element(s) → re-run Python scripts and regenerate documentation site
- Update metadata descriptions → re-run Python scripts and regenerate documentation site
- Update controlled vocabularies → re-run Python scripts and regenerate documentation site

These are advanced workflows:

- Change documentation site layout
  - Requires editing templates in `site/layouts` and regenerating documentation site
- Change documentation site style
  - Requires editing styles in `site/source/scss` and regenerating documentation site
- Add a new schema extension
  - Requires editing Python utility scripts
  - Requires editing styles in `site/source/scss` and regenerating documentation site
  - Requires editing templates in `site/layouts` and regenerating documentation site
