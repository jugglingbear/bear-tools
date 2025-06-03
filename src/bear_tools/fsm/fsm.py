from enum import Enum
from typing import Callable, Generic, TypeVar

State = TypeVar("State", bound=Enum)  # State type
Input = TypeVar("Input", bound=Enum)  # Input type


class FSM(Generic[State, Input]):
    """Generic Finite State Machine"""

    def __init__(self, initial: State, transitions: dict[tuple[State, Input | None], State]) -> None:
        """
        Initializer

        :param initial: The FSM's initial state
        :param transitions: A table of all possible transitions that the FSM can take
        """

        self.state: State = initial
        self._input_handlers: dict[Input, Callable[[], None]] = {}
        self._transitions: dict[tuple[State, Input | None], State] = transitions


    def transition(self, action: Input) -> State:
        """
        Get the next state in the FSM given an input

        :param action: The action to take from the current state
        :raises ValueError: If FSM is unable to transition to next state
        """

        key: tuple[State, Input] = (self.state, action)
        if key not in self._transitions:
            raise ValueError(f"Invalid transition: {self.state.name} + {action.name}")

        next_state: State = self._transitions[key]
        self.state = next_state

        if action in self._input_handlers:
            self._input_handlers[action]()

        return self.state


    def bind_input_handler(self, action: Input, callback: Callable[[], None]) -> None:
        """
        Associate a callback with an FSM input

        :param action: An FSM input
        :param callback: A function to call when the FSM transitions on {action}
        """

        self._input_handlers[action] = callback
