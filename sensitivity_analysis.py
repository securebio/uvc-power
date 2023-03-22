import numpy as np
import matplotlib.pyplot as plt  # type: ignore
from src.poisson_sim import simulate, total_positive_tests


def sim_power(n_sims, reduction_factor, *params):
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
    # Disease parameters
    R0 = 1.3
    c = 100
    T1 = 2
    T2 = 12
    Tpos = 2
    p = R0 / (c * (T2 - T1))

    n_sims = 4000
    reduction_factors = np.arange(0.2, 1.0, 0.2)
    num_trips = [1, 2, 5]
    num_passengers = [400, 1200, 3600]
    trip_lengths = [10, 20]

    for prevalence in [0.04, 0.1]:
        for outside_infection_rate in [0, 1 / 400]:
            fig, axes = plt.subplots(
                len(num_passengers), len(trip_lengths), figsize=(6, 8)
            )

            for i, num_p in enumerate(num_passengers):
                for j, Tc in enumerate(trip_lengths):
                    ax = axes[i, j]
                    avg_init_infected = prevalence * num_p
                    for nt in num_trips:
                        power_curve = np.array(
                            [
                                sim_power(
                                    n_sims,
                                    rf,
                                    nt,
                                    avg_init_infected,
                                    T1,
                                    T2,
                                    Tc,
                                    p,
                                    c,
                                    outside_infection_rate * num_p,
                                )
                                for rf in reduction_factors
                            ]
                        )
                        ax.plot(reduction_factors, power_curve, label=nt)
                    ax.legend(title="# trips")
                    ax.set_ylim([-0.05, 1.05])
                    if j == 0:
                        ax.set_ylabel("Power")
                    else:
                        ax.set_yticklabels([])
                    if i == 0:
                        ax.set_title(f"Trip length = {Tc} days\n# passengers = {num_p}")
                    else:
                        ax.set_title(f"# passengers = {num_p}")
                    if i == len(num_passengers) - 1:
                        ax.set_xlabel("Transmission reduction factor")
                    else:
                        ax.set_xticklabels([])

            fig.savefig(
                f"fig/power_analysis_prevalence={prevalence}_orate={outside_infection_rate}.png",
                bbox_inches="tight",
            )
