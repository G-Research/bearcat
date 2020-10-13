# Designing Bearcat: a work in progress

## Initial usage sketch

Given initial code:

```python
import pandas as pd

def run():
    df = pd.from_csv("my.csv")
    intermediate_df = df.transform().another_transform()
    result = intermediate_df.more_transforms()
    result.to_csv("result.csv")

run()
```

We switch it to pluggable Pandas, and add some annotations:

```python
from bearcat import pandas as pd, record_value

def run():
    df = pd.from_csv("my.csv")
    record_value(initial=df)
    intermediate_df = df.transform().another_transform()
    record_value(intermediate=intermediate_df)
    result = intermediate_df.more_transforms()
    record_value(result=result)
    result.to_csv("result.csv")

run()
```

And then run a diff:

```shell-session
$ bearcat-diff --version-a pandas==1.1.0 --version-b=modin==0.8.1 yourscript.py
```

This will run the script twice, once with each library plugged in as `bearcat.pandas`, and then do a diff.

## Implementation discussions

### Supporting multiple libraries

Different versions of Pandas requires multiple virtualenvs.
In theory this is not the case for e.g. Modin vs Pandas, except in practice Modin requires a particular version of Pandas that not might match what the user is currently using.

How to do this nicely is a question.

### Tracking intermediate data

Conditionals and loops means just a naive recording of values will become hard to understand when the code gets larger.
A better model might be [Eliot's tree of actions](https://eliot.readthedocs.io/en/stable/quickstart.html); Eliot may well allow be a good basis for implementation.

### Integrating with ongoing user code development

Doing the annotation and changes once is fine, but... you upgrade from Pandas 1.0 to 1.1.
In three months you want to upgrade to 1.2—you shouldn't have to do all the annotation work from scratch.

There are two parts, the import and the annotation code.

#### Annotations (recording intermediate/final values)

* Using Eliot means annotation code is actually useful outside of Bearcat, just for debugging, though perhaps with a different output format.
  So could just leave that in, and point out the benefits, and try to minimize performance overhead if logging isn't needed.
* Get rid of explicit annotations, figure out way to hook into intermediate steps (specifically, external Pandas API calls.). This would also make debugging/diagnosing differences easier since it would be clear exactly where initial mismatching results are.

#### Pandas import

Some potential solutions:

1. Just have users do it each time.
   Not that much work, but error prone across multiple modules.
2. Have users rely on Bearcat for production use as well.
3. Change `sys.modules["pandas"]` to be Bearcat and then you can just stick to `import pandas`; this would likely break e.g. Modin, so probably not actually realistic.
4. Do a code transform that converts imports?!
5. try/except where it falls back to normal library if bearcat is unavailable.


## Next steps

Prototype tracing every call into Pandas API; basically "is this call into the Pandas-like library with no parents being in the Pandas-like library".
Specifically _don't_ care about other threads because Pandas API is single-threaded, and can start with that assumption and it'll cover majority of users (multi-threading on the backend is a thing, but that's beyond the abstraction boundary and not something we need to care about).
