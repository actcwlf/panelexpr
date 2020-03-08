from panelexpr import TimeSeriesOperator
import panelexpr as pe
import pandas as pd


class MyMovingAverageOperator(TimeSeriesOperator):
    def eval(self, series: pd.Series, window):  # all udo must implement this method
        s = series.rolling(window).mean()
        return s


pe.register("my_ma", MyMovingAverageOperator)  # register the operator

data = pd.read_csv("data/sample_zh_2.csv")
s2 = pe.eval("my_ma(Open, 2)", data=data, group_tag="windcode")

# equivalent to
# data.groupby("windcode").rolling(2).mean()["Open"].reset_index(drop=True).rename()
