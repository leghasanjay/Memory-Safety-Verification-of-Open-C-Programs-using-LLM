# LLM-Assisted Memory-Safety Verification of Open C Programs

## Overview

This project implements a pipeline for memory-safety verification of open C programs using LLM-generated assumptions.

The workflow is:

C program → SMACK → Boogie → LLM-generated assumptions → Boogie injection → instrumentation → Corral

The goal is to study how well LLM-generated idiomatic assumptions can help verify open programs and suppress false positives.

---

## What this repository contains

This repository contains the project files under the `AvTesting/` folder:

- `scripts/`
  - `final.py`
  - `compile_single_file_from_c_to_bpl.py`
  - `compile_single_file_from_bpl_to_bpl_inst.py`
  - `compile_simple_set_cfiles_to_inst_bpl.py`
  - `programs_to_run_on`
  - other helper scripts used in the benchmark pipeline

---

## Benchmarks

This project uses the VeriSec benchmark suite, which is provided as part of the SMACK artifact.

The benchmarks are NOT included in this repository to avoid duplication.

They are automatically available after downloading the artifact from:

https://zenodo.org/records/15760792

## External dependency

This project is designed to run inside the SMACK/Vagrant environment used in development.

The SMACK artifact can be obtained from:

https://zenodo.org/records/15760792

You must first download and extract that artifact, because the scripts in this repository expect the SMACK folder layout and the verification tools provided by that environment.

---

## Required folder layout

After downloading and extracting the SMACK artifact, place this repository inside the SMACK directory so that the final layout becomes:

```text
smack/
└── AvTesting/
    ├── scripts/
    └── benchmarks/

    Inside benchmarks/, the VeriSec tree should remain as:
    AvTesting/benchmarks/verisec-benchmarks/suite/
├── programs/
│   └── apps/
└── lib/
    └── stubs.c


    Setup instructions
1. Download and extract the SMACK artifact

Download the artifact from:
https://zenodo.org/records/15760792

Extract it on your machine.

2. Copy this repository into the SMACK directory

Copy the AvTesting/ folder from this repository into:
smack/AvTesting/

3. Keep the benchmark tree in place

Make sure the VeriSec benchmark files remain under:

smack/AvTesting/benchmarks/verisec-benchmarks/

The script expects the benchmark applications in:

smack/AvTesting/benchmarks/verisec-benchmarks/suite/programs/apps/

and the stub file in:
smack/AvTesting/benchmarks/verisec-benchmarks/suite/lib/stubs.c

4. Start the VM
From the SMACK root directory, run:
vagrant up
vagrant ssh

5. Go to the scripts directory

Inside the VM, move to:
cd AvTesting/scripts

6. Run the benchmark script
Run:
python3 compile_simple_set_cfiles_to_inst_bpl.py

This script reads the benchmark list from programs_to_run_on, translates the selected C programs to Boogie, generates assumptions using the LLM, injects them into the Boogie file, instruments the result, and runs Corral.


Outputs

The benchmark run produces:

generated .bpl files
generated _inst.bpl files
benchmark_results.csv

The final summary is printed in the terminal.

My final Result on benchmark of 285 open c programs-->
==============================
FINAL SUMMARY
==============================
Total: 285
SAFE: 25
BUG: 27
ERROR: 230
UNKNOWN: 3

Result meaning in this implementation
SAFE
Corral proves the program safe under the generated assumptions.
BUG
Corral reports a bug. In this implementation, this often indicates that the assumptions were too weak or incomplete.
ERROR
The pipeline failed before a valid verification result could be produced. This usually means a syntax or instrumentation issue in the generated Boogie file.
UNKNOWN
The verifier did not produce a clear classification.

--> loook wait wait, read this repo ,  i think we didn't required benchmark folder also, as all the folders are present in aftifact zip file intalled by link mentioned in repo , so i think we also should reomve the benchmark folder 