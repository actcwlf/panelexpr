import unittest
from panelexpr._utils.utils import *
from panelexpr import eval as t_eval


THRESHOLD = 1e-6


class BasicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv("../data/sample_zh_2.csv")

    def test_add(self):
        s1 = t_eval("Open + Close", data=self.data)
        s2 = self.data["Open"] + self.data["Close"]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)

    def test_sub(self):
        s1 = t_eval("Open - Close", data=self.data)
        s2 = self.data["Open"] - self.data["Close"]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)

    def test_mul(self):
        s1 = t_eval("Open * Close", data=self.data)
        s2 = self.data["Open"] * self.data["Close"]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)
#
    def test_div(self):
        s1 = t_eval("Open / Close", data=self.data)
        s2 = self.data["Open"] / self.data["Close"]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)

    def test_complex(self):
        s1 = t_eval("Open / (Close - High)", data=self.data)
        s2 = self.data["Open"] / (self.data["Close"] - self.data["High"])
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)

    def test_rolling_mean(self):
        s1 = t_eval("mmean(Open, 2, group_by='windcode')", data=self.data)
        df = self.data.groupby("windcode").apply(lambda df: df["Open"].rolling(2).mean()).reset_index()
        s2 = df["Open"]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)

    def test_rolling_mean_global_params(self):
        s1 = t_eval("ma(Open, 2)", group_tag="windcode", data=self.data)
        df = self.data.groupby("windcode").apply(lambda df: df["Open"].rolling(2).mean()).reset_index()
        s2 = df["Open"]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)

    def test_rolling_max(self):
        s1 = t_eval("mmax(Open, 2)", group_tag="windcode", data=self.data)
        df = self.data.groupby("windcode").apply(lambda df: df["Open"].rolling(2).max()).reset_index()
        s2 = df["Open"]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)

    def test_rolling_min(self):
        s1 = t_eval("mmin(Open, 2)", group_tag="windcode", data=self.data)
        df = self.data.groupby("windcode").apply(lambda df: df["Open"].rolling(2).min()).reset_index()
        s2 = df["Open"]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)

    def test_rolling_mean_overflow(self):
        s1 = t_eval("mmean(Open, 10)", group_tag="windcode", data=self.data)
        df = self.data.groupby("windcode").apply(lambda df: df["Open"].rolling(10).mean()).reset_index()
        s2 = df["Open"]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD or matching)

    def test_rolling_std(self):
        s1 = t_eval("mstd(Open, 2)", group_tag="windcode", data=self.data)
        df = self.data.groupby("windcode").apply(lambda df: df["Open"].rolling(2).std()).reset_index()
        s2 = df["Open"]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)

    def test_rolling_cov(self):
        s1 = t_eval("mcov(Open, Close, 2)", group_tag="windcode", data=self.data)
        df = self.data.groupby("windcode").apply(lambda df: df["Open"].rolling(2).cov(df["Close"].rolling(2))).reset_index()
        s2 = df[0]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)

    def test_rolling_corr(self):
        s1 = t_eval("mcorr(Open, Close, 2)", group_tag="windcode", data=self.data)
        df = self.data.groupby("windcode").apply(lambda df: df["Open"].rolling(2).corr(df["Close"].rolling(2))).reset_index()
        s2 = df[0]
        v = mean_absolute_deviation(s1, s2)
        self.assertTrue(v < THRESHOLD)

    def test_ewma(self):
        s1 = t_eval("ewm(Open, 2)", group_tag="windcode", data=self.data)
        df = self.data.groupby("windcode").apply(lambda d: d["Open"].ewm(span=2, min_periods=1).mean()).reset_index()
        s2 = df["Open"]
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)

    def test_rank(self):
        def fun(df):
            df["or"] = df["Open"].rank()
            return df

        data = self.data.sort_values(["Date", "windcode"])
        data["s1"] = s1 = t_eval("rank(Open)", time_tag="Date", data=data)
        data["s2"] = s2 = data.groupby("Date").apply(fun)["or"]
        # print(data[["Date", "windcode", "Open", "s1", "s2"]])
        # print(data)
        v = mean_absolute_deviation(s1, s2)
        matching = nan_matching(s1, s2)
        self.assertTrue(v < THRESHOLD)
        self.assertTrue(matching)


class NanTest(BasicTest):
    @classmethod
    def setUpClass(cls):
        cls.data = pd.read_csv("../data/sample_zh_3.csv")


if __name__ == '__main__':
    unittest.main()

