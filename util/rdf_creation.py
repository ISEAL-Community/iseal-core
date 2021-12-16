#!/usr/bin/env python
# coding: utf-8

from rdflib import Graph
from rdflib.namespace import OWL, DC, DCTERMS, RDF, RDFS, SKOS, XSD
from rdflib import URIRef, BNode, Literal
import json
import os
import pandas as pd
import re


def make_core():
    g = Graph()

    ##namespace
    # NS = "http://iseal.org/terms/"
    NS = "https://alanorth.github.io/iseal-schema/#"
    ## create ontology
    iseal = URIRef(NS)
    g.add((iseal, RDF.type, OWL.Ontology))

    df = pd.read_csv("../data/schema-fields.csv")
    df.dropna(how="all", axis=1)
    df.fillna("", inplace=True)

    for index, row in df.iterrows():
        element_name = row["element name"]
        element_description = row["element description"]
        comment = row["element guidance"]
        example = row["element link for more information"]
        cardinality = row["element options"]
        prop_type = row["element type"]
        controlled_vocab = row["element controlled values or terms"]
        module = row["idss element cluster"]
        module_cat = row["idss schema module"]
        dc = row["element link for dublin core attributes"]
        dspace = row["dspace field name"]

        ##module
        moduleUri = URIRef(NS + module)
        if not (None, SKOS.prefLabel, Literal(module)) in g:
            ##create module as skos concept
            g.add((moduleUri, RDF.type, OWL.Class))  ## SKOS.Concept
            g.add((moduleUri, SKOS.prefLabel, Literal(module)))
        ##element
        # if '-' not in element_name:
        if True:  ## lazy reindenting
            concept = module_cat  # element_name.split(' - ')[0]
            # element = element_name.strip()
            ## code from Alan
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

            # For example Certifying Body, FSC audit, Certificate, etc
            cluster = row["idss element cluster"].capitalize()

            # For example Assurance, Certification, Core, Impact, etc
            module = row["idss schema module"].capitalize()

            # Generate a "safe" version of the element name for use in URLs and
            # files by combining the cluster and the element name. This could
            # change in the future.
            element_name_safe = cluster.replace(" ", "-").lower() + "-" + element_name

            element = element_name_safe

            conceptUri = URIRef(NS + concept.replace(" ", "_"))
            if not (None, SKOS.prefLabel, Literal(concept)) in g:
                ##create concept as skos concept
                g.add((conceptUri, RDF.type, OWL.Class))  ## SKOS.Concept
                g.add((conceptUri, SKOS.prefLabel, Literal(concept)))
                g.add((conceptUri, RDFS.subClassOf, moduleUri))

            ## create properties
            elementURI = URIRef(NS + element.replace(" ", "_"))
            if prop_type == "CONTROLLED VALUE":  ## object property
                g.add((elementURI, SKOS.prefLabel, Literal(element)))
                g.add((elementURI, RDF.type, OWL.ObjectProperty))
                g.add((elementURI, OWL.domain, conceptUri))
                ## add suproperty link
                if dc:
                    dct = dc.split(":")[1]
                    if "wgs84" in dc:
                        g.add(
                            (
                                elementURI,
                                RDFS.subPropertyOf,
                                URIRef(
                                    "http://www.w3.org/2003/01/geo/wgs84_pos#" + dct
                                ),
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
                cvURI = URIRef(NS + "VOCAB_" + element.replace(" ", "_"))
                g.add(
                    (cvURI, RDF.type, OWL.Class)
                )  ## SKOS.Concept ## SKOS.Collection??
                g.add((cvURI, SKOS.prefLabel, Literal("VOCAB " + element)))
                for term in controlled_vocab.split("||"):
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
                            "https://raw.githubusercontent.com/alanorth/iseal-schema/main/data/controlled-vocabularies/"
                            + element
                            + ".txt"
                        ),
                    )
                )

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

            # elif prop_type == 'URL': ## object property
            #    g.add((elementURI, RDF.type, OWL.ObjectProperty))
            #    g.add((elementURI, OWL.domain, conceptUri))
            #    g.add((elementURI, OWL.range, URIRef("") ))
            #    g.add((elementURI, SKOS.prefLabel, Literal(element)))
            else:  ## datatype properties
                g.add((elementURI, SKOS.prefLabel, Literal(element)))
                g.add((elementURI, RDF.type, OWL.DatatypeProperty))
                g.add((elementURI, OWL.domain, conceptUri))
                if dc:
                    dct = dc.split(":")[1]
                    if "wgs84" in dc:
                        g.add(
                            (
                                elementURI,
                                RDFS.subPropertyOf,
                                URIRef(
                                    "http://www.w3.org/2003/01/geo/wgs84_pos#" + dct
                                ),
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
        # else:
        # print(element_name)

    ## save graph
    g.serialize(destination="idds_new3.ttl", format="turtle")


def make_fsc():
    g = Graph()

    ##namespace
    # NS = "http://iseal.org/terms/"
    NS = "https://alanorth.github.io/iseal-schema/FSC#"
    ## create ontology
    iseal = URIRef(NS)
    g.add((iseal, RDF.type, OWL.Ontology))

    df = pd.read_excel("./idss_schema_fields_new2.xlsx", "fsc extension")
    df.dropna(how="all", axis=1)
    df.fillna("", inplace=True)

    for index, row in df.iterrows():
        element_name = row["element name"]
        element_description = row["element description"]
        comment = row["element guidance"]
        example = row["element link for more information"]
        cardinality = row["element options"]
        prop_type = row["element type"]
        controlled_vocab = row["element controlled values or terms"]
        module = row["idss element cluster"]
        module_cat = row["fsc extension module"]
        dc = row["element link for dublin core attributes"]
        dspace = row["dspace field name"]

        ##module
        moduleUri = URIRef(NS + module)
        if not (None, SKOS.prefLabel, Literal(module)) in g:
            ##create module as skos concept
            g.add((moduleUri, RDF.type, OWL.Class))  ## SKOS.Concept
            g.add((moduleUri, SKOS.prefLabel, Literal(module)))
        ##element
        # if '-' not in element_name:
        if True:  ## lazy reindenting
            concept = module_cat  # element_name.split(' - ')[0]
            # element = element_name.strip()
            ## code from Alan
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

            # For example Certifying Body, FSC audit, Certificate, etc
            cluster = row["idss element cluster"].capitalize()

            # For example Assurance, Certification, Core, Impact, etc
            module = row["fsc extension module"].capitalize()

            # Generate a "safe" version of the element name for use in URLs and
            # files by combining the cluster and the element name. This could
            # change in the future.
            element_name_safe = cluster.replace(" ", "-").lower() + "-" + element_name

            element = element_name_safe
            # remove extra fsc in name
            element = element.replace("fsc-fsc-", "fsc-")

            conceptUri = URIRef(NS + concept.replace(" ", "_"))
            if not (None, SKOS.prefLabel, Literal(concept)) in g:
                ##create concept as skos concept
                g.add((conceptUri, RDF.type, OWL.Class))  ## SKOS.Concept
                g.add((conceptUri, SKOS.prefLabel, Literal(concept)))
                g.add((conceptUri, RDFS.subClassOf, moduleUri))

            ## create properties
            elementURI = URIRef(NS + element.replace(" ", "_"))
            if prop_type == "CONTROLLED VALUE":  ## object property
                g.add((elementURI, SKOS.prefLabel, Literal(element)))
                g.add((elementURI, RDF.type, OWL.ObjectProperty))
                g.add((elementURI, OWL.domain, conceptUri))
                ## add suproperty link
                if dc:
                    dct = dc.split(":")[1]
                    if "wgs84" in dc:
                        g.add(
                            (
                                elementURI,
                                RDFS.subPropertyOf,
                                URIRef(
                                    "http://www.w3.org/2003/01/geo/wgs84_pos#" + dct
                                ),
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
                # g.add((elementURI, URIRef("http://purl.org/dc/terms/alternative"), Literal(dspace)))
                ## create controlled vocab
                cvURI = URIRef(NS + "VOCAB_" + element.replace(" ", "_"))
                g.add(
                    (cvURI, RDF.type, OWL.Class)
                )  ## SKOS.Concept ## SKOS.Collection??
                g.add((cvURI, SKOS.prefLabel, Literal("VOCAB " + element)))
                for term in controlled_vocab.split("||"):
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
                            "https://raw.githubusercontent.com/alanorth/iseal-schema/main/data/controlled-vocabularies/"
                            + element
                            + ".txt"
                        ),
                    )
                )

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

            # elif prop_type == 'URL': ## object property
            #    g.add((elementURI, RDF.type, OWL.ObjectProperty))
            #    g.add((elementURI, OWL.domain, conceptUri))
            #    g.add((elementURI, OWL.range, URIRef("") ))
            #    g.add((elementURI, SKOS.prefLabel, Literal(element)))
            else:  ## datatype properties
                g.add((elementURI, SKOS.prefLabel, Literal(element)))
                g.add((elementURI, RDF.type, OWL.DatatypeProperty))
                g.add((elementURI, OWL.domain, conceptUri))
                if dc:
                    dct = dc.split(":")[1]
                    if "wgs84" in dc:
                        g.add(
                            (
                                elementURI,
                                RDFS.subPropertyOf,
                                URIRef(
                                    "http://www.w3.org/2003/01/geo/wgs84_pos#" + dct
                                ),
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
                # g.add((elementURI, URIRef("http://purl.org/dc/terms/alternative"), Literal(dspace)))
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
        # else:
        # print(element_name)

    ## save graph
    g.serialize(destination="fsc.ttl", format="turtle")


make_core()
