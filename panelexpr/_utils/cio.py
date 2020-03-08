import pandas as pd
import pathlib
import json
import datetime


def load_data_from_file(p, load_fun=None) -> pd.DataFrame:
    """
    从文件中加载DataFrame
    :param p: pathlib.Path
    :param load_fun: 接受 pathlib.Path，返回 pd.DataFrame
    :return: pd.DataFrame
    """
    if load_fun is None:
        if p.suffix == ".csv":
            def load_fun(_p): return pd.read_csv(pathlib.Path(_p).absolute())
        elif p.suffix == ".h5":
            def load_fun(_p): return pd.read_hdf(str(_p))
        else:
            def load_fun(_p): return None

    return load_fun(p)


def load_data(filepath, load_fun=None) -> pd.DataFrame:
    p = pathlib.Path(filepath)
    if p.is_file():
        return load_data_from_file(p, load_fun)

    data_list = [load_data_from_file(fp, load_fun) for fp in p.iterdir() if fp.is_file()]
    if data_list is None:
        return None
    data = data_list[0]
    for d in data_list[1:]:
        data = data.append(d)
    return data



def load_exprs(path):
    """
    :param path:
    :return: 返回字典
    """
    d = pathlib.Path(path)
    factor_files = []
    for p in d.iterdir():
        if p.suffix == ".json":
            factor_files.append(p)
    factors = {}
    for ff in factor_files:
        with ff.open('r') as f:
            factors[ff.stem] = json.load(f)
    return factors


def save_expr(expr, name, path):
    d = pathlib.Path(path)
    tp = d.joinpath(name + ".json")
    with tp.open("w") as f:
        json.dump(expr, f)


def gen_results_dir(path, future):
    d = pathlib.Path(path)
    t = datetime.datetime.now()
    td = d.joinpath("result-f" +str(future) + t.strftime("-%Y%m%d-%H%M%S"))
    td.mkdir(exist_ok=True)
    return str(td)
