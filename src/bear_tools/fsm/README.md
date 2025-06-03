# Finite State Machine (FSM)

This is a simple Finite State Machine implementation.
Below is an example of how to use it.

```python
from enum import Enum

from bear_tools.fsm import FSM


class State(Enum):
    """Example states"""
    START      = 1
    PROCESSING = 2
    COMPLETE   = 3
    ERROR      = 4


class Input(Enum):
    """Example inputs"""
    START_PROCESSING  = 1
    FINISH_PROCESSING = 2


fsm = FSM[State, Input](
    initial=State.START,
    transitions={
        (State.START,      Input.START_PROCESSING):  State.PROCESSING,
        (State.START,      Input.FINISH_PROCESSING): State.ERROR,
        (State.PROCESSING, Input.START_PROCESSING):  State.ERROR,
        (State.PROCESSING, Input.FINISH_PROCESSING): State.COMPLETE,
        (State.COMPLETE,   Input.START_PROCESSING):  State.ERROR,
        (State.COMPLETE,   Input.FINISH_PROCESSING): State.ERROR,
    }
)

print(f'fsm.state: {fsm.state}')  # output: fsm.state: State.START
fsm.transition(Input.START_PROCESSING)
print(f'fsm.state: {fsm.state}')  # output: fsm.state: State.PROCESSING
fsm.transition(Input.FINISH_PROCESSING)
print(f'fsm.state: {fsm.state}')  # output: fsm.state: State.COMPLETE
fsm.transition(Input.START_PROCESSING)
print(f'fsm.state: {fsm.state}')  # output: fsm.state: State.ERROR
```
