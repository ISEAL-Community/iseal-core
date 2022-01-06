#!/usr/bin/env python3
#
# export-controlled-vocabularies.py v0.0.1
#
# This is a legacy script used to export the controlled vocabularies from a CSV
# file. Originally we were embedding the controlled vocabularies directly inside
# the CSV, but we eventually decided that this was unwieldy and error prone.
#
# SPDX-License-Identifier: GPL-3.0-only

import argparse
import os
import re
import sys
from shutil import rmtree

import pandas as pd


def parseSchema(schema_df):
    # Iterate over all rows (the "index, row" syntax allows us to access column
    # headings in each row, which isn't possible if we just do row).
    for index, row in schema_df.iterrows():

        if row["dspace field name"] is not None and row["dspace field name"] != "":
            dspace_field_name = row["dspace field name"]
        else:
            dspace_field_name = False

        # Generate a "safe" version of the element name for use in URLs and
        # files by using the DSpace field name with dots replaced by dashes.
        element_name_safe = dspace_field_name.replace(".", "-").lower()

        print(f"element name: {element_name_safe}")

        # Export controlled vocabularies from CSV file if they exist
        if row["element controlled values or terms"]:
            exportVocabulary(
                row["element controlled values or terms"], element_name_safe
            )


def exportVocabulary(vocabulary: str, element_name_safe: str):
    # Create an empty list where we'll add all the values (we don't need to do
    # it this way, but using a list allows us to de-duplicate the values).
    controlledVocabularyLines = []
    for value in vocabulary.split("||"):
        if value not in controlledVocabularyLines:
            controlledVocabularyLines.append(value)

    with open(f"data/controlled-vocabularies/{element_name_safe}.txt", "w") as f:
        for value in controlledVocabularyLines:
            f.write(f"{value}\n")

    if args.debug:
        print(f"Exported controlled vocabulary: {element_name_safe}")


parser = argparse.ArgumentParser(
    description="Parse an ISEAL schema CSV file to extract embedded controlled vocabularies."
)
parser.add_argument(
    "--clean",
    help="Clean controlled vocabularies directory before exporting.",
    action="store_true",
)
parser.add_argument(
    "-d",
    "--debug",
    help="Print debug messages.",
    action="store_true",
)
parser.add_argument(
    "-i",
    "--input-file",
    help="Path to schema fields file (ie, iseal-core.csv).",
    required=True,
    type=argparse.FileType("r"),
)
args = parser.parse_args()

if args.clean:
    if args.debug:
        print(f"Cleaning controlled vocabularies directory")

    rmtree("data/controlled-vocabularies", ignore_errors=True)

if args.debug:
    print(f"Creating controlled vocabularies directory")

# Make sure controlled vocabularies directory exists.
# metadata and controlled vocabularies for Hugo to process.
os.makedirs("data/controlled-vocabularies", mode=0o755, exist_ok=True)

if args.debug:
    print(f"Opening {args.input_file.name}")

df = pd.read_csv(args.input_file.name)
df.dropna(how="all", axis=1, inplace=True)
df.fillna("", inplace=True)

parseSchema(df)
