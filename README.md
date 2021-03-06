# Bearcat: Pandas logic validation

## Initial use cases

### Can you upgrade Pandas?

Your code is running with Pandas version X, now you want to upgrade to version X+1.
How do you know your code is still giving the same results?

### Can you switch implementations?

There are other implementations of Pandas: cuDF, Dask, Koalas, Modin.
Can you switch to another implementation and still get the same results?


## Try it out

Setup:

```bash
python3 -m venv venv
. venv/bin/activate
pip install modin[ray] pandas
```

Running:

```bash
BEARCAT_PANDAS=pandas python example.py
BEARCAT_PANDAS=modin.pandas python example.py
python bearcat-diff.py bearcat-output-modin.pandas.pkl bearcat-output-pandas.pkl 
```
