import numpy as np
import matplotlib.pyplot as plt  # type: ignore


def simulate(
    num_trips: int,
    avg_init_infected: float,
    T1: int,
    T2: int,
    Tc: int,
    p: float,
    c: float,
    outside_infection_rate: float,
    reduction_factor: float = 1.0,
) -> np.ndarray:
    n_infected = np.zeros((Tc + 1, T2 - T1, num_trips))
    n_infected[0] = initialize_infected(avg_init_infected, T1, T2, num_trips)
    for i in range(1, Tc + 1):
        new_infections = generate_new_infections(
            n_infected[i - 1], p * reduction_factor, c, outside_infection_rate
        )
        n_infected[i, 0] = new_infections
        n_infected[i, 1:] = n_infected[i - 1, :-1]
    return n_infected


def initialize_infected(
    avg_init_infected: float,
    T1: int,
    T2: int,
    num_trips: int,
) -> np.ndarray:
    lam = avg_init_infected / float(T2 - T1)
    return np.random.poisson(lam, (T2 - T1, num_trips))


def generate_new_infections(
    n_infected: np.ndarray, p: float, c: float, outside_infection_rate: float
) -> int:
    lam = p * c * np.sum(n_infected, axis=0) + outside_infection_rate
    return np.random.poisson(lam)


def new_positive_tests(n_infected: np.ndarray, Tpos: int) -> np.ndarray:
    return n_infected[:, Tpos]


def total_positive_tests(n_infected: np.ndarray, Tpos: int) -> int:
    return np.sum(new_positive_tests(n_infected[1:], Tpos))


if __name__ == "__main__":
    # Disease parameters
    R0 = 1.3
    c = 100
    T1 = 2
    T2 = 12
    Tpos = 2
    p = R0 / (c * (T2 - T1))

    # Cruise parameters
    num_trips = 1
    Tc = 20
    avg_init_infected = 16 * 2
    reduction_factor = 0.5
    outside_infection_rate = 0.0

    n_sims = 10000
    params = (
        num_trips,
        avg_init_infected,
        T1,
        T2,
        Tc,
        p,
        c,
        outside_infection_rate,
    )
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

    bins = np.arange(min(d_control) - 1, max(d_uv) + 1, 1)
    plt.hist(d_uv[d_uv > d_thresh], bins=bins, color="C1", alpha=0.5)
    plt.hist(
        d_uv,
        bins=bins,
        histtype="step",
        color="C1",
        label="50% reduction in spread",
    )
    plt.hist(
        d_control, bins=bins, histtype="step", color="C0", label="null (no reduction)"
    )
    plt.legend()
    plt.xlabel("Difference in new case numbers")
    plt.ylabel("Number of simulations")
    plt.title(f"Power = {power:.2f}")
    plt.savefig("fig/power_example.png")
    plt.show()

    ax1 = plt.subplot(211)
    for sim in sims_control[:100]:
        ax1.plot(sim[1:, Tpos, 0], color="C0", alpha=0.25)
    ax1.set_ylim([-0.5, 10])
    ax2 = plt.subplot(212)
    for sim in sims_uv[:100]:
        ax2.plot(sim[1:, Tpos, 0], color="C0", alpha=0.25)
    ax2.set_ylim([-0.5, 10])
    plt.show()
