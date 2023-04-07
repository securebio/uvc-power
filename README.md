# UVC Power Analysis
SecureBio

Spring 2023

## Introduction

This repository contains code to simulate viral outbreaks in isolated
environments (oil rigs and cruise ships).
It was developed for a power analysis of a proposed experiment to evaluate
the efficacy of 222 nm far-UVC in reducing infection rates on oil platforms.
It contains:

- Code to simulate viral spread among workers on an oil platform (`src/rig.py`)
- Code to simulate viral spread among passengers on a cruise ship (`src/cruise.py`)
- A `snakemake` pipeline (`Snakefile`) to demonstrate use of the code and
reproduce the power analysis figures in the proposal.

## Installation

The simulation code requires Python >= 3.9.
We recommend using [`pyenv`](https://github.com/pyenv/pyenv) to manage Python versions.

First, clone the repository:
```bash
git clone https://github.com/securebio/uvc-power.git && cd uvc-power
```

Next, set up a virtual environment (optional, but recommended)
and install the requirements:
```bash
python -m venv env &&
source env/bin/activate &&
python -m pip install -r requirements.txt
```

Now the simulations are ready to run.

## Usage

To run all the simulations and make the figures:
```bash
snakemake --cores
```
If the simulation output already exists and you'd like to force snakemake to rerun the pipeline, use the `-F` flag.

**Warning**: The simulations are not optimized for speed and may take a long time to run
(~1hr using a 10-core machine).
To test the simulations without waiting as long, you can set the number of replicate simulations per condition (default=4000) to a smaller number (200 is recommended):
```bash
snakemake --cores --config n_sims=200
```
