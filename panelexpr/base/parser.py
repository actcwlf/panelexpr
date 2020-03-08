import ast
import warnings


def parse(formula):
    tree = ast.parse(formula)
    tree = ast.fix_missing_locations(tree)
    return tree


def ast2desc(node, ctx):
    e = node.body[0].value
    return _ast2desc(e, ctx)


def _construct_unaryop(node, ctx):
    return {}


BINOP_MAPPING = {
    ast.Add: "Add",
    ast.Mult: "Mul",
    ast.Sub: "Sub",
    ast.Div: "Div"

}


def _construct_binop(node, ctx):
    d = {
        "op": BINOP_MAPPING[type(node.op)]
    }
    children = [
        _ast2desc(node.left, ctx),
        _ast2desc(node.right, ctx)
    ]
    d["children"] = children

    return d


def _keyword_parser(node, ctx):
    assert isinstance(node, ast.keyword)
    k = node.arg
    if isinstance(node.value, ast.Str):
        v = node.value.s
    else:
        v = None
    return k, v


FUN_MAPPING = {
    "shift": "Shift",
    "mmean": "MovingAverage",
    "ma": "MovingAverage",
    "mstd": "MovingStd",
    "mcov": "MovingCov",
    "mcorr": "MovingCorr",
    "ewm": "EWM",
    "ema": "EWM",
    "where": "Where",
    "less": "Less",
    "rank": "Rank",
    "mmax": "TimeSeriesMax",
    "mmin": "TimeSeriesMin"
}

NECESSARY_ARGS = {
    "shift": {"group_by": "group_tag"},
    "mmean": {"group_by": "group_tag"},
    "ma": {"group_by": "group_tag"},
    "mstd": {"group_by": "group_tag"},
    "mcov": {"group_by": "group_tag"},
    "mcorr": {"group_by": "group_tag"},
    "ewm": {"group_by": "group_tag"},
    "ema": {"group_by": "group_tag"},
    "where": None,
    "less": None,
    "rank": {"group_by": "time_tag"},
    "mmax": {"group_by": "group_tag"},
    "mmin": {"group_by": "group_tag"},
}


def _check_func(funcid):
    try:
        FUN_MAPPING[funcid]
    except KeyError:
        raise ValueError(f"no function with name {funcid}")


def _construct_call(node, ctx):
    _check_func(node.func.id)
    d = {
        "op": FUN_MAPPING[node.func.id]
    }
    children = [
        _ast2desc(n, ctx) for n in node.args
    ]
    kwargs = {}
    for k, v in [_keyword_parser(k, ctx) for k in node.keywords]:
        kwargs[k] = v
    # print(node.func.id, kwargs, ctx)
    if NECESSARY_ARGS[node.func.id]:
        nargs = NECESSARY_ARGS[node.func.id]
        for k, v in nargs.items():
            try:
                kwargs[k]
            except KeyError:
                kwargs[k] = ctx["kwargs"][v]

    d["args"] = kwargs
    d["children"] = children
    return d


def _construct_name(node, ctx):
    d = {
        "op": "Extract",
        "args": {"name": node.id}
    }
    return d


def _construct_num(node, ctx):
    d = {
        "op": "Literal",
        "args": {"value": node.n}
    }
    return d


CONSTRUCTOR = {
    ast.UnaryOp: _construct_unaryop,
    ast.BinOp: _construct_binop,
    ast.Call: _construct_call,
    ast.Name: _construct_name,
    ast.Num: _construct_num
}


def _ast2desc(node, ctx):
    try:
        # print(type(node))
        return CONSTRUCTOR[type(node)](node, ctx)
    except KeyError:
        print("KeyError with", type(node))
        return {}


def register(key, ir_name, necessary_args=None):
    try:
        t = FUN_MAPPING[key]
        warnings.warn(f"Function {key} is overridden.")
    except KeyError:
        pass
    finally:
        FUN_MAPPING[key] = ir_name
        NECESSARY_ARGS[key] = necessary_args


def unregister(key):
    del FUN_MAPPING[key]
    del NECESSARY_ARGS[key]
