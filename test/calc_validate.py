import pandas as pd
import numpy as np
import unittest
from panelexpr.boost.calc import *


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.data = pd.DataFrame({
            "a1": pd.Series(np.random.rand(20)),
            "a2": pd.Series(np.random.rand(20)),
        })

    def test_corr(self):
        v1 = self.data["a1"].corr(self.data["a2"])
        v2 = corr(self.data["a1"].to_numpy(), self.data["a2"].to_numpy())
        self.assertTrue(np.abs(v1 - v2) < 1e-6)  # 测试用例

    def test_cov(self):
        v1 = self.data["a1"].cov(self.data["a2"])
        v2 = cov(self.data["a1"].to_numpy(), self.data["a2"].to_numpy())
        print(v1)
        print(v2)
        self.assertTrue(np.abs(v1 - v2) < 1e-6)

    def test_rolling_mean(self):
        v1 = self.data["a1"].rolling(5).mean()
        v2 = rolling_mean(self.data["a1"].to_numpy(), 5)
        v = np.abs(v1 - v2).mean()
        self.assertTrue(v < 1e-6)

        v1 = self.data["a1"].rolling(30).mean()
        v2 = rolling_mean(self.data["a1"].to_numpy(), 30)
        v = np.abs(v1 - v2).mean()
        self.assertTrue(v < 1e-6 or pd.isnull(v))

    def test_rolling_var(self):
        v1 = self.data["a1"].rolling(5).var()
        v2 = rolling_var(self.data["a1"].to_numpy(), 5)
        v = np.abs(v1 - v2).mean()
        self.assertTrue(v < 1e-6)

    def test_rolling_cov(self):
        v1 = self.data["a1"].rolling(5).cov(self.data["a2"].rolling(5))
        v2 = rolling_cov(self.data["a1"].to_numpy(), self.data["a2"].to_numpy(), 5)

        v = np.abs(v1 - v2).mean()
        self.assertTrue(v < 1e-6)

    def test_rolling_corr(self):
        v1 = self.data["a1"].rolling(5).corr(self.data["a2"].rolling(5))
        v2 = rolling_corr(self.data["a1"].to_numpy(), self.data["a2"].to_numpy(), 5)
        v = np.abs(v1 - v2).mean()
        self.assertTrue(v < 1e-6)

    def test_ewma(self):
        v1 = self.data["a1"].ewm(span=3, adjust=False).mean()
        v2 = ewma(self.data["a1"].to_numpy(), 3)
        print(v1, v2)
        v = np.abs(v1 - v2).mean()
        print(v)
        self.assertTrue(v < 1e-6)


class NanTest(Test):
    @classmethod
    def setUpClass(self):
        self.data = pd.DataFrame({
            "a1": pd.Series(np.random.rand(20)),
            "a2": pd.Series(np.random.rand(20)),
        })

        self.data['a1'][:2] = np.nan
        self.data['a1'][10] = np.nan


if __name__ == '__main__':
    unittest.main()

