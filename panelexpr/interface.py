from panelexpr.base.parser import *
from panelexpr.base.exprtree import ExpressionTree, DataProvider
from panelexpr.base.operator import TimeSeriesOperator, CrossSectionalOperator, DoubleSeriesOperator,global_operator_dict
from panelexpr.base import parser


__all__ = [
    "TimeSeriesOperator",
    "CrossSectionalOperator",
    "DoubleSeriesOperator",
    "eval",
    "register",
    "unregister"
]


def eval(formula, data, group_tag=None, time_tag=None, print_only=False):
    tree = parse(formula)
    ctx = {
        "kwargs": {
            "group_tag": group_tag,
            "time_tag": time_tag
        }
    }
    f_desc = ast2desc(tree, ctx)
    if print_only:
        print(f_desc)
        return None
    expr = ExpressionTree(f_desc, data_provider=DataProvider(data))
    return expr.values.rename()


def register(key, op_cls):
    ir_name = op_cls.__name__
    global_operator_dict.register(ir_name, op_cls)
    if issubclass(op_cls, TimeSeriesOperator):
        parser.register(key, ir_name, {"group_by": "group_tag"})
    elif issubclass(op_cls, CrossSectionalOperator):
        parser.register(key, ir_name, {"group_by": "time_tag"})
    else:
        parser.register(key, ir_name)


def unregister(key):
    ir_name = parser.FUN_MAPPING[key]
    global_operator_dict.unregister(ir_name)
    parser.unregister(key)

