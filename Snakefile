import numpy as np
import json

from src import rig


PREV = np.logspace(-2, 0, 3, base=2) * 0.1
R0 = [0.1 * i for i in range(5, 14)] + [0.65]
SHIFT = [28]
case_sim_template = "data/cases/shift={shift}/prev={prev}/r0={r0}.txt"

rule all:
    input:
        expand(case_sim_template, prev=PREV, r0=R0, shift=SHIFT)


rule simulate_cases:
    output:
        case_sim_template
    run:
        n_sims = 2000
        params = dict(
            days_on = int(wildcards.shift),
            days_off = 28,
            crew_size = 100,
            prevalence = float(wildcards.prev),
            n_days = 460,
            t_pos=2,
            t_inf=2,
            t_rec=12,
            r0=float(wildcards.r0),
            t_change=7,
        )
        with open(output[0], 'wt') as outfile:
            outfile.write(json.dumps(params) + "\n")
            for _ in range(n_sims):
                outfile.write(",".join(str(cases) for cases in rig.sim_cases(**params)) + "\n")
