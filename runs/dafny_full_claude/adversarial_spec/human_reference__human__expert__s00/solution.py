from __future__ import annotations


def transition_state(state: str, event: str) -> str:
    transitions = {('idle', 'start'): 'running', ('running', 'stop'): 'idle', ('running', 'fail'): 'failed', ('failed', 'reset'): 'idle'}
    return transitions.get((state, event), state)
