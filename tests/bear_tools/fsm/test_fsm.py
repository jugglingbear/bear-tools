# pylint: disable=C0103

from enum import Enum

import pytest

from bear_tools.fsm import FSM


class State(Enum):
    """Test states"""
    START      = 1
    PROCESSING = 2
    COMPLETED  = 3
    FINISHED   = 4


class Input(Enum):
    """Test inputs"""
    INPUT_A = 1
    INPUT_B = 2


def test_initial_state() -> None:
    """Verify that setting initial state works"""

    fsm = FSM[State, Input](State.START, {})
    assert fsm.state == State.START


def test_register_get_state_callback() -> None:
    """Tests that the override mechanics for the get-current-state work as expected"""

    def get_state() -> State:
        """Get customized current state"""
        return next(states)

    states = iter([State.FINISHED, State.COMPLETED, State.PROCESSING, State.START])
    fsm = FSM[State, Input](State.START, {})
    fsm.register_get_state_callback(get_state)
    assert fsm.state == State.FINISHED
    assert fsm.state == State.COMPLETED   # type: ignore[comparison-overlap]
    assert fsm.state == State.PROCESSING
    assert fsm.state == State.START


def test_transition_valid() -> None:
    """Tests a valid transition from START to PROCESSING on ACTION_A"""

    fsm = FSM[State, Input](
        State.START,
        {
            (State.START,      Input.INPUT_A): State.PROCESSING,
            (State.PROCESSING, Input.INPUT_B): State.COMPLETED,
            (State.COMPLETED,  None):          State.FINISHED,
        }
    )
    next_state: State = fsm.transition(Input.INPUT_A)
    assert next_state == State.PROCESSING
    assert fsm.state == State.PROCESSING
    next_state = fsm.transition(Input.INPUT_B)
    assert next_state == State.COMPLETED
    assert fsm.state == State.COMPLETED  # type: ignore[comparison-overlap]
    next_state = fsm.transition(None)
    assert next_state == State.FINISHED
    assert fsm.state == State.FINISHED


def test_transition_invalid() -> None:
    """Tests an invalid transition, which should raise a ValueError"""

    fsm = FSM[State, Input](
        State.START,
        {
            (State.START,      Input.INPUT_A): State.PROCESSING,
            (State.PROCESSING, Input.INPUT_B): State.COMPLETED,
        }
    )

    with pytest.raises(ValueError):
        fsm.transition(Input.INPUT_B)  # Attempt an invalid transition


def test_register_input_handler() -> None:
    """Tests binding a callback to an FSM input and ensuring it is called on transition."""

    was_callback_called: bool = False

    def input_a_callback() -> None:
        nonlocal was_callback_called
        was_callback_called = True

    fsm = FSM[State, Input](
        State.START,
        {
            (State.START,      Input.INPUT_A): State.PROCESSING,
            (State.PROCESSING, Input.INPUT_B): State.COMPLETED,
        }
    )

    fsm.register_input_handler(Input.INPUT_A, input_a_callback)
    fsm.transition(Input.INPUT_A)
    assert was_callback_called
