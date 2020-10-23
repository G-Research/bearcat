from bearcat import pandas as pd


def main():
    # TODO for __init__ we actually need to pickle self, rather than the
    # result...
    df = pd.DataFrame(
        {"a": [1, 2, 3, 1], "b": [4, 5, 6, 7], "s": ["hello", "world", "Bar", "foo"]}
    )
    # Very simple call
    df2 = df.sum()
    # TODO do variations in __str__/__repr__ really merit comparison?
    print(df2)
    # TODO groupby() is harder, Modin has no Pandas conversion at the moment
    # counts = df.groupby("a").count()
    # df2 = df[["b", "s"]]
    # TODO comparing written files is not currently handled...
    # df2.to_csv("/tmp/out.csv")


if __name__ == "__main__":
    main()
