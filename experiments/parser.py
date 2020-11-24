#! /usr/bin/env python

import json

from lab.parser import Parser


def error(content, props):
    if props["extractor_exit_code"] == 0:
        props["error"] = "none"
    else:
        props["error"] = "error-occured"


def parse_features(content, props):
    dic = json.loads(content)
    features = list(dic["instance_features"].values())[0]
    props.update(features)


parser = Parser()
parser.add_pattern("node", r"node: (.+)\n", type=str, file="driver.log", required=True)
parser.add_pattern(
    "extractor_exit_code", r"compute-features exit code: (.+)\n", type=int, file="driver.log"
)
parser.add_function(error)
parser.add_function(parse_features, file="features.json")
parser.parse()
