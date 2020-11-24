#! /usr/bin/env python

import os
import platform
import shutil

from downward import suites
from downward.reports.absolute import AbsoluteReport
from lab.environments import BaselSlurmEnvironment, LocalEnvironment
from lab.experiment import Experiment

import project


# Create custom report class with suitable info and error attributes.
class BaseReport(AbsoluteReport):
    INFO_ATTRIBUTES = ["time_limit", "memory_limit"]
    ERROR_ATTRIBUTES = [
        "domain",
        "problem",
        "unexplained_errors",
        "error",
        "node",
    ]


NODE = platform.node()
REMOTE = NODE.endswith(".scicore.unibas.ch") or NODE.endswith(".cluster.bc2.ch")
EXTRACTION_SCRIPT = os.environ["EXTRACT_PLANNING_FEATURES"]
BENCHMARKS_DIR = os.environ["DOWNWARD_BENCHMARKS"]
if REMOTE:
    ENV = BaselSlurmEnvironment(email="jendrik.seipp@unibas.ch", partition="infai_2")
    SUITE = project.SUITE_ALL
else:
    ENV = LocalEnvironment(processes=2)
    SUITE = ["gripper:prob01.pddl", "miconic:s1-0.pddl", "mystery:prob07.pddl"]
ATTRIBUTES = [
    "error",
    "sas*",
]
TIME_LIMIT = 36000
MEMORY_LIMIT = 3584


exp = Experiment(environment=ENV)
exp.add_parser("parser.py")

for task in suites.build_suite(BENCHMARKS_DIR, SUITE):
    run = exp.add_run()
    run.add_resource("domain", task.domain_file, symlink=True)
    run.add_resource("problem", task.problem_file, symlink=True)
    run.add_command(
        "compute-features",
        ["python2", EXTRACTION_SCRIPT,
         "--domain-file", "{domain}", "--instance-file", "{problem}",
         "--json-output-file", "features.json",
         "--csv-output-file", "features.csv",
        ],
        time_limit=TIME_LIMIT,
        memory_limit=MEMORY_LIMIT,
    )
    run.set_property("domain", task.domain)
    run.set_property("problem", task.problem)
    run.set_property("algorithm", "extractor")
    # BaseReport needs the following properties:
    # 'time_limit', 'memory_limit'.
    run.set_property("time_limit", TIME_LIMIT)
    run.set_property("memory_limit", MEMORY_LIMIT)
    run.set_property("id", [task.domain, task.problem])

exp.add_step("build", exp.build)
exp.add_step("start", exp.start_runs)
exp.add_fetcher(name="fetch")
exp.add_report(BaseReport(attributes=ATTRIBUTES), outfile="report.html")

exp.run_steps()
