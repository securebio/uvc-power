import numpy as np
import sys
from itertools import product
from src import rig
from typing import Iterable


def power(
    test_stat_control: np.ndarray, test_stat_alt: np.ndarray, alpha: float = 0.05
) -> np.ndarray:
    t_thresh = np.quantile(test_stat_control, 1 - alpha, axis=-1)
    return np.mean(test_stat_alt > np.expand_dims(t_thresh, axis=(-1, -2)), axis=-1)


def total_pos_tests(sim: rig.SimulationResult, t_pos: int) -> int:
    return sum(rig.count_first_positive_tests(crew, t_pos) for crew in sim)


def sim_power(
    n_sims: int,
    n_days: Iterable[int],
    r0: float,
    reduction_factors: Iterable[float],
    t_pos: int,
    **params,
) -> np.ndarray:
    sims_control = [
        rig.run_simulation(r0=r0, n_days=max(n_days), **params) for _ in range(n_sims)
    ]
    sims_uv = [
        [
            rig.run_simulation(r0=r0 * f, n_days=max(n_days), **params)
            for _ in range(n_sims)
        ]
        for f in reduction_factors
    ]
    pos_tests_control = np.array(
        [[total_pos_tests(sim[:nd], t_pos) for sim in sims_control] for nd in n_days]
    )
    pos_tests_uv = np.array(
        [
            [[total_pos_tests(sim[:nd], t_pos) for sim in sims] for sims in sims_uv]
            for nd in n_days
        ]
    )

    rng = np.random.default_rng()
    d_null = pos_tests_control - rng.permutation(pos_tests_control, axis=-1)
    d_alt = pos_tests_control[:, np.newaxis, :] - pos_tests_uv
    return power(d_null, d_alt)


def main():
    days_on = 28
    days_off = 28
    crew_sizes = [50, 100, 200]
    prevalences = [0.025, 0.05, 0.1]
    n_days = [30 * months for months in range(1, 9)]
    reduction_factors = [0.5, 0.8]
    print("crew_size", "prevalence", "days", "reduction_factor", "power", sep=",")
    for crew_size, prevalence in product(crew_sizes, prevalences):
        sys.stderr.write(
            f"Working on: crew_size={crew_size}, prevalence={prevalence}\n"
        )
        params = dict(
            n_sims=1000,
            n_days=n_days,
            crew_size=crew_size,
            prevalence=prevalence,
            t_inf=2,
            t_rec=12,
            t_pos=2,
            r0=1.3,
            reduction_factors=reduction_factors,
            schedule={
                rig.Shift.ON: rig.ScheduleEntry(days_on, rig.Shift.OFF),
                rig.Shift.OFF: rig.ScheduleEntry(days_off, rig.Shift.ON),
            },
            t_change=7,
        )
        powers = sim_power(**params)
        for (i, nd), (j, f) in product(enumerate(n_days), enumerate(reduction_factors)):
            print(crew_size, prevalence, nd, f, powers[i, j], sep=",")


if __name__ == "__main__":
    main()
