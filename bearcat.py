"""
Proof-of-concept, based on tracing.
"""

import sys
import os
import importlib
import pickle
from pathlib import Path


def _to_pandas_from_modin(obj):
    """
    Convert Modin DataFrame etc. to a Pandas DataFrame.
    """
    from modin.utils import to_pandas
    from modin.pandas import DataFrame, Series

    if isinstance(obj, (DataFrame, Series)):
        return to_pandas(obj)
    else:
        return obj


def _to_pandas_from_pandas(obj):
    """
    Convert Pandas DataFrame etc. to a Pandas DataFrame.

    A no-op, in short.
    """
    return obj


class DumpPandasResults:
    """
    Dump results from Pandas-like API calls to a file.
    """

    def __init__(self, pandas_module_name):
        self.pandas = importlib.import_module(pandas_module_name)
        self.pandas_dirs = {
            Path(self.pandas.__file__).resolve().parent,
            Path(importlib.import_module("pandas").__file__).resolve().parent,
        }

        self.to_pandas = {
            "pandas": _to_pandas_from_pandas,
            "modin.pandas": _to_pandas_from_modin,
        }[pandas_module_name]
        self.output = open(f"bearcat-output-{pandas_module_name}.pkl", "wb")

    def trace(self):
        """
        Start tracing.
        """
        # TODO threading?
        sys.setprofile(self._tracer)

    def _dump(self, obj):
        """
        Write an object to disk for later comparison.
        """
        pickle.dump(self.to_pandas(obj), self.output, pickle.HIGHEST_PROTOCOL)
        self.output.flush()

    def _is_top_level_pandas_call(self, frame) -> bool:
        """
        Return whether the frame is a top-level Pandas-like API, i.e. no parent
        calls were Pandas-like API.
        """

        def is_pandas(f):
            parents = Path(f.f_code.co_filename).resolve().parents
            for pandas_dir in self.pandas_dirs:
                if pandas_dir in parents:
                    return True

        if not is_pandas(frame):
            # Not a Pandas-like call.
            return False

        frame = frame.f_back
        while frame:
            if is_pandas(frame):
                # Parent call was also Pandas-like API, so not top-level call.
                return False
            frame = frame.f_back

        return True

    def _tracer(self, frame, event, arg):
        """
        Passed to sys.profile(), will get called on tracing events.

        For function returns, if the function is in the chosen Pandas package
        _and_ no parent caller was in Pandas-alike, pickle the result to disk
        as an actual-Pandas DataFrame.
        """
        # On function return, first dump return result if we're inside Pandas
        # call, but none of ancestors are, i.e. top level Pandas API call.
        if event == "c_return":
            # TODO Some public APIs may be C functions... Need to handle this
            # somehow. The arg however is the Python-level "builtin" function
            # itself, rather than the result, and the frame is the parent
            # Python frame. So dunno what to do.
            return

        if event == "return":
            # Handling attribute lookups is too tricky; sometimes it hits code,
            # sometimes it doesn't, so don't try.
            if self._is_top_level_pandas_call(frame) and not frame.f_code.co_name in (
                "__getattr__",
                "__getattribute__",
            ):
                # We should record this.
                print(f"DUMPING {frame.f_code.co_filename}:{frame.f_code.co_name}")
                self._dump(arg)

        # Continue tracing:
        return self._tracer


def _setup():
    pandas_module_name = os.environ["BEARCAT_PANDAS"]

    # Setup the logic:
    global _dumper
    _dumper = DumpPandasResults(pandas_module_name)

    # Expose the Pandas-like module:
    global pandas
    pandas = _dumper.pandas

    # Start tracing:
    _dumper.trace()


if not os.environ.get("BEARCAT_DISABLE_SETUP"):
    _setup()


__all__ = ["pandas"]
