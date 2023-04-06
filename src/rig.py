import json
from dataclasses import dataclass
from enum import Enum
from itertools import accumulate, chain, cycle, islice
from math import exp, pi, sqrt
from pathlib import Path
from random import random
from typing import Callable, Iterable, Optional


class Shift(str, Enum):
    """
    An enumeration that represents a worker's shift (either "on" or "off").

    Attributes:
    - ON: A worker's shift on the rig.
    - OFF: A worker's shift off the rig (on the mainland).
    """

    ON = "on"
    OFF = "off"


class InfectionStatus(str, Enum):
    """
    An enumeration that represents a worker's infection status.

    Attributes:
    - S: A worker who is susceptible to infection.
    - E: A worker who has been exposed to the virus but is not yet infectious.
    - I: A worker who is currently infectious.
    - R: A worker who has recovered from the virus.
    """

    S = "susceptible"
    E = "exposed"
    I = "infectious"  # noqa: E741
    R = "recovered"


@dataclass
class Worker:
    """
    A worker on the oil rig.

    Attributes:
    - shift: The current shift of the worker.
    - shift_changed_on: The time (in days) when the worker last changed shift.
    - infection_status: The current infection status of the worker.
    - infection_status_changed_on: The time (in days) when the worker last
        changed infection status.
    """

    shift: Shift
    shift_changed_on: int
    infection_status: InfectionStatus
    infection_status_changed_on: int


Crew = list[Worker]


@dataclass
class ScheduleEntry:
    """
    A single entry in the schedule for worker shifts.

    Attributes:
    - length: The length (in days) of the shift.
    - next_shift: The shift that follows this one.
    """

    length: int
    next_shift: Shift


Schedule = dict[Shift, ScheduleEntry]


def change_shift(worker: Worker, day: int, sched: Schedule) -> Worker:
    """
    Changes the shift of a worker on the oil rig, based on the current day and
        the worker's schedule.

    Args:
    - worker: The worker whose shift is being changed.
    - day: The current day.
    - sched: The worker's schedule.

    Returns:
    - The worker after their shift has potentially changed.
    """
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
    """
    Expose a worker to the virus, based on the current day and the infection rate
        for their shift.

    Args:
    - w: The Worker object representing the worker being exposed.
    - day: The current day.
    - infection_rates: The RateMap object representing the infection rate for
        each shift.

    Returns:
    - The worker after potential exposure.
    """
    if w.infection_status == InfectionStatus.S and random() <= infection_rates[w.shift]:
        return Worker(w.shift, w.shift_changed_on, InfectionStatus.E, day)
    else:
        return w


def update_infections(w: Worker, day: int, t_inf: int, t_rec: int) -> Worker:
    """
    Update the infection status of a worker based on the current day and the
        duration of each infection stage.

    Args:
    - w: The worker whose infection status is being updated.
    - day: The current day.
    - t_inf: The duration of the infectious stage.
    - t_rec: The total duration of infection (from exposure to recovery).

    Returns:
    - The worker after their infection status has potentially changed.
    """
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
    """Count the number of workers on a given shift."""
    return sum(w.shift == shift for w in crew)


def count_status(
    crew: Crew, status: InfectionStatus, shift: Optional[Shift] = None
) -> int:
    """Count the number of workers in the crew with the given infection status.

    If shift is not None, only count workers on that shift.
    """
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


def _initialize_crew(crew_size: int, sched: Schedule, t_change: int) -> Crew:
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
    """Run a simulation of virus spread among workers on an oil rig.

    Args:
        n_days: The number of days to simulate.
        crew_size: The size of the crew.
        mainland_infection_rate: A function that takes the number of days
            as input and returns representing the probability that a worker
            returning from the mainland is infected.
        r0: The basic reproduction number of the virus.
        t_inf: The number of days it takes for a worker to
            transition from the exposed state to the infectious state.
        t_rec: The number of days from initial exposure to recovery.
        days_on: The number of days a worker spends on the rig
            before rotating to the mainland.
        days_off: The number of days a worker spends on the mainland
            before rotating back to the rig.
        t_change: The number of days between shift changes on the rig.

    Returns:
        A SimulationResult object containing the state of the crew on each day.
    """
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

    crew = _initialize_crew(crew_size, schedule, t_change)
    days = range(1, n_days)
    return list(accumulate(days, _step, initial=crew))


def tests_positive(w: Worker) -> bool:
    """Return True if a worker is on the rig and Infectious."""
    return w.shift == Shift.ON and w.infection_status == InfectionStatus.I


def count_first_positive_tests(
    sim: SimulationResult,
    test_frequency: int,
) -> Iterable[int]:
    """
    Count the number of new positive tests on each day of the simulation.

    Args:
        sim: The result of a completed simulation.
        test_frequency: The number of days between tests.

    Returns:
        The number of new positive tests each day.
    """
    test_days = range(0, len(sim), test_frequency)
    return (
        sum(
            tests_positive(w_now) and not tests_positive(w_past)
            for (w_now, w_past) in zip(sim[crew_now], sim[crew_past])
        )
        for crew_now, crew_past in zip(test_days, test_days[1:])
    )


def _gaussian_infection_rates(
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
    """
    Run a simulation of viral cases in a crew on an oil rig.

    Args:
        duration: The length of time (in days) of the wave of infections on the
            mainland.
        peak: The day of the peak infection rate on the mainland.
        total_prev: The total proportion of people on the mainland infected
            over the course of the wave.
        t_samps: A list of integers representing frequencies when tests are taken to
            determine whether a person has been infected.
        **params: Keyword arguments for `run_simulation()` function.

    Returns:
        A list of integers where the first element is the number of imported cases
        and the remaining elements represent the number of positive cases
        discovered at each of the specified test frequencies.
    """
    infection_rate = _gaussian_infection_rates(duration, peak, total_prev)
    sim = run_simulation(mainland_infection_rate=infection_rate, **params)
    return [sum(count_first_positive_tests(sim, t_samp)) for t_samp in t_samps]


@dataclass
class Virus:
    """Class representing a virus.

    Attributes:
        name: The name of the virus.
        r0: The basic reproduction number of the virus.
        t_inf: The number of days between exposure and becoming infectious.
        t_rec: The number of days between initial exposure and recovery.
        total_prev: The total prevalence of the virus.
        duration: The duration of the virus outbreak.
        peak: The day of the outbreak when the virus reaches its peak prevalence.
    """

    name: str
    r0: float
    t_inf: int
    t_rec: int
    total_prev: float
    duration: float
    peak: float


def load_viruses(filepath: Path, **kwargs) -> list[Virus]:
    """Loads a list of Virus objects from a JSON file.

    Args:
        filepath: A Path object pointing to the location of the JSON file.
        **kwargs: Additional keyword arguments to be passed to each Virus object.

    Returns:
        A list of Virus objects.
    """

    with open(filepath) as f:
        data = json.load(f)
    return [Virus(**entry, **kwargs) for entry in data]


def sim_multiple_viruses(
    viruses: list[Virus], reduction_factor: float, t_samps: list[int], **params
):
    """Simulate multiple viruses and returns the total number of cases for each
        time step.

    Args:
        viruses: A list of Virus objects.
        reduction_factor: The reduction factor to be applied to the basic
            reproduction number of each virus.
        t_samps: A list of sampling frequencies for which to count the number of
            cases.
        **params: Additional keyword arguments to be passed to each simulation.

    Returns:
        A list of integers representing the total number of cases for each
            sampling frequency.
    """

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
    infection_rate = _gaussian_infection_rates(duration, peak, total_prev)
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

    print("First positive tests at 1,3,7 days:")
    print(*(sum(count_first_positive_tests(sim, t_samp)) for t_samp in [1, 3, 7]))


if __name__ == "__main__":
    main()
