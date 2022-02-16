#!/usr/bin/env python
# coding: utf-8

import json
import os
import re
import argparse
import sys


import pandas as pd
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import DC, DCTERMS, OWL, RDF, RDFS, SKOS, XSD


def make_rdf(file, ns):
    g = Graph()

    ##namespace
    # NS = "https://iseal-community.github.io/iseal-core#"
    NS = ns
    ## create ontology
    iseal = URIRef(NS)
    g.add((iseal, RDF.type, OWL.Ontology))
    df = pd.read_csv(file)
    df.dropna(how="all", axis=1)
    df.fillna("", inplace=True)

    for index, row in df.iterrows():
        element_name = row["element name"]
        element_description = row["element description"]
        comment = row["element guidance"]
        example = row["element link for more information"]
        cardinality = row["element options"]
        prop_type = row["element type"]
        # controlled_vocab = row["element controlled values or terms"]
        module = row["idss element cluster"]
        module_cat = ""
        try:  ## for extensions
            module_cat = row["idss schema module"]
        except:
            module_cat_name = [col for col in df.columns if "module" in col][0]
            module_cat = row[module_cat_name]
        dc = row["element link for dublin core attributes"]
        dspace = row["dspace field name"]

        ##module
        moduleUri = URIRef(NS + module)
        if not (None, SKOS.prefLabel, Literal(module)) in g:
            ##create module as skos concept
            g.add((moduleUri, RDF.type, OWL.Class))  ## SKOS.Concept
            g.add((moduleUri, SKOS.prefLabel, Literal(module)))

        conceptUri = URIRef(NS + module_cat.replace(" ", "_"))
        if not (None, SKOS.prefLabel, Literal(module_cat)) in g:
            ##create concept as skos concept
            g.add((conceptUri, RDF.type, OWL.Class))  ## SKOS.Concept
            g.add((conceptUri, SKOS.prefLabel, Literal(module_cat)))
            g.add((conceptUri, RDFS.subClassOf, moduleUri))

        ## create properties
        elementURI = URIRef(NS + dspace.replace(".", "-").lower())
        if prop_type == "CONTROLLED VALUE":  ## object property
            g.add((elementURI, SKOS.prefLabel, Literal(element_name)))
            g.add((elementURI, RDF.type, OWL.ObjectProperty))
            g.add((elementURI, OWL.domain, conceptUri))
            ## add suproperty link
            if dc:
                dct = dc.split(":")[1]
                if "||" in dct:
                    dct = dc.split(":")[0]
                if "wgs84" in dc:
                    g.add(
                        (
                            elementURI,
                            RDFS.subPropertyOf,
                            URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#" + dct),
                        )
                    )
                else:
                    g.add(
                        (
                            elementURI,
                            RDFS.subPropertyOf,
                            URIRef("http://purl.org/dc/terms/" + dct),
                        )
                    )
            ## add dspace alternative ID
            g.add(
                (
                    elementURI,
                    URIRef("http://purl.org/dc/terms/alternative"),
                    Literal(dspace),
                )
            )
            ## create controlled vocab
            cvURI = URIRef(NS + "VOCAB_" + element_name.replace(" ", "_"))
            g.add((cvURI, RDF.type, OWL.Class))  ## SKOS.Concept ## SKOS.Collection??
            g.add((cvURI, SKOS.prefLabel, Literal("VOCAB " + element_name)))
            ## open controlled vocab file
            ## open controlled vocab file
            try:
                with open(
                    "data/controlled-vocabularies/"
                    + dspace.replace(".", "-").lower()
                    + ".txt",
                    "r",
                    encoding="utf-8",
                ) as f:
                    lines = f.readlines()
                    for line in lines:
                        term = line.strip()
                        termURI = URIRef(NS + term.replace(" ", "_").replace("|", ""))
                        g.add((termURI, RDF.type, OWL.Class))  ## SKOS.Concept
                        g.add((termURI, SKOS.prefLabel, Literal(term)))
                        g.add((termURI, RDFS.subClassOf, cvURI))  ## SKOS.member???
                g.add((elementURI, OWL.range, cvURI))

                ## add the controlled vocab information on properties directly
                g.add(
                    (
                        elementURI,
                        URIRef("http://purl.org/dc/dcam/rangeIncludes"),
                        Literal(
                            "https://raw.githubusercontent.com/iseal-community/iseal-core/main/data/controlled-vocabularies/"
                            + dspace.replace(".", "-").lower()
                            + ".txt"
                        ),
                    )
                )
            except FileNotFoundError:
                continue

            ## cardinality
            if cardinality == "MULTI SELECT FROM CONTROL LIST":
                br = BNode()
                g.add((br, RDF.type, OWL.Restriction))
                g.add((br, OWL.onProperty, elementURI))
                g.add((br, OWL.minQualifiedCardinality, Literal(1)))
                g.add((br, OWL.someValuesFrom, cvURI))
                g.add((conceptUri, RDFS.subClassOf, br))
            else:
                br = BNode()
                g.add((br, RDF.type, OWL.Restriction))
                g.add((br, OWL.onProperty, elementURI))
                g.add((br, OWL.maxQualifiedCardinality, Literal(1)))
                g.add((br, OWL.onClass, cvURI))
                g.add((conceptUri, RDFS.subClassOf, br))

        else:  ## datatype properties
            g.add((elementURI, SKOS.prefLabel, Literal(element_name)))
            g.add((elementURI, RDF.type, OWL.DatatypeProperty))
            g.add((elementURI, OWL.domain, conceptUri))
            if dc:
                dct = dc.split(":")[1]
                if "||" in dct:
                    dct = dc.split(":")[0]
                if "wgs84" in dc:
                    g.add(
                        (
                            elementURI,
                            RDFS.subPropertyOf,
                            URIRef("http://www.w3.org/2003/01/geo/wgs84_pos#" + dct),
                        )
                    )
                else:
                    g.add(
                        (
                            elementURI,
                            RDFS.subPropertyOf,
                            URIRef("http://purl.org/dc/terms/" + dct),
                        )
                    )
            ## add dspace alternative ID
            g.add(
                (
                    elementURI,
                    URIRef("http://purl.org/dc/terms/alternative"),
                    Literal(dspace),
                )
            )
            range = None
            if prop_type == "DATE":
                g.add((elementURI, OWL.range, XSD.date))
                range = XSD.date
            elif prop_type == "NUMERIC VALUE":
                g.add((elementURI, OWL.range, XSD.float))
                range = XSD.float
            else:
                g.add((elementURI, OWL.range, XSD.string))
                range = XSD.string
            ##cardinality
            if cardinality == "REPEAT VALUES":
                br = BNode()
                g.add((br, RDF.type, OWL.Restriction))
                g.add((br, OWL.onProperty, elementURI))
                g.add((br, OWL.someValuesFrom, range))
                g.add((conceptUri, RDFS.subClassOf, br))
            else:
                br = BNode()
                g.add((br, RDF.type, OWL.Restriction))
                g.add((br, OWL.onProperty, elementURI))
                g.add((br, OWL.maxQualifiedCardinality, Literal(1)))
                g.add((br, OWL.onDataRange, range))
                g.add((conceptUri, RDFS.subClassOf, br))

        if comment:
            g.add((elementURI, SKOS.scopeNote, Literal(comment)))
        if example:
            g.add((elementURI, RDFS.comment, Literal(example)))
        if element_description:
            g.add((elementURI, SKOS.definition, Literal(element_description)))

    ## save graph
    head, tail = os.path.split(file)
    filename = tail.split(".")[0]
    g.serialize(destination="data/rdf/" + filename + ".ttl", format="turtle")


parser = argparse.ArgumentParser(
    description="Parse an ISEAL schema CSV file to export it as RDF."
)
parser.add_argument(
    "-i",
    "--input-file",
    help="Path to schema fields file (ie, iseal-core.csv).",
    required=True,
    type=argparse.FileType("r"),
)
parser.add_argument(
    "-ns",
    "--namespace",
    help="Namespace of the schema. Used to create the URIs, should point to the website (ie. https://iseal-community.github.io/iseal-core#).",
    required=True,
)
args = parser.parse_args()
try:
    make_rdf(args.input_file.name, args.namespace)
except FileNotFoundError:
    sys.stderr.write(f"  Could not open {args.input_file.name}\n")
