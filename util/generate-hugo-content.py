#!/usr/bin/env python3
#
# generate-hugo-content.py v0.0.1
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
        # Split the element name on " - " because the category is duplicated
        # here, but in a format that is more difficult to use than the "idss
        # module category" field. I will # encourage Peter to modify this
        # field so it is less descriptive because that's what the "idss module
        # category" field does (and more consistently).
        if " - " in row["element name"]:
            # We only want the specific element name, not the category, ie:
            #
            #   [Category]  [Element]
            #   FSC audit - sampling system
            element_name = row["element name"].split(" - ")[1]
        else:
            element_name = row["element name"]

        # Make sure element name is URL friendly because we need to use it in
        # the file system and in the URL.
        #
        # Replace two or more whitespaces with one
        element_name = re.sub(r"\s{2,}", " ", element_name)
        # Replace unnecessary stuff in some element names (I should tell Peter
        # that these belong in the description)
        element_name = re.sub(r"\s?\(\w+\)", "", element_name)
        # Remove commas and question marks
        element_name = re.sub(r"[,?]", "", element_name)
        # Replace ": " with a dash (as in "Evaluation: ")
        element_name = element_name.replace(": ", "-")
        # Replace " / " with a dash (as in "biome / zone")
        element_name = element_name.replace(" / ", "-")
        # Replace whitespace, colons, and slashes with dashes
        element_name = re.sub(r"[\s/]", "-", element_name)
        # Lower case it
        element_name = element_name.lower()
        # Strip just in case
        element_name = element_name.strip()

        # For example Assurance, Certification, Core, Impact, etc
        module = row["idss schema module"].capitalize()
        # For example Certifying Body, FSC audit, Certificate, etc
        cluster = row["idss element cluster"].capitalize()

        # Generate a URL-safe version of the element name, though we need to
        # think about what field we want to use here.
        element_name_safe = cluster.replace(" ", "-").lower() + "-" + element_name

        print(f"element name: {element_name_safe}")

        # Create output directory for term using the URL-safe version
        outputDirectory = f"site/content/terms/{element_name_safe}"
        os.makedirs(outputDirectory, mode=0o755, exist_ok=True)

        if args.debug:
            print(f"Created terms directory: site/content/terms/{element_name_safe}")

        # Take the element description as is, but remove quotes
        element_description = row["element description"].replace("'", "")

        # Take the element guidance as is
        if row["element guidance"]:
            comment = row["element guidance"]
        else:
            comment = False

        example = row["element link for more information"]

        # How to use these in the HTML, slightly overlapping?
        cardinality = row["element options"].capitalize()
        prop_type = row["element type"].capitalize()

        if row["element controlled values or terms"]:
            controlled_vocab = True

            exportVocabulary(
                row["element controlled values or terms"], element_name_safe
            )
        else:
            controlled_vocab = False

        if row["mandatory?"] == "MANDATORY":
            required = True
        else:
            required = False

        if row["dspace field name"] is not None and row["dspace field name"] != "":
            dspace_field_name = row["dspace field name"]
        else:
            dspace_field_name = False

        # Combine element type and options into a "policy" of sorts and convert
        # them to sentence case because they are ALL CAPS in the Excel. We don't
        # need to do any checks because these fields should always exist.
        policy = f'{row["element type"].capitalize()}. {row["element options"].capitalize()}.'

        if args.debug:
            print(f"Processed: {row['element name']}")

        # Create an empty list with lines we'll write to the term's index.md in
        # TOML frontmatter format for Hugo.
        indexLines = []
        indexLines.append("---\n")
        # Use the full title for now (even though it's ugly). Better to fix the
        # schema spreadsheet than try to process the title here.
        indexLines.append("title: '" + row["element name"] + "'\n")
        if dspace_field_name:
            indexLines.append(f"field: '{dspace_field_name}'\n")
        indexLines.append(f"slug: '{element_name_safe}'\n")
        if element_description:
            indexLines.append(f"description: '{element_description}'\n")
        if comment:
            indexLines.append(f"comment: '{comment}'\n")
        indexLines.append(f"required: {required}\n")
        if controlled_vocab:
            indexLines.append(f"vocabulary: '{element_name_safe}.txt'\n")
        if module:
            indexLines.append(f"module: '{module}'\n")
        if cluster:
            indexLines.append(f"cluster: '{cluster}'\n")
        indexLines.append(f"policy: '{policy}'\n")
        ## TODO: use some real date...?
        # indexLines.append(f"date: '2019-05-04T00:00:00+00:00'\n")
        indexLines.append("---")

        with open(f"site/content/terms/{element_name_safe}/index.md", "w") as f:
            f.writelines(indexLines)


def exportVocabulary(vocabulary: str, element_name_safe: str):
    # Create an empty list where we'll add all the values (we don't need to do
    # it this way, but using a list allows us to de-duplicate the values).
    controlledVocabularyLines = []
    for value in vocabulary.split("||"):
        if value not in controlledVocabularyLines:
            controlledVocabularyLines.append(value)

    with open(
        f"site/content/terms/{element_name_safe}/{element_name_safe}.txt", "w"
    ) as f:
        for value in controlledVocabularyLines:
            f.write(f"{value}\n")

    if args.debug:
        print(f"Exported controlled vocabulary: {element_name_safe}")


parser = argparse.ArgumentParser(
    description="Parse an ISEAL schema Excel file to produce documentation about metadata requirements."
)
parser.add_argument(
    "--clean",
    help="Clean output directory before building.",
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
    help="Path to schema fields file (idss_schema_fields.xlsx).",
    required=True,
    type=argparse.FileType("r"),
)
args = parser.parse_args()

if args.clean:
    if args.debug:
        print(f"Cleaning terms output directory")

    rmtree("site/content/terms", ignore_errors=True)

if args.debug:
    print(f"Creating terms output directory")
# Make sure content directory exists. This is where we will deposit all the term
# metadata and controlled vocabularies for Hugo to process.
os.makedirs("site/content/terms", mode=0o755, exist_ok=True)

if args.debug:
    print(f"Opening {args.input_file.name}")

df = pd.read_excel(args.input_file.name)
# Added inplace=True
df.dropna(how="all", axis=1, inplace=True)
df.fillna("", inplace=True)

parseSchema(df)
