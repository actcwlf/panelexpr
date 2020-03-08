import unittest
from panelexpr._utils.utils import *
from panelexpr.base.operator import TimeSeriesOperator
import panelexpr as pe
import pandas as pd


THRESHOLD = 1e-6


class MyMovingAverageOperator(TimeSeriesOperator):
    def eval(self, series: pd.Series, window):
        s = series.rolling(window).mean()
        return s


pe.register("my_ma", MyMovingAverageOperator)


class BasicTest(unittest.TestCase):  # 继承unittest.TestCase
    @classmethod
    def setUpClass(cls):
        # 必须使用@classmethod 装饰器,所有test运行前运行一次
        cls.data = pd.read_csv("data/sample_zh_2.csv")

    def test_rolling_mean(self):
        s1 = pe.eval("mmean(Open, 2, group_by='windcode')", data=self.data)
        s2 = pe.eval("my_ma(Open, 2)", data=self.data, group_tag="windcode")
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)


if __name__ == '__main__':
    unittest.main()  # 运行所有的测试用例

