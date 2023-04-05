from sys import argv

import matplotlib.pyplot as plt  # type: ignore
import numpy as np

from src.cruise import simulate, total_positive_tests


def sim_power(n_sims, reduction_factor, Tpos, *params):
    sims_control = [simulate(*params) for _ in range(n_sims)]
    sims_uv = [
        simulate(*params, reduction_factor=reduction_factor) for _ in range(n_sims)
    ]

    pos_tests_control = np.array(
        [total_positive_tests(sim, Tpos) for sim in sims_control]
    )
    pos_tests_uv = np.array([total_positive_tests(sim, Tpos) for sim in sims_uv])

    d_control = pos_tests_control - np.random.permutation(pos_tests_control)
    d_uv = pos_tests_control - pos_tests_uv

    d_thresh = np.quantile(d_control, 0.95)
    power = np.mean(d_uv > d_thresh)
    return power


if __name__ == "__main__":
    np.random.seed(3094820)
    _, output_file = argv

    xlim = [0.1 - 0.025, 0.525]
    ylim = [-0.05, 1.05]
    xticks = np.arange(0.1, 0.55, 0.1)

    # Disease parameters
    R0 = 1.5
    c = 100
    T1 = 2
    T2 = 12
    Tpos = T1
    p = R0 / (c * (T2 - T1))

    n_sims = 4000
    reduction_factors = np.arange(0.5, 0.95, 0.05)
    num_trips = [1, 2, 5]
    trip_length = 10

    num_passengers = 400
    prevalence = 0.1
    avg_init_infected = prevalence * num_passengers

    fig = plt.figure(figsize=(3, 2))
    ax = fig.add_subplot(1, 1, 1)
    for nt in num_trips:
        # sim_power(n_sims, reduction_factor, *params):
        power_curve = np.array(
            [
                sim_power(
                    n_sims,
                    rf,
                    Tpos,
                    nt,
                    avg_init_infected,
                    T1,
                    T2,
                    trip_length,
                    p,
                    c,
                    0,
                )
                for rf in reduction_factors
            ]
        )
        ax.plot(1 - reduction_factors, power_curve, label=nt)
    ax.legend(title="# of trips", frameon=False)
    ax.set_ylim(ylim)
    ax.set_xlim(xlim)
    ax.set_xticks(xticks)
    ax.set_ylabel("Power")
    ax.set_xlabel("Fraction of transmissions prevented")

    fig.savefig(
        output_file,
        bbox_inches="tight",
        dpi=300,
    )
