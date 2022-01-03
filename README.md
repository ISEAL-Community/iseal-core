# ISEAL Core Metadata Set
The ISEAL Core Metadata Set (ISEAL Core) is a set of structured terms and vocabularies that can be used as metadata to describe, share, and reuse different digital resources across the [ISEAL Community](https://www.isealalliance.org/) and broader set of stakeholders. The resources described using the ISEAL Core are those that sustainability systems typically collect, curate, manage, use, publish and archive. They may be datasets, published research, certificates, videos, images, maps, or other organizational documentation.

<p align="center">
  <img width="600" alt="Screenshot of ISEAL Core Metadata Set documentation" src="screenshot.png">
</p>

You can see a user-friendly version of the schema [here](https://alanorth.github.io/iseal-schema/).

## Requirements

- Python 3.7+ (for parsing the schema)
- Node.js 12+ (for generating the HTML documentation site)

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

## TODO

- Repository
  - Update links to final version (from alanorth to iseal GitHub)
  - Add more information and instructions to README.md
- Schema
  - Remove combined "latLong" fields (they can be inferred from the separate fields)
  - Remove controlled vocabularies from the schema CSVs
- Site
  - Change "Suggested element" to "DSpace mapping"?

## License

This project's source code is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0-standalone.html). This project's text and graphics are licensed under the [Creative Commons Attribution Share Alike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/legalcode) license.
