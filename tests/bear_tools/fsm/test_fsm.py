# pylint: disable=C0103
# mypy: disable-error-code=comparison-overlap

from enum import Enum

import pytest

from bear_tools.fsm import FSM


class State(Enum):
    """Test states"""

    START = 1
    PROCESSING = 2
    COMPLETED = 3
    FINISHED = 4


class Input(Enum):
    """Test inputs"""

    PROCESS = 1
    COMPLETE = 2


def test_initial_state() -> None:
    """Verify that setting initial state works"""

    fsm = FSM[State, Input](State.START, {})
    assert fsm.state == State.START


def test_register_input_callback() -> None:
    """Tests binding a callback to an FSM input and ensuring it is called on transition."""

    was_callback_called: bool = False

    def input_a_callback() -> None:
        nonlocal was_callback_called
        was_callback_called = True

    fsm = FSM[State, Input](
        State.START,
        {
            (State.START, Input.PROCESS): State.PROCESSING,
            (State.PROCESSING, Input.COMPLETE): State.COMPLETED,
        },
    )

    fsm.register_input_callback(Input.PROCESS, input_a_callback)
    fsm.transition(Input.PROCESS)
    assert was_callback_called


def test_register_jump_to_state_callback() -> None:
    """Tests that the jump-to-state handler works as expected"""

    def callback(state: State) -> bool:
        """Jump to state callback"""
        return not state == State.FINISHED

    fsm = FSM[State, Input](State.START, {})
    fsm.register_jump_to_state_callback(callback)

    assert fsm.jump_to_state(State.START) is True and fsm.state == State.START
    assert fsm.jump_to_state(State.PROCESSING) is True and fsm.state == State.PROCESSING
    assert fsm.jump_to_state(State.COMPLETED) is True and fsm.state == State.COMPLETED
    assert fsm.jump_to_state(State.FINISHED) is False and fsm.state != State.FINISHED


def test_register_get_state_callback() -> None:
    """Tests that the override mechanics for the get-current-state work as expected"""

    def get_state() -> State:
        """Get customized current state"""
        return next(states)

    states = iter([State.FINISHED, State.COMPLETED, State.PROCESSING, State.START])
    fsm = FSM[State, Input](State.START, {})
    fsm.register_get_state_callback(get_state)
    assert fsm.state == State.FINISHED
    assert fsm.state == State.COMPLETED
    assert fsm.state == State.PROCESSING
    assert fsm.state == State.START


def test_transition_valid() -> None:
    """Tests a valid transition from START to PROCESSING on ACTION_A"""

    fsm = FSM[State, Input](
        State.START,
        {
            (State.START, Input.PROCESS): State.PROCESSING,
            (State.PROCESSING, Input.COMPLETE): State.COMPLETED,
            (State.COMPLETED, None): State.FINISHED,
        },
    )
    next_state: State = fsm.transition(Input.PROCESS)
    assert next_state == State.PROCESSING
    assert fsm.state == State.PROCESSING
    next_state = fsm.transition(Input.COMPLETE)
    assert next_state == State.FINISHED  # Automatically transition from COMPLETE to FINISHED on epsilon input
    assert fsm.state == State.FINISHED


def test_transition_invalid() -> None:
    """Tests an invalid transition, which should raise a ValueError"""

    fsm = FSM[State, Input](
        State.START,
        {
            (State.START, Input.PROCESS): State.PROCESSING,
            (State.PROCESSING, Input.COMPLETE): State.COMPLETED,
        },
    )

    with pytest.raises(ValueError):
        fsm.transition(Input.COMPLETE)  # Attempt an invalid transition
