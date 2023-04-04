from src import rig

global_params = dict(
    n_days = 180,
    crew_size=120,
    days_on=28,
    days_off=28,
    t_change=7,
    t_samps=[1, 3, 7],
)

VIRUSES = ["viruses", "viruses_75"]
R0 = [1.0, 1.125, 1.25, 1.5, 2.0]
RF = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]
virus_sim_template = "data/{viruses}/r0={r0}/reduction_factor={rf}.txt"


rule all:
    input:
        expand(virus_sim_template, r0=R0, rf=RF, viruses=VIRUSES)


rule simulate_viruses:
    input:
        "{viruses}.json"
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
