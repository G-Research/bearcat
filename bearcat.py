"""
Proof-of-concept, based on tracing.
"""

import sys
import os
import importlib
import contextvars
from pathlib import Path


def _to_pandas_from_modin(obj):
    """
    Convert Modin DataFrame etc. to a Pandas DataFrame.
    """
    from modin.utils import to_pandas

    return to_pandas(obj)


def _to_pandas_from_pandas(obj):
    """
    Convert Pandas DataFrame etc. to a Pandas DataFrame.

    A no-op, in short.
    """
    return obj


# Track whether the current call is in a Pandas call, as a list (a stack,
# really) of booleans.
_in_pandas_call_context = contextvars.ContextVar("in_pandas_call")


def _add_call_to_stack(in_pandas: bool):
    """
    Add whether current function is in Pandas-alike.
    """
    try:
        stack = _in_pandas_call_context.get()
    except contextvars.LookupError:
        stack = []
        _in_pandas_call_context.set(stack)
    stack.append(in_pandas)


def _remove_call_from_stack():
    """
    We've returned from function, so pop it off the stack.
    """
    _in_pandas_call_context.get().pop()


def _has_ancestor_pandas_call() -> bool:
    """
    Return whether the _parent_ or its parents are a Pandas API.

    If the current function only is in Pandas, that doesn't count.
    """
    in_pandas = _in_pandas_call_context.get([])
    if not in_pandas:
        # This is top-level traced call, therefore not in Pandas:
        return False

    # Iterate over ancestors, starting with parent, then grandparent, etc.:
    for ancestor_in_pandas in reversed(in_pandas[:-1]):
        if ancestor_in_pandas:
            return True

    # No ancestor was in Pandas-alike:
    return False


class DumpPandasResults:
    """
    Dump results from Pandas-like API calls to a file.
    """

    def __init__(self, pandas_module_name):
        self.pandas = importlib.import_module(pandas_module_name)
        # TODO We assume it's a package...
        self.pandas_dir = Path(self.pandas.__file__).absolute().parent()
        self.to_pandas = {
            "pandas": _to_pandas_from_pandas,
            "modin.pandas": _to_pandas_from_modin,
        }[pandas_module_name]

    def trace(self):
        """
        Start tracing.
        """
        # TODO threading?
        sys.setprofile(self._tracer)

    def _tracer(self, frame, event, arg):
        """
        Passed to sys.profile(), will get called on tracing events.

        For function returns, if the function is in the chosen Pandas package
        _and_ no parent caller was in Pandas-alike, pickle the result to disk
        as an actual-Pandas DataFrame.
        """
        # Is this API call inside the Pandas-alike?
        in_pandas = (
            Path(frame.f_code.co_filename).absolute().is_relative_to(self.pandas_dir)
        )

        # On function entry, add in-Pandas status to stack:
        if event in ("call", "c_call"):
            _add_call_to_stack(in_pandas)

        # On function return, first dump return result if we're inside Pandas
        # call, but none of ancestors are, i.e. top level Pandas API call.
        if event in ("return", "c_return"):
            if in_pandas and not _has_ancestor_pandas_call():
                # We should record this.
                self._dump(arg)
            # Remove in-Pandas status from stack, since this function is
            # returning:
            _remove_call_from_stack()

        # Continue tracing:
        return self._tracer


def _setup():
    pandas_module_name = os.env["BEARCAT_PANDAS"]

    # Setup the logic:
    global _dumper
    _dumper = DumpPandasResults(pandas_module_name)

    # Expose the Pandas-like module:
    global pandas
    pandas = _dumper.pandas

    # Start tracing:
    _dumper.trace()


_setup()


__all__ = ["pandas"]
