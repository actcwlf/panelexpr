import numba
import numpy as np


@numba.jit
def corr(a1, a2):
    c = np.mean((a1-np.mean(a1)) * (a2-np.mean(a2)))
    v1 = np.var(a1)
    v2 = np.var(a2)
    return c / np.sqrt(v1 * v2)


@numba.jit
def cov(a1, a2):
    # 返回无偏结果
    c = np.sum((a1-np.mean(a1)) * (a2-np.mean(a2))) / (len(a1) - 1)
    return c


@numba.jit
def rolling_mean(a, lag):
    l = len(a)
    r = np.empty(l, dtype=np.float64)

    if l < lag:
        r[:] = np.nan
        return r

    f = 1
    s = 0
    for i in range(l):
        if not np.isnan(a[i]):
            s += a[i]
            if f < lag:
                f += 1
                r[i] = np.nan
            else:
                r[i] = s / lag
                s -= a[i - lag + 1]
        else:
            s = 0
            f = 1
            r[i] = np.nan

    return r


@numba.jit
def _rolling_var(a, lag):
    m = rolling_mean(a, lag)
    l = len(a)
    r = np.empty(l, dtype=np.float64)
    r[:lag-1] = np.nan

    if l < lag:
        return r

    for i in range(lag - 1, l):
        s = a[i - lag + 1: i + 1]
        r[i] = np.sum((s - m[i]) * (s - m[i]))
    return r


@numba.jit
def rolling_var(a, lag):
    return _rolling_var(a, lag) / (lag - 1)


@numba.jit
def rolling_std(a, lag):
    return np.sqrt(_rolling_var(a, lag) / (lag - 1))


@numba.jit
def _rolling_cov(a1, a2, lag):
    m1 = rolling_mean(a1, lag)
    m2 = rolling_mean(a2, lag)
    l = len(a1)
    r = np.empty(l, dtype=np.float64)
    r[:lag-1] = np.nan
    if l < lag:
        return r
    for i in range(lag - 1, l):
        s1 = a1[i - lag + 1: i + 1]
        s2 = a2[i - lag + 1: i + 1]
        r[i] = np.sum((s1 - m1[i]) * (s2 - m2[i]))
    return r


@numba.jit
def rolling_cov(a1, a2, lag):
    return _rolling_cov(a1, a2, lag) / (lag - 1)


@numba.jit
def rolling_corr(a1, a2, lag):
    c = _rolling_cov(a1, a2, lag)
    v1 = _rolling_var(a1, lag)
    v2 = _rolling_var(a2, lag)
    return c / np.sqrt(v1 * v2)


@numba.jit
def rolling(a, lag):
    l = len(a)
    r = np.empty(l, dtype=np.float64)
    r[:lag] = np.nan
    if l < lag:
        return r
    r[lag:] = a[:-lag]
    return r


@numba.jit
def ewma(a, span):
    # print(a)
    alpha = 2 / (span + 1)
    l = len(a)
    wa = np.empty(l, dtype=np.float64)

    p = np.nan
    f = 1
    wa[0] = p = a[0]
    for i in range(1, l):
        if np.isnan(a[i]):
            wa[i] = p
        else:
            if np.isnan(wa[i-1]):
                if np.isnan(p):
                    p = wa[i] = a[i]
                else:
                    wa[i] = p
            else:
                p = wa[i] = alpha * a[i] + (1 - alpha) * wa[i-1]
                f = 1
                # p = wa[i]


    return wa



