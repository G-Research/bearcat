from bearcat import pandas as pd


def main():
    df = pd.DataFrame(
        {"a": [1, 2, 3, 1], "b": [4, 5, 6, 7], "s": ["hello", "world", "Bar", "foo"]}
    )
    # Simple call:
    counts = df.groupby("a").count()
    # TODO do variations in __str__/__repr__ really merit comparison?
    print(counts)
    df2 = df[["b", "s"]]
    # TODO comparing written files is not currently handled...
    df2.to_csv("/tmp/out.csv")


if __name__ == "__main__":
    main()
