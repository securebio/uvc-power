from src import rig
import json


rule all:
    input:
        expand("data/cases_prev={prev}.txt", prev=[0.025, 0.05, 0.1])


rule simulate_cases:
    output:
        "data/cases_prev={prev}.txt"
    run:
        n_sims = 100
        params = dict(
            days_on = 28,
            days_off = 28,
            crew_size = 100,
            prevalence = float(wildcards.prev),
            n_days = 240,
            t_pos=2,
            t_inf=2,
            t_rec=12,
            r0=1.3,
            t_change=7,
        )
        with open(output[0], 'wt') as outfile:
            outfile.write(json.dumps(params) + "\n")
            for _ in range(n_sims):
                outfile.write(",".join(str(cases) for cases in rig.sim_cases(**params)) + "\n")
