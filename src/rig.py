from dataclasses import dataclass
from typing import Optional, Iterable, Callable
from enum import Enum
from random import random
from itertools import cycle, islice, chain, accumulate
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
    shift_changed_on: int
    infection_status: InfectionStatus
    infection_status_changed_on: int


Crew = list[Worker]


@dataclass
class ScheduleEntry:
    length: int
    next_shift: Shift


Schedule = dict[Shift, ScheduleEntry]


def change_shift(worker: Worker, day: int, sched: Schedule) -> Worker:
    sched_entry = sched[worker.shift]
    if day - worker.shift_changed_on >= sched_entry.length:
        return Worker(
            sched_entry.next_shift,
            day,
            worker.infection_status,
            worker.infection_status_changed_on,
        )
    else:
        return worker


RateMap = dict[Shift, float]


def infect(w: Worker, day: int, infection_rates: RateMap) -> Worker:
    if w.infection_status == InfectionStatus.S and random() <= infection_rates[w.shift]:
        return Worker(w.shift, w.shift_changed_on, InfectionStatus.I, day)
    else:
        return w


def recover(w: Worker, day: int, t_rec: int) -> Worker:
    if (
        w.infection_status == InfectionStatus.I
        and day - w.infection_status_changed_on >= t_rec
    ):
        return Worker(w.shift, w.shift_changed_on, InfectionStatus.R, day)
    else:
        return w


def count_shift(crew: Crew, shift: Shift) -> int:
    return sum(w.shift == shift for w in crew)


def count_status(
    crew: Crew, status: InfectionStatus, shift: Optional[Shift] = None
) -> int:
    return sum(
        not shift or w.shift == shift for w in crew if w.infection_status == status
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


SimulationResult = list[Crew]


def run_simulation(
    n_days: int,
    crew_size: int,
    mainland_infection_rate: Callable[[int], float],
    r0: float,
    t_inf: int,
    t_rec: int,
    days_on: int,
    days_off: int,
    t_change: int,
) -> SimulationResult:
    schedule = {
        Shift.ON: ScheduleEntry(days_on, Shift.OFF),
        Shift.OFF: ScheduleEntry(days_off, Shift.ON),
    }

    def _infection_rates(c: Crew, day: int) -> RateMap:
        rate_off = mainland_infection_rate(day)
        prop_inf_on = count_status(c, InfectionStatus.I, Shift.ON) / count_shift(
            c, Shift.ON
        )
        rate_on = r0 * prop_inf_on / (t_rec - t_inf)
        return {Shift.OFF: rate_off, Shift.ON: rate_on}

    def _step(c: Crew, day: int) -> Crew:
        rates = _infection_rates(c, day)
        infected = (infect(w, day, rates) for w in c)
        recovered = (recover(w, day, t_rec) for w in infected)
        return [change_shift(w, day, schedule) for w in recovered]

    crew = initialize_crew(crew_size, schedule, t_change)
    days = range(1, n_days)
    return list(accumulate(days, _step, initial=crew))


# NOTE: Not generically correct, just works for current infection
def _tests_positive(w: Worker, d: int, t_pos: int) -> bool:
    return (
        w.shift == Shift.ON
        and w.infection_status == InfectionStatus.I
        and w.shift_changed_on <= d
        and w.infection_status_changed_on <= d - t_pos
    )


def count_first_positive_tests(
    sim: SimulationResult,
    test_frequency: int,
    t_pos: int,
) -> list[int]:
    test_days = range(0, len(sim), test_frequency)
    return [
        sum(
            _tests_positive(w, this_test, t_pos)
            and not _tests_positive(w, last_test, t_pos)
            for w in sim[this_test]
        )
        for last_test, this_test in zip(test_days, test_days[1:])
    ]


def _new_imported_case(w: Worker, d: int) -> bool:
    return _tests_positive(w, d, 0) and w.shift_changed_on == d


def count_new_imported_cases(sim: SimulationResult) -> list[int]:
    return [sum(_new_imported_case(w, d) for w in crew) for d, crew in enumerate(sim)]


def power(
    test_stat_control: np.ndarray, test_stat_alt: np.ndarray, alpha: float = 0.05
) -> np.ndarray:
    t_thresh = np.quantile(test_stat_control, 1 - alpha, axis=-1)
    return np.mean(test_stat_alt > np.expand_dims(t_thresh, axis=(-1, -2)), axis=-1)


def main():
    params = dict(
        n_days=365,
        crew_size=120,
        mainland_infection_rate=lambda d: 0.005 if d < 100 else 0,
        r0=1.3,
        t_inf=2,
        t_rec=12,
        days_on=28,
        days_off=28,
        t_change=7,
    )
    sim = run_simulation(**params)
    for line in sim:
        print(
            "Infected: ",
            count_status(line, InfectionStatus.I, Shift.ON),
            count_status(line, InfectionStatus.I, Shift.OFF),
        )
        print(
            "Recovered:",
            count_status(line, InfectionStatus.R, Shift.ON),
            count_status(line, InfectionStatus.R, Shift.OFF),
        )

    print("First positive tests:")
    for line in count_first_positive_tests(sim, 7, 2):
        print(line)
    print("New imported cases:")
    for line in count_new_imported_cases(sim):
        print(line)


if __name__ == "__main__":
    main()
