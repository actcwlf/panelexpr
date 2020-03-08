import pandas as pd
import numpy as np


def mean_absolute_deviation(s1, s2):
    if len(s1) != len(s2):
        return np.nan
    return np.abs(s1 - s2).mean()


def nan_matching(s1, s2):
    if len(s1) != len(s2):
        return False
    flag = True
    for i, j in zip(s1, s2):
        if pd.isnull(i) == pd.isnull(j):
            pass
        else:
            flag = False
            break
    return flag
