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

        self._state: State = initial
        self._transitions: dict[tuple[State, Input | None], State] = transitions

        self._input_handlers: dict[Input, Callable[..., None]] = {}
        self._current_state_handler: Callable[..., State] | None = None
        self._jump_to_state_handler: Callable[[State], bool] | None = None


    @property
    def state(self) -> State:
        """
        Get the current state
        """

        if self._current_state_handler is not None:
            return self._current_state_handler()
        return self._state


    def jump_to_state(self, state: State) -> bool:
        """
        Jump directly to a specific state
        """

        success: bool = True
        if self._jump_to_state_handler is not None:
            success = self._jump_to_state_handler(state)
            if success:
                self._state = state
        else:
            self._state = state
        return success


    def transition(self, action: Input | None) -> State:
        """
        Get the next state in the FSM given an input

        :param action: The action to take from the current state
        :raises ValueError: If FSM is unable to transition to next state
        """

        key: tuple[State, Input | None] = (self.state, action)
        if key not in self._transitions:
            raise ValueError(f"Invalid transition: {self.state.name} + {action.name if action is not None else None}")

        next_state: State = self._transitions[key]
        self._state = next_state
        if action in self._input_handlers:
            self._input_handlers[action]()

        # Check for epsilon transitions
        previous_state: State = self.state
        while (key := (self.state, None)) in self._transitions:
            next_state = self._transitions[key]
            self._state = next_state
            if action in self._input_handlers:
                self._input_handlers[action]()
            if previous_state == self.state:
                break
            previous_state = self.state

        return self.state


    def register_input_callback(self, action: Input, callback: Callable[..., None]) -> None:
        """
        Register a function to be called whenever the FSM transitions on a specific Input

        :param action: An FSM input
        :param callback: A function to call when the FSM transitions on {action}
        """

        self._input_handlers[action] = callback


    def register_get_state_callback(self, callback: Callable[..., State] | None) -> None:
        """
        Register a function to be used to determine the FSM's current state rather than the default action of
        inspecting self._state

        Note: Setting the value to None returns system to default behavior
        """

        self._current_state_handler = callback


    def register_jump_to_state_callback(self, callback: Callable[[State], bool] | None) -> None:
        """
        Register a function to be called whenever jumping directly to a state in the FSM

        Note: Setting the value to None returns system to default behavior
        """

        self._jump_to_state_handler = callback
