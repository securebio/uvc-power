import numpy as np
import json

from src import rig

global_params = dict(
    n_days = 180,
    crew_size=120,
    days_on=28,
    days_off=28,
    t_change=7,
    t_samps=[1, 3, 7],
)


R0 = [0.1 * i for i in range(5, 14)] + [0.65] + [2.0, 4.0]
PREV = [0.05, 0.1, 0.2, 0.4]
DURATION = [30, 60, 90, 120]
T_REC = [6, 12]
RF = [0.5, 0.6, 0.7, 0.8, 0.9]
case_sim_template = "data/cases/r0={r0}/prev={prev}/duration={duration}/t_rec={t_rec}.txt"
virus_sim_template = "data/viruses/r0={r0}/reduction_factor={rf}.txt"

rule all:
    input:
        expand(case_sim_template, prev=PREV, r0=R0, duration=DURATION, t_rec=T_REC),
        expand(virus_sim_template, r0=[1.0, 1.1, 1.2, 1.3, 1.4, 1.5], rf=RF)

rule simulate_cases:
    output:
        case_sim_template
    run:
        n_sims = 2000
        params = global_params | dict(
            duration = float(wildcards.duration),
            peak = 90,
            total_prev = float(wildcards.prev),
            r0=float(wildcards.r0),
            t_inf=2,
            t_rec=int(wildcards.t_rec),
            t_pos = 2,
        )
        header = "imported_cases," + ",".join(f"pos_tests_sampled_{d}_days" for d in params["t_samps"])
        with open(output[0], 'wt') as outfile:
            outfile.write(json.dumps(params) + "\n")
            outfile.write(header + "\n")
            for _ in range(n_sims):
                outfile.write(",".join(str(cases) for cases in rig.sim_cases(**params)) + "\n")


rule simulate_viruses:
    input:
        "viruses.json"
    output:
        virus_sim_template
    run:
        n_sims = 2000
        r0 = float(wildcards.r0)
        reduction_factor = float(wildcards.rf)
        viruses = rig.load_viruses(input[0], r0=r0, duration=60, peak=90)
        with open(output[0], 'wt') as outfile:
            for _ in range(n_sims):
                cases_control = rig.sim_multiple_viruses(
                        viruses, reduction_factor=1.0, **global_params
                        )
                cases_uv = rig.sim_multiple_viruses(
                        viruses, reduction_factor=reduction_factor, **global_params
                        )
                outfile.write(",".join(str(cases) for cases in cases_control + cases_uv) + "\n")
