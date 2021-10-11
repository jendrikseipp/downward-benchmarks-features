#! /usr/bin/env python

from collections import defaultdict
from pathlib import Path
import platform

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
if REMOTE:
    ENV = BaselSlurmEnvironment(email="jendrik.seipp@liu.se", partition="infai_2", memory_per_cpu="9G")
    REPOS = Path(project.USER.remote_repos)
    SUITE = project.SUITE_ALL
else:
    ENV = LocalEnvironment(processes=2)
    REPOS = Path(project.USER.local_repos)
BENCHMARKS_DIR = REPOS / "di-heu-sel" / "benchmarks"
SUITE = sorted(str(p) for p in BENCHMARKS_DIR.iterdir() if p.is_dir())
if not REMOTE:
    SUITE = ["gripper:autoscale14-opt-p01.pddl", "miconic:autoscale14-opt-p01.pddl"]
EXTRACTION_SCRIPT = REPOS / "planning-features" / "extract_planning_features.py"
ATTRIBUTES = [
    "error",
    "sas*",
]
TIME_LIMIT = 36000
MEMORY_LIMIT = 8192


exp = Experiment(environment=ENV)
exp.add_parser("parser.py")

domains = defaultdict(int)

for task in suites.build_suite(BENCHMARKS_DIR, SUITE):
    if not task.problem.endswith(".pddl"):
        continue
    print("TASK", task.domain, task.problem)
    domains[task.domain] += 1
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

for domain, count in sorted(domains.items()):
    print(domain, count)

exp.add_step("build", exp.build)
exp.add_step("start", exp.start_runs)
exp.add_fetcher(name="fetch")
exp.add_report(BaseReport(attributes=ATTRIBUTES), outfile="report.html")

exp.run_steps()
