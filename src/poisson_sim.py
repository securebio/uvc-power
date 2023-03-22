import numpy as np
import matplotlib.pyplot as plt  # type: ignore


def simulate(
    avg_init_infected: float,
    T1: int,
    T2: int,
    Tc: int,
    p: float,
    c: float,
) -> np.ndarray:
    n_infected = np.zeros((Tc + 1, T2 - T1))
    n_infected[0] = initialize_infected(
        avg_init_infected,
        T1,
        T2,
    )
    for i in range(1, Tc + 1):
        new_infections = generate_new_infections(n_infected[i - 1], p, c)
        n_infected[i, 0] = new_infections
        n_infected[i, 1:] = n_infected[i - 1, :-1]
    return n_infected


def initialize_infected(
    avg_init_infected: float,
    T1: int,
    T2: int,
) -> np.ndarray:
    lam = avg_init_infected / float(T2 - T1)
    return np.random.poisson(lam, T2 - T1)


def generate_new_infections(n_infected: np.ndarray, p: float, c: float) -> int:
    lam = p * c * np.sum(n_infected)
    return np.random.poisson(lam)


def new_positive_tests(n_infected: np.ndarray, tpos: int) -> np.ndarray:
    return n_infected[:, tpos]


def total_positive_tests(n_infected: np.ndarray, tpos: int) -> int:
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
    Tc = 10
    avg_init_infected = 16
    reduction_factor = 0.5

    n_sims = 10000
    pos_tests_null1 = np.array(
        [
            total_positive_tests(simulate(avg_init_infected, T1, T2, Tc, p, c), Tpos)
            for i in range(n_sims)
        ]
    )

    pos_tests_null2 = np.array(
        [
            total_positive_tests(simulate(avg_init_infected, T1, T2, Tc, p, c), Tpos)
            for i in range(n_sims)
        ]
    )

    pos_tests_alt = np.array(
        [
            total_positive_tests(
                simulate(avg_init_infected, T1, T2, Tc, p * reduction_factor, c), Tpos
            )
            for i in range(n_sims)
        ]
    )

    d_null = pos_tests_null1 - pos_tests_null2
    d_alt = pos_tests_null1 - pos_tests_alt

    d_thresh = np.quantile(d_null, 0.95)
    power = np.mean(d_alt > d_thresh)
    print(d_thresh)
    print(power)
    bins = np.arange(min(d_null) - 1, max(d_alt) + 1, 1)
    plt.hist(d_alt[d_alt > d_thresh], bins=bins, color="C1", alpha=0.5)
    plt.hist(
        d_alt,
        bins=bins,
        histtype="step",
        color="C1",
        label=f"efficacy = {reduction_factor}",
    )
    plt.hist(d_null, bins=bins, histtype="step", color="C0", label="efficacy = 0")
    plt.legend()
    plt.xlabel("Difference in new case numbers")
    plt.ylabel("Number of simulations")
    plt.title(f"Power = {power:.2f}")
    plt.show()
