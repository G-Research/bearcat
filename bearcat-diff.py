"""
Prototype: compare two stream-o'-pickles files written by bearcat.
"""
import sys
import pickle
from typing import Iterable
from itertools import zip_longest

import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal, assert_index_equal
import numpy as np


class NotInFile:
    """
    Marker object indicating the file ended.
    """


def load_contents(filepath: str) -> Iterable:
    """
    Load pickles one a time, return as generator.
    """
    f = open(filepath, "rb")
    while True:
        try:
            result = pickle.load(f)
        except EOFError:
            return
        yield result


def main(file_path1: str, file_path2: str):
    """
    Load two files, compare their contents.

    Each file should be a series of pickled objects, mostly real-Pandas objects
    but potentially other types as well.
    """
    for obj1, obj2 in zip_longest(
        load_contents(file_path1), load_contents(file_path2), fillvalue=NotInFile()
    ):
        print(obj1, obj2)
        if isinstance(obj1, pd.DataFrame):
            assert_frame_equal(obj1, obj2)
        elif isinstance(obj1, pd.Series):
            assert_series_equal(obj1, obj2)
        elif isinstance(obj1, pd.Index):
            assert_index_equal(obj1, obj2)
        elif isinstance(obj1, np.ndarray):
            assert np.array_equal(obj1, obj2), f"{obj1} != {obj2}"
        else:
            assert obj1 == obj2, f"{obj1} != {obj2}"
    print("Everything looks the same, hurrah.")


if __name__ == "__main__":
    main(*sys.argv[1:])
