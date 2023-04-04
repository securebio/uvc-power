import json
from dataclasses import dataclass
from enum import Enum
from itertools import accumulate, chain, cycle, islice
from math import exp, pi, sqrt
from pathlib import Path
from random import random
from typing import Callable, Iterable, Optional


class Shift(str, Enum):
    ON = 1
    OFF = 2


class InfectionStatus(Enum):
    S = 1
    E = 2
    I = 3  # noqa: E741
    R = 4


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


def expose(w: Worker, day: int, infection_rates: RateMap) -> Worker:
    if w.infection_status == InfectionStatus.S and random() <= infection_rates[w.shift]:
        return Worker(w.shift, w.shift_changed_on, InfectionStatus.E, day)
    else:
        return w


def update_infections(w: Worker, day: int, t_inf: int, t_rec: int) -> Worker:
    if (
        w.infection_status == InfectionStatus.E
        and day - w.infection_status_changed_on >= t_inf
    ):
        return Worker(w.shift, w.shift_changed_on, InfectionStatus.I, day)
    elif (
        w.infection_status == InfectionStatus.I
        and day - w.infection_status_changed_on >= t_rec - t_inf
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
        (not shift or w.shift == shift) and w.infection_status == status for w in crew
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
InfectionCurve = Callable[[int], float]


def run_simulation(
    n_days: int,
    crew_size: int,
    mainland_infection_rate: InfectionCurve,
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
        changed = (change_shift(w, day, schedule) for w in c)
        updated = [update_infections(w, day, t_inf, t_rec) for w in changed]
        rates = _infection_rates(updated, day)
        return [expose(w, day, rates) for w in updated]

    crew = initialize_crew(crew_size, schedule, t_change)
    days = range(1, n_days)
    return list(accumulate(days, _step, initial=crew))


def tests_positive(w: Worker) -> bool:
    return w.shift == Shift.ON and w.infection_status == InfectionStatus.I


def count_first_positive_tests(
    sim: SimulationResult,
    test_frequency: int,
) -> Iterable[int]:
    test_days = range(0, len(sim), test_frequency)
    return (
        sum(
            tests_positive(w_now) and not tests_positive(w_past)
            for (w_now, w_past) in zip(sim[crew_now], sim[crew_past])
        )
        for crew_now, crew_past in zip(test_days, test_days[1:])
    )


def new_imported_case(w: Worker, d: int) -> bool:
    return (
        w.infection_status in [InfectionStatus.E, InfectionStatus.I]
        and w.shift_changed_on == d
    )


def count_new_imported_cases(sim: SimulationResult) -> Iterable[int]:
    return (sum(new_imported_case(w, d) for w in crew) for d, crew in enumerate(sim))


def gaussian_infection_rates(
    duration: float, peak: float, total_prevalence: float
) -> InfectionCurve:
    sigma = duration / 8
    return (
        lambda d: total_prevalence
        * exp(-(((d - peak) / sigma) ** 2) / 2)
        / (sqrt(2 * pi) * sigma)
    )


def sim_cases(
    duration: float, peak: float, total_prev: float, t_samps: list[int], **params
):
    infection_rate = gaussian_infection_rates(duration, peak, total_prev)
    sim = run_simulation(mainland_infection_rate=infection_rate, **params)
    return [sum(count_new_imported_cases(sim))] + [
        sum(count_first_positive_tests(sim, t_samp)) for t_samp in t_samps
    ]


@dataclass
class Virus:
    name: str
    r0: float
    t_inf: int
    t_rec: int
    total_prev: float
    duration: float
    peak: float


def load_viruses(filepath: Path, **kwargs) -> list[Virus]:
    with open(filepath) as f:
        data = json.load(f)
    return [Virus(**entry, **kwargs) for entry in data]


def sim_multiple_viruses(
    viruses: list[Virus], reduction_factor: float, t_samps: list[int], **params
):
    cases = (
        sim_cases(
            v.duration,
            v.peak,
            v.total_prev,
            t_samps,
            r0=v.r0 * reduction_factor,
            t_inf=v.t_inf,
            t_rec=v.t_rec,
            **params
        )
        for v in viruses
    )
    return [sum(x) for x in zip(*cases)]


def main():
    duration = 60
    peak = duration / 2
    total_prev = 0.20
    infection_rate = gaussian_infection_rates(duration, peak, total_prev)
    print([infection_rate(d) for d in range(duration)])

    params = dict(
        n_days=180,
        crew_size=120,
        mainland_infection_rate=infection_rate,
        r0=2.5,
        t_inf=2,
        t_rec=12,
        days_on=28,
        days_off=28,
        t_change=7,
    )
    sim = run_simulation(**params)
    for line in sim:
        print(
            "Exposed: ",
            count_status(line, InfectionStatus.E, Shift.ON),
            count_status(line, InfectionStatus.E, Shift.OFF),
        )
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

    print("New imported cases:")
    print(sum(count_new_imported_cases(sim)))
    print("First positive tests at 1,3,7 days:")
    print(*(sum(count_first_positive_tests(sim, t_samp)) for t_samp in [1, 3, 7]))


if __name__ == "__main__":
    main()
