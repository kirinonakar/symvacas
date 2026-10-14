"""Scoped execution limits and cooperative service cancellation."""
import sys
import time
from threading import get_ident
from contextlib import contextmanager
from contextvars import ContextVar

_active_budget = ContextVar("symvacas_active_budget", default=None)

class SolverTimeLimit(BaseException):
    """Stop one symbolic solver without swallowing request cancellation."""

@contextmanager
def solver_phase(seconds):
    budget=_active_budget.get()
    if budget is None:
        with Budget(seconds=max(60,seconds+1)) as local:
            with solver_phase(seconds): yield
        return
    previous=budget.phase_deadline
    budget.phase_deadline=min(previous,time.monotonic()+seconds)
    try:
        budget.check()
        yield
        budget.check()
    finally:
        budget.phase_deadline=previous


class ExecutionStopped(BaseException):
    """Escape CAS routines which catch Exception and retry expensive work."""


class Budget:
    def __init__(self, seconds=8, steps=3000000, control=None):
        self.deadline = time.monotonic() + seconds
        self.steps = steps
        self.cancelled = control.isCancelled if control is not None else None
        self.tool_id = None
        self.tracing = False
        self.owner = get_ident()
        self.ticks = 256
        self.phase_deadline = float("inf")
        self.active_token = None

    def check(self):
        if self.cancelled is not None and self.cancelled():
            self.stop()
            raise ExecutionStopped("Calculation cancelled")
        if self.steps <= 0 or time.monotonic() > self.deadline:
            self.stop()
            raise ExecutionStopped("Computation limit reached. Reduce expression complexity.")
        if time.monotonic() > self.phase_deadline:
            raise SolverTimeLimit("Symbolic solver time limit reached")

    def tick(self, code, offset):
        # Monitoring is interpreter-wide; requests only own their worker thread.
        if get_ident() != self.owner:
            return
        self.steps -= 1
        self.ticks -= 1
        if self.ticks == 0:
            self.ticks = 256
            self.check()

    def jump(self, code, offset, destination):
        # Backward jumps cover loops, including `while True: pass` on one line.
        if destination <= offset:
            self.tick(code, offset)

    def trace(self, frame, event, arg):
        self.tick(None, 0)
        return self.trace

    def __enter__(self):
        self.check()
        self.active_token=_active_budget.set(self)
        monitoring = getattr(sys, "monitoring", None)
        if monitoring is not None:
            for tool_id in (5, 4, 3, 2, 1, 0):
                try:
                    monitoring.use_tool_id(tool_id, "symvacas-budget")
                except ValueError:
                    continue
                self.tool_id = tool_id
                try:
                    monitoring.register_callback(tool_id, monitoring.events.PY_START, self.tick)
                    monitoring.register_callback(tool_id, monitoring.events.JUMP, self.jump)
                    # Function entries and loop backedges bound Python work without
                    # calling into a Python trace hook on every source line/return.
                    monitoring.set_events(tool_id, monitoring.events.PY_START | monitoring.events.JUMP)
                except BaseException:
                    self.stop()
                    raise
                return self
        self.previous_trace = sys.gettrace()
        self.tracing = True
        sys.settrace(self.trace)
        return self

    def stop(self):
        if self.active_token is not None:
            _active_budget.reset(self.active_token)
            self.active_token=None
        if self.tool_id is not None:
            tool_id, self.tool_id = self.tool_id, None
            monitoring = sys.monitoring
            monitoring.set_events(tool_id, 0)
            monitoring.register_callback(tool_id, monitoring.events.PY_START, None)
            monitoring.register_callback(tool_id, monitoring.events.JUMP, None)
            monitoring.free_tool_id(tool_id)
        if self.tracing:
            self.tracing = False
            sys.settrace(self.previous_trace)

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        if exc_type is None:
            self.check()
