# panelexpr
A simple panel data evaluator
## Installation

```bash
$ pip install panelexpr
```


## Usage
### Sample Data

sample_zh_2.csv:

| Date     | windcode  | Open        | High        | Low         | Close       | Volume    |
|  ----     | ----  | ----       | ----      | ----         | ----     | ----    |
| 20170913 | 000001.SZ | 1221.488009 | 1226.803448 | 1205.54169  | 1215.109481 | 668237.42 | 
| 20170914 | 000001.SZ | 1215.109481 | 1232.118888 | 1194.910811 | 1203.415514 | 883087.77 |
| 20170915 | 000001.SZ | 1200.22625  | 1203.415514 | 1185.34302  | 1200.22625  | 646094.81 |
| 20170918 | 000001.SZ | 1195.973899 | 1203.415514 | 1190.658459 | 1195.973899 | 607612.96 |
| 20170919 | 000001.SZ | 1195.973899 | 1205.54169  | 1177.901404 | 1183.216844 | 764212.62 |
| 20170913 | 000002.SZ | 3473.691392 | 3576.666433 | 3431.128374 | 3536.849417 | 467463.77 |
| 20170914 | 000002.SZ | 3539.595418 | 3852.639543 | 3508.016405 | 3783.989516 | 1150696.14|
| 20170915 | 000002.SZ | 3775.751513 | 4149.207662 | 3771.632511 | 4022.891612 | 1550495.61|
| 20170918 | 000002.SZ | 3983.074596 | 4083.303636 | 3843.028539 | 3849.893542 | 1063043.07|
| 20170919 | 000002.SZ | 3881.472555 | 4132.731656 | 3858.131546 | 3950.122582 | 1196308.5 |


load data
```python
import pandas as pd
data = pd.read_csv("../data/sample_zh_2.csv")
```

### Calculation

```python
import panelexpr as pe
pe.eval("ma(Open, 2)", data=data, group_tag="windcode")
```
```python
# equivalent to
data.groupby("windcode").rolling(2).mean()["Open"].reset_index(drop=True).rename()
```

Output:
```
0            NaN
1    1218.298745
2    1207.667866
3    1198.100075
4    1195.973899
5            NaN
6    3506.643405
7    3657.673466
8    3879.413054
9    3932.273575
dtype: float64
```
### User defined operator
```python
from panelexpr import TimeSeriesOperator

class MyMovingAverageOperator(TimeSeriesOperator):
    def eval(self, series: pd.Series, window) -> pd.Series: # all udo must implement this method
        s = series.rolling(window).mean()
        return s
        
pe.register("my_ma", MyMovingAverageOperator) # register the operator
pe.eval("my_ma(Open, 2)", data=data, group_tag="windcode")
```

