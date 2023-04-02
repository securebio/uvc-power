import numpy as np
import json

from src import rig


R0 = [0.1 * i for i in range(5, 14)] + [0.65]
PREV = [0.05, 0.1, 0.2, 0.4]
DURATION = [30, 60, 120]
T_REC = [6, 12]
case_sim_template = "data/cases/r0={r0}/prev={prev}/duration={duration}/t_rec={t_rec}.txt"
avg_sim_template = "data/avg/r0={r0}/prev={prev}/duration={duration}/t_rec={t_rec}.txt"

rule all:
    input:
        expand(avg_sim_template, prev=PREV, r0=R0, duration=DURATION, t_rec=T_REC)

rule simulate_cases:
    output:
        case_sim_template
    run:
        n_sims = 2000
        params = dict(
            n_days = 180,
            duration = float(wildcards.duration),
            peak = 90,
            total_prev = float(wildcards.prev),
            crew_size=120,
            r0=float(wildcards.r0),
            t_inf=2,
            t_rec=int(wildcards.t_rec),
            days_on=28,
            days_off=28,
            t_change=7,
            t_samps = [1, 3, 7],
            t_pos = 2,
        )
        header = "imported_cases," + ",".join(f"pos_tests_sampled_{d}_days" for d in params["t_samps"])
        with open(output[0], 'wt') as outfile:
            outfile.write(json.dumps(params) + "\n")
            outfile.write(header + "\n")
            for _ in range(n_sims):
                outfile.write(",".join(str(cases) for cases in rig.sim_cases(**params)) + "\n")


rule average_sims:
    input:
        case_sim_template
    output:
        avg_sim_template
    run:
        with open(output[0], 'wt') as outfile:
            with open(input[0], 'rt') as infile:
                outfile.write(infile.readline())
                outfile.write(infile.readline())
                data = np.loadtxt(infile, delimiter=",")
            outfile.write(','.join(str(x) for x in np.mean(data, axis=0)) + '\n')
            outfile.write(','.join(str(x) for x in np.var(data, axis=0)) + '\n')
