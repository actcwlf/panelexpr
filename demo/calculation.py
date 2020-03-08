import pandas as pd
import panelexpr as pe

data = pd.read_csv("../data/sample_zh_2.csv")
print(pe.eval("ma(Open, 2, group_by='windcode')", data=data))

# or pe.eval("ma(Open, 2)", data=data, group_tag="windcode")

# equivalent to
# data.groupby("windcode").rolling(2).mean()["Open"].reset_index(drop=True).rename()
