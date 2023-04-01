from dataclasses import dataclass
from typing import Optional, Iterable, Callable
from enum import Enum
from random import random
from itertools import cycle, islice, chain
import numpy as np


class Shift(str, Enum):
    ON = 1
    OFF = 2


class InfectionStatus(Enum):
    S = 1
    I = 2  # noqa: E741
    R = 3


@dataclass
class Worker:
    shift: Shift
    shift_days: int
    infection_status: InfectionStatus
    infection_days: int


Crew = list[Worker]


@dataclass
class ScheduleEntry:
    length: int
    next_shift: Shift


Schedule = dict[Shift, ScheduleEntry]


def change_shift(worker: Worker, sched: Schedule) -> Worker:
    sched_entry = sched[worker.shift]
    if worker.shift_days >= sched_entry.length:
        return Worker(
            sched_entry.next_shift, 0, worker.infection_status, worker.infection_days
        )
    else:
        return worker


def advance_day(w: Worker) -> Worker:
    return Worker(w.shift, w.shift_days + 1, w.infection_status, w.infection_days + 1)


RateMap = dict[Shift, float]


def infect(w: Worker, infection_rates: RateMap, infection_age: int = 0) -> Worker:
    if w.infection_status == InfectionStatus.S and random() <= infection_rates[w.shift]:
        return Worker(w.shift, w.shift_days, InfectionStatus.I, infection_age)
    else:
        return w


def recover(w: Worker, t_rec: int) -> Worker:
    if w.infection_status == InfectionStatus.I and w.infection_days >= t_rec:
        return Worker(w.shift, w.shift_days, InfectionStatus.R, 0)
    else:
        return w


def count_shift(crew: Crew, shift: Shift) -> int:
    return sum(w.shift == shift for w in crew)


def count_infected(crew: Crew, shift: Optional[Shift] = None) -> int:
    return sum(
        not shift or w.shift == shift
        for w in crew
        if w.infection_status == InfectionStatus.I
    )


def _generate_shift(
    shift: Shift, crew_size: int, sched: Schedule, t_change: int
) -> Iterable[Worker]:
    num_shift = crew_size * sched[shift].length // sched[Shift.ON].length
    return islice(
        cycle(
            Worker(shift, d, InfectionStatus.S, 0)
            for d in range(0, sched[shift].length, t_change)
        ),
        num_shift,
    )


def initialize_crew(crew_size: int, sched: Schedule, t_change: int) -> Crew:
    return list(
        chain.from_iterable(
            _generate_shift(s, crew_size, sched, t_change) for s in Shift
        )
    )


def first_positive_test(w: Worker, t_pos: int) -> bool:
    return (
        w.shift == Shift.ON
        and w.infection_status == InfectionStatus.I
        # Don't count new infections on when they first join the crew
        and w.shift_days > 0
        and w.infection_days == t_pos
    )


def count_first_positive_tests(crew: Crew, t_pos: int) -> int:
    return sum(first_positive_test(w, t_pos) for w in crew)


def power(
    test_stat_control: np.ndarray, test_stat_alt: np.ndarray, alpha: float = 0.05
) -> np.ndarray:
    t_thresh = np.quantile(test_stat_control, 1 - alpha, axis=-1)
    return np.mean(test_stat_alt > np.expand_dims(t_thresh, axis=(-1, -2)), axis=-1)


SimulationResult = list[Crew]


def run_simulation(
    n_days: int,
    crew_size: int,
    prevalence: Callable[[int], float],
    r0: float,
    t_inf: int,
    t_rec: int,
    schedule: Schedule,
    t_change: int,
) -> SimulationResult:
    def _infection_rates(c: Crew, day: int) -> RateMap:
        rate_off = prevalence(day) / t_rec
        prop_inf_on = count_infected(c, Shift.ON) / count_shift(c, Shift.ON)
        rate_on = r0 * prop_inf_on / (t_rec - t_inf)
        return {Shift.OFF: rate_off, Shift.ON: rate_on}

    def _step(c: Crew, day: int) -> Crew:
        rates = _infection_rates(c, day)
        infected = (infect(w, rates) for w in c)
        recovered = (recover(w, t_rec) for w in infected)
        changed = (change_shift(w, schedule) for w in recovered)
        return [advance_day(w) for w in changed]

    crew = initialize_crew(crew_size, schedule, t_change)
    sim = [crew]
    for day in range(n_days):
        sim.append(_step(sim[-1], day))
    return sim


def sim_cases(
    t_pos: int,
    days_on: int,
    days_off: int,
    **params,
) -> list[int]:
    schedule = {
        Shift.ON: ScheduleEntry(days_on, Shift.OFF),
        Shift.OFF: ScheduleEntry(days_off, Shift.ON),
    }
    sim = run_simulation(schedule=schedule, **params)
    return [count_first_positive_tests(crew, t_pos) for crew in sim]


def main():
    days_on = 28
    days_off = 28
    params = dict(
        n_days=365,
        crew_size=120,
        prevalence=lambda d: 0.05,
        r0=1.3,
        t_inf=2,
        t_rec=12,
        schedule={
            Shift.ON: ScheduleEntry(days_on, Shift.OFF),
            Shift.OFF: ScheduleEntry(days_off, Shift.ON),
        },
        t_change=7,
    )
    sim = run_simulation(**params)
    for line in sim:
        print(count_infected(line, Shift.ON), count_infected(line, Shift.OFF))


if __name__ == "__main__":
    main()
