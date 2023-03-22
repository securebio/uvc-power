from collections.abc import Callable
from dataclasses import dataclass

Curve = Callable[[int], float]


@dataclass
class DiseaseState:
    name: str
    succeptibility: Curve
    infectiousness: Curve
    shedding: Curve


class Person:
    def __init__(self, initial_state: DiseaseState, start_day: int):
        self.history = [(initial_state, start_day)]

    def add_state(self, new_state: DiseaseState, day: int):
        self.history.append((new_state, day))

    def get_current_state(self):
        return self.history[-1][0]

    def get_state_on_day(self, day: int):
        state, start_day = self.history[0]
        if day < start_day:
            raise Exception
        for s, d in self.history[1:]:
            if day < d:
                return state
            else:
                state = s
        else:
            return state


if __name__ == "__main__":
    s = DiseaseState(
        "susceptible",
        lambda d: 1.0,
        lambda d: 0.0,
        lambda d: 0.0,
    )
    i = DiseaseState("infected", lambda d: 1.0, lambda d: 1.0, lambda d: 1.0)
    p = Person(s, 0)
    print(p.get_current_state())
    p.add_state(i, 4)
    print(p.get_current_state())
    print(p.get_state_on_day(1))
    print(p.get_state_on_day(4))
    print(p.get_state_on_day(5))
