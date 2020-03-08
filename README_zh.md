panelexpr是一个专门用于简化面板数据处理的包，使用方法类似于`pandas.eval`，使用一个字符串描述要求值的公式。但不同之处在于panelexpr是针对面板数据进行设计，可以大大简化需要反复分组求值的表达式。
# 安装

```bash
$ pip install panelexpr
```


# 使用方法
## 示例数据

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
加载数据
```python
import pandas as pd
data = pd.read_csv(“sample_zh_2.csv")
```

### 计算

```python
import panelexpr as pe
data["Open_ma2"] = pe.eval("ma(Open, 2)", data=data, group_tag="windcode", time_tag="Date")
```
这里`ma()`称为运算符，也可以说是函数。它的第一个参数是列名，第二个为进行平均运算的时间窗口大小。所有继承自`TimeSeriesOperator`的算符使用方法都遵循这一模式。

`group_tag`和`time_tag`都是用于分组的标签，相当于`pandas.groupby`的参数。这两个标签对表达式中的所有运算符都是有效的。`panelexpr`会根据运算符自身的特性（时序操作还是截面操作）使用适当的分组方法。时序运算符会根据`group_tag`进行分组，截面运算符会根据`time_tag`进行分组。如果表达式中仅涉及其中一种运算符，可以不指定另一个参数。
```python
# 等价于
data["Open_ma2"] = data.groupby("windcode").rolling(2).mean()["Open"]
```

输出:
```
       Date   windcode         Open     Open_ma2
0  20170913  000001.SZ  1221.488009          NaN
1  20170914  000001.SZ  1215.109481  1218.298745
2  20170915  000001.SZ  1200.226250  1207.667866
3  20170918  000001.SZ  1195.973899  1198.100075
4  20170919  000001.SZ  1195.973899  1195.973899
5  20170913  000002.SZ  3473.691392          NaN
6  20170914  000002.SZ  3539.595418  3506.643405
7  20170915  000002.SZ  3775.751513  3657.673466
8  20170918  000002.SZ  3983.074596  3879.413054
9  20170919  000002.SZ  3881.472555  3932.273575
```
### 自定义运算
```python
from panelexpr import TimeSeriesOperator

class MyMovingAverageOperator(TimeSeriesOperator):
    def eval(self, series: pd.Series, window) -> pd.Series: # 所有的自定义运算需要实现此方法
        s = series.rolling(window).mean()
        return s
        
pe.register("my_ma", MyMovingAverageOperator) # 注册运算符
pe.eval("my_ma(Open, 2)", data=data, group_tag="windcode")
```
自定义运算符时要注意：
1. 必须继承自`TimeSeriesOperator`，`DoubleSeriesOperator`，`CrossSectionalOperator`。使用时也必须遵循相应的规则。
2. 自定义运算要实现`eval`方法。在实现中，不需要考虑分组操作，只需要当作单纯的时序数据或截面数据即可。返回序列长度需和输入序列长度一致且索引不变。
3. 注册后的算符才为可以在`pe.eval`中使用。

## 优势
### 直观易用
* 使用和`pd.eval`类似的公式描述方法
```python
pe.eval("(Open + Close) / Volume", data=data)
# 等价于
pd.eval("(data.Open + data.Close) / data.Volume")
```

* 通过使用自定义运算，可以方便地将适用于时间序列的运算应用于面板数据，例如移动平均，移动协方差等（示例见`demo/udo.py`）

* 简化复杂公式的描述

```python
# MACD
pe.eval("ema(Close, 12) - ema(Close, 26)", data=data, group_tag="windcode")
```
算符之间可以不受限制地嵌套

## 不足
不支持求和等聚合操作

## 目前已支持的运算
### 基础运算
`+, -, *, \`

### 单序列时序运算
**使用方法 `fun(col_name, window)`**，继承自`TimeSeriesOperator`


`shift` 时间轴移位

`ma` 移动平均

`mstd` 移动方差

`mmax` 窗口内的最大值

`mmin` 窗口内的最小值

`ema ` 指数移动平均

##双序列时序运算
**使用方法 `fun(col_name1, col_name2, window)`**，继承自`DoubleSeriesOperator`

`mcov` 移动协方差

`mcorr` 移动相关系数

### 截面运算
**使用方法 `fun(col_name)`**，继承自`CrossSectionalOperator`

`rank` 求排序位次值

