#!/usr/bin/env python3
#
# create-schema-dspace.py 0.0.1
#
# SPDX-License-Identifier: GPL-3.0-only
#
# ---
#
# A quick and dirty script to read schema fields from a CSV file and create them
# them in the DSpace metadata registry using the REST API. Specify an email and
# for a DSpace user with administrator privileges when running:
#
#   $ ./util/create-schema-dspace.py -e me@example.com -p 'fuu!'
#
# You can optionally specify the URL of a DSpace REST application (default is to
# use http://localhost:8080/rest).
#
# This script is written for Python 3 and requires several modules that you can
# install with pip (I recommend setting up a Python virtual environment first):
#
#   $ pip install requests pandas
#

import argparse
import signal
import sys

import pandas as pd
import requests


def signal_handler(signal, frame):
    sys.exit(1)


# Try to log in, for example:
#
#   $ http -f POST http://localhost:8080/rest/login email=aorth@fuuu.com password='fuuuuuu'
#
def login(user, password):
    request_url = rest_login_endpoint
    headers = {"user-agent": rest_user_agent}
    data = {"email": args.user, "password": args.password}

    print(f"Logging in...")

    try:
        request = requests.post(rest_login_endpoint, headers=headers, data=data)
    except requests.ConnectionError:
        sys.stderr.write(f" Could not connect to REST API: {args.request_url}\n")

        exit(1)

    if request.status_code != requests.codes.ok:
        sys.stderr.write(f" Login failed.\n")

        exit(1)

    return request.cookies["JSESSIONID"]


# Check the authentication status of the specified JSESSIONID.
def check_session(sessionid):
    request_url = rest_status_endpoint
    headers = {"user-agent": rest_user_agent, "Accept": "application/json"}
    cookies = {"JSESSIONID": sessionid}

    print(f"Checking session status...")

    try:
        request = requests.get(request_url, headers=headers, cookies=cookies)
    except requests.ConnectionError:
        sys.stderr.write(f" Could not connect to REST API: {args.request_url}\n")

        exit(1)

    if request.status_code == requests.codes.ok:
        if not request.json()["authenticated"]:
            sys.stderr.write(f" Session expired: {sessionid}\n")

            exit(1)
    else:
        sys.stderr.write(f" Error checking session status.\n")

        exit(1)


# Create a new schema by passing a Schema Object, for example:
#
#  $ http POST http://localhost:8080/rest/registries/schema Cookie:JSESSIONID=549756EB08169F17697A56A7D56901B3 < schema.json
#
# See: https://wiki.lyrasis.org/display/DSDOC6x/REST+API#RESTAPI-SchemaObject
def create_schema(schema):
    request_url = rest_schema_registry_endpoint
    headers = {"user-agent": rest_user_agent}
    cookies = {"JSESSIONID": session}

    print(f" Attempting to create schema: {schema['prefix']}")

    try:
        request = requests.post(
            request_url, headers=headers, json=schema, cookies=cookies
        )
    except requests.ConnectionError:
        sys.stderr.write(f"  Could not connect to REST API: {args.request_url}\n")

        exit(1)

    # Check the status
    if request.status_code == requests.codes.ok:
        return True
    # DSpace responds with HTTP 500 if the schema exists
    elif request.status_code == requests.codes.internal_server_error:
        print(f"  Schema already exists: {schema['prefix']}")

        return False
    # DSpace responds with HTTP 415 if we POST bad data like a malformed JSON
    # or a request without headers, etc.
    elif request.status_code == requests.codes.unsupported_media_type:
        sys.stderr.write(f"  Could not create schema: {schema['prefix']}\n")
        sys.stderr.write(f"  HTTP error code: {request.status_code}\n")

        return False
    # Unknown error
    else:
        sys.stderr.write(f"  Could not create schema: {schema['prefix']}\n")
        sys.stderr.write(f"  HTTP error code: {request.status_code}\n")

        return False


# Create a new metadata field by passing a MetadataField Object, for example:
#
#  $ http POST http://localhost:8080/rest/registries/schema/fuuu/metadata-fields \
#         Cookie:JSESSIONID=549756EB08169F17697A56A7D56901B3 < field.json
#
# See: https://wiki.lyrasis.org/display/DSDOC6x/REST+API#RESTAPI-MetadataFieldObject
def create_field(schema_prefix, field):
    request_url = f"{rest_schema_registry_endpoint}/{schema_prefix}/metadata-fields"
    headers = {"user-agent": rest_user_agent}
    cookies = {"JSESSIONID": session}

    print(f"  Attempting to create field: {field['name']}")

    try:
        request = requests.post(
            request_url,
            headers=headers,
            json=field,
            cookies=cookies,
        )
    except requests.ConnectionError:
        sys.stderr.write(f"   Could not connect to REST API: {args.request_url}\n")

        exit(1)

    # Check the status
    if request.status_code == requests.codes.ok:
        return True
    # DSpace responds with HTTP 500 if the field exists
    elif request.status_code == requests.codes.internal_server_error:
        print(f"  Field already exists: {field['name']}")

        return False
    # DSpace responds with HTTP 415 if we POST bad data like a malformed JSON
    # or a request without headers, etc.
    elif request.status_code == requests.codes.unsupported_media_type:
        sys.stderr.write(f"  Could not create field: {field['name']}.\n")
        sys.stderr.write(f"  HTTP error code: {request.status_code}\n")
        sys.stderr.write("\n")

        return False
    # DSpace responds with HTTP 404 if the schema does not exist
    elif request.status_code == requests.codes.not_found:
        sys.stderr.write(
            f"  Could not create field: {field['name']} (parent schema does not exist).\n"
        )

        return False
    # Unknown error
    else:
        sys.stderr.write(f"  Could not create field: {field['name']}\n")
        sys.stderr.write(f"  HTTP error code: {request.status_code}\n")

        return False


def parse_fields(schema_df):
    # Iterate over all rows (the "index, row" syntax allows us to access column
    # headings in each row, which isn't possible if we just do row).
    for index, row in schema_df.iterrows():
        dspace_field_name = row["dspace field name"]
        # Extract the prefix from the field name, ie is.link.url
        dspace_field_prefix = dspace_field_name.split(".")[0]
        element_name = row["element name"]

        # Make sure we only try to create fields in IS and FSC schemas for now.
        # In the future we may create fields for other schema extensions, but
        # we don't want to create dcterms fields, for example.
        if "is" in dspace_field_prefix or "fsc" in dspace_field_prefix:
            # Extract the element, ie "link" in is.link.url
            dspace_field_element = dspace_field_name.split(".")[1]

            try:
                # Extract the qualifier, ie "url" in is.link.url, if it exists
                dspace_field_qualifier = dspace_field_name.split(".")[2]
            except IndexError:
                dspace_field_qualifier = None

            # Create a list of tuples with the metadata field components
            field_components = [
                ("element", dspace_field_element),
                ("qualifier", dspace_field_qualifier),
                ("name", row["dspace field name"]),
                ("description", element_name),
            ]

            # Create a dict from the list of tuples аbove. We can pass the dict
            # to requests directly and it will be converted to JSON.
            field = dict(field_components)

            if create_field(dspace_field_prefix, field):
                print(f"   Created field: {dspace_field_name}")


parser = argparse.ArgumentParser(
    description="Create ISEAL and FSC schemas in a DSpace 6.x repository."
)
parser.add_argument("-d", "--debug", help="Print debug messages.", action="store_true")
parser.add_argument(
    "-u",
    "--rest-url",
    help="URL of the DSpace 6.x REST API.",
    default="http://localhost:8080/rest",
)
parser.add_argument("-e", "--user", help="Email of administrator user.")
parser.add_argument("-p", "--password", help="Email of administrator user.")
parser.add_argument(
    "-s", "--jsessionid", help="JESSIONID, if previously authenticated."
)
args = parser.parse_args()

# DSpace 6.x REST API base URL and endpoints
rest_base_url = args.rest_url
rest_login_endpoint = f"{rest_base_url}/login"
rest_status_endpoint = f"{rest_base_url}/status"
rest_schema_registry_endpoint = f"{rest_base_url}/registries/schema"
rest_user_agent = "Alan Test Python Requests Bot"
session = args.jsessionid

# set the signal handler for SIGINT (^C)
signal.signal(signal.SIGINT, signal_handler)

# Try to login if no session was passed
if not args.jsessionid:
    session = login(args.user, args.password)
else:
    check_session(args.jsessionid)

if args.debug:
    sys.stderr.write(f" Logged in, using JSESSIONID: {session}\n")

print("\nCreating schemas...")

iseal_schema = {
    "namespace": "https://iseal-community.github.io/iseal-core",
    "prefix": "is",
}
fsc_schema = {
    "namespace": "https://iseal-community.github.io/iseal-core/fsc",
    "prefix": "fsc",
}

if create_schema(iseal_schema):
    print("  Created ISEAL Core schema")

if create_schema(fsc_schema):
    print("  Created FSC schema")

print("\nCreating fields...")

for file in ["data/iseal-core.csv", "data/fsc.csv"]:
    if args.debug:
        sys.stderr.write(f" Opening {file}\n")

    try:
        df = pd.read_csv(file, usecols=["dspace field name", "element name"])
        parse_fields(df)
    except FileNotFoundError:
        sys.stderr.write(f"  Could not open {file}\n")
