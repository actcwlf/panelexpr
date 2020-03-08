from abc import abstractmethod, ABC, ABCMeta
import pandas as pd
import numpy as np
from enum import Enum
import panelexpr.boost.calc as bt
import warnings
"""
整体设计思路：
在子节点计算值保存在dataframe中后，同时向上返回列的名称和dataframe
装饰器根据这些信息提取出待计算的数据，送到相应exec函数中（将peeled_args传入），计算完毕后再以同样的方式向上层节点传递
"""

OpType = Enum("OperatorType", ["TERM", "UNARY", "BINARY", "TERNARY", "MULTI"])
label_recorder = 0
LABEL_PREFIX = "__ct_"


def get_label(op_str=""):
    global label_recorder
    label_recorder += 1
    return LABEL_PREFIX + op_str + "_" + str(label_recorder)


def is_label(s):
    return s[:len(LABEL_PREFIX)] == LABEL_PREFIX


def drop_med(data, ignore=None, inplace=True):
    if not isinstance(data, pd.DataFrame):
        return
    cols = list(data.columns)
    if ignore is not None:
        cols = set(cols) - set(ignore)
    med_col = [c for c in cols if is_label(c)]
    data.drop(columns=med_col, inplace=inplace)


def panel_wrapper(func):
    """
    确保输入输出均为带有标记的面板数据，适用于截面数据
    :param func:
    :return:
    """
    def wrapped(instance, *args):
        result = {}
        # 以靠前的dataframe优先作为保存结果的基础
        i = 0
        gid = []
        for arg in args:
            if isinstance(arg[1], pd.DataFrame):
                result = arg[1]
            else:
                gid.append(i)
            i += 1
        # 生成保存当前节点计算结果列的列名
        label = get_label(instance.__class__.__name__)
        # 将参数处理成便于计算的形式
        peeled_args = [arg[1][arg[0]] for arg in args]
        # 计算
        result[label] = func(instance, *peeled_args)

        # for i in gid:
        #     del args[i]
        # 按传递规则向上层返回
        return label, result

    return wrapped


class BasePanelMixin:
    @abstractmethod
    def extract(self, *args, **kwargs):
        pass

    def save(self, context, eval_result):
        # 生成保存当前节点计算结果列的列名
        label = get_label(self.__class__.__name__)
        context['data'][label] = eval_result
        # pass
        return 'data', label


class PanelMixin(BasePanelMixin):
    def extract(self, context, *args):
        operands = [context[k1][k2] for k1, k2 in args]
        return operands


class SingleGroupedPanelMixin(BasePanelMixin):
    """
    Single moving operator
    """
    def extract(self, context, key_col, groupby, key_num):
        """"""
        k1, k2 = key_col
        grouped_operand = context[k1].groupby(groupby)[k2]
        k1, k2 = key_num
        num_operand = context[k1][k2]
        return grouped_operand, num_operand


class CrossSectionGroupedPanelMixin(BasePanelMixin):
    """
    Single moving operator
    """
    def extract(self, context, key_col, groupby):
        """"""
        k1, k2 = key_col
        grouped_operand = context[k1].groupby(groupby)[k2]
        return grouped_operand


class DoubleGroupedPanelMixin(BasePanelMixin):
    """
    Single moving operator
    """
    def extract(self, context, key_col1, key_col2, groupby, key_num):
        """"""
        k1, k2 = key_col1
        grouped_operand1 = context[k1].groupby(groupby)[k2]
        k1, k2 = key_col2
        grouped_operand2 = context[k1].groupby(groupby)[k2]
        k1, k2 = key_num
        num_operand = context[k1][k2]
        return grouped_operand1, grouped_operand2, num_operand


def grouped_panel_wrapper(func):
    """
    确保输入输出均为带有标记的面板数据，适用于时间序列计算
    :param func:
    :return:
    """
    def wrapped(instance, *args):
        result = args[0][1]
        if not isinstance(result, pd.DataFrame):
            raise Exception("unmatched calculation")
        label = get_label(instance.__class__.__name__)

        if instance.sort:
            grouped = (
                args[0][1]
                .sort_values(
                    [instance.group_by, instance.sort_by],
                    ascending=instance.ascending
                )
                .groupby(instance.group_by)[args[0][0]]
            )
        else:
            grouped = args[0][1].groupby(instance.group_by)[args[0][0]]

        if instance.operator_type == OpType.UNARY:
            peeled_args = [grouped]
        else:
            peeled_args = [
                grouped,
                args[1][1][args[1][0]]
            ]
        # print(instance.__class__.__name__)
        # print(instance, *peeled_args)
        t = func(instance, *peeled_args)
        # print(t.shape)
        if isinstance(t.index, pd.MultiIndex):
            # print(t.index)
            # print(t.reset_index(drop=True))
            # print(t.droplevel(instance.group_by))
            try:
                result[label] = t.droplevel(instance.group_by)
            except:
                result[label] = t.reset_index(drop=True)
            # print(result)
        else:
            result[label] = t
        # del t
        # del peeled_args

        return label, result

    return wrapped


def grouped_panel_wrapper2(func):
    """
    确保输入输出均为带有标记的面板数据，适用于两个时间序列交叉计算
    目前已可以废弃
    :param func:
    :return:
    """
    def wrapped(instance, *args):
        result = args[0][1]
        if not isinstance(result, pd.DataFrame):
            raise Exception("unmatched calculation")
        label = get_label(instance.__class__.__name__)

        if instance.sort:
            grouped1 = (
                args[0][1]
                .sort_values(
                    [instance.group_by, instance.sort_by],
                    ascending=instance.ascending
                )
                .groupby(instance.group_by)[args[0][0]]
            )
            grouped2 = (
                args[1][1]
                .sort_values(
                    [instance.group_by, instance.sort_by],
                    ascending=instance.ascending
                )
                .groupby(instance.group_by)[args[1][0]]
            )
        else:
            grouped1 = args[0][1].groupby(instance.group_by)[args[0][0]]
            grouped2 = args[1][1].groupby(instance.group_by)[args[1][0]]

        t = pd.Series()
        for x, y in zip(grouped1, grouped2):
            t = t.append(func(instance, x[1], y[1], args[2][1][args[2][0]]))

        result[label] = t
        return label, result

    return wrapped


class BaseOperator:
    def __init__(self, op_type):
        self.__type = op_type

    @abstractmethod
    def exec(self, *args):
        pass

    @abstractmethod
    def eval(self, *args, **kwargs):
        pass

    @property
    def operator_type(self):
        return self.__type

    def name(self):
        return self.__class__.__name__[:-8]

    def __repr__(self):
        return self.__class__.__name__[:-8]


class BinaryOperator(BaseOperator, PanelMixin):
    def __init__(self):
        super().__init__(OpType.BINARY)

    def eval(self, lope, rope):
        pass

    def exec(self, context, *args):
        """
        extracting operands from context, executing operation and saving the result to the context
        :param context:
        :param args: keys of operands in context
        :return: key of result in context
        """
        operands = self.extract(context, *args)
        eval_result = self.eval(*operands)
        return self.save(context, eval_result)


class TernaryOperator(BaseOperator, ABC):
    def __init__(self, *args):
        super().__init__(OpType.TERNARY)

    def exec(self, *args):
        pass


class MultiOperator(BaseOperator, ABC):
    def __init__(self, *args):
        super().__init__(OpType.MULTI)

    def exec(self, *args):
        pass


class SingleSeriesOperator(BaseOperator, SingleGroupedPanelMixin, ABC):
    def __init__(self, op_type, group_by, sort=False, sort_by=None, ascending=True):
        super().__init__(op_type)
        self.group_by = group_by
        self.sort = sort
        self.sort_by = sort_by
        self.ascending = ascending

    def exec(self, context, *args):
        grouped_operand, num_operand = self.extract(context, args[0], self.group_by, args[1])
        eval_result = pd.Series()
        for k, operand in grouped_operand:
            eval_result = eval_result.append(self.eval(operand, num_operand))
        return self.save(context, eval_result)


class TimeSeriesOperator(SingleSeriesOperator, ABC):
    def __init__(self, group_by, sort=False, sort_by=None, ascending=True):
        super().__init__(OpType.BINARY, group_by, sort, sort_by, ascending)


class CrossSectionalOperator(BaseOperator, CrossSectionGroupedPanelMixin, ABC):
    def __init__(self, group_by):
        super().__init__(OpType.UNARY)
        self.group_by = group_by

    def exec(self, context, *args):
        grouped_operand = self.extract(context, args[0], self.group_by)
        eval_result = pd.Series()
        for k, operand in grouped_operand:
            eval_result = eval_result.append(self.eval(operand))
        return self.save(context, eval_result)


class DoubleSeriesOperator(BaseOperator, DoubleGroupedPanelMixin, ABC):
    def __init__(self, group_by, sort=False, sort_by=None, ascending=True):
        super().__init__(OpType.TERNARY)
        self.group_by = group_by
        self.sort = sort
        self.sort_by = sort_by
        self.ascending = ascending

    def exec(self, context, *args):
        grouped_operand1, grouped_operand2, num_operand = self.extract(context, args[0], args[1], self.group_by, args[2])
        eval_result = pd.Series()
        for x, y in zip(grouped_operand1, grouped_operand2):
            eval_result = eval_result.append(self.eval(x[1],y[1], num_operand))
        return self.save(context, eval_result)


class ExtractOperator(BaseOperator, ABC):
    """
    从数据源中提取数据
    """
    def __init__(self, name):
        super().__init__(OpType.TERM)
        self.__name = name
        self.__data_provider = None

    def load(self, data_provider):
        self.__data_provider = data_provider

    def exec(self, context):
        context['data'] = self.__data_provider()
        return 'data', self.__name

    def __repr__(self):
        return self.__class__.__name__[:-8] + ": '" + self.__name + "'"


class SlotOperator(BaseOperator, ABC):
    def __init__(self):
        super().__init__(OpType.TERM)

    def exec(self, context):
        label = get_label(self.__class__.__name__)
        context['literal'][label] = np.nan
        return 'literal', label


class LiteralOperator(BaseOperator):
    def __init__(self, value):
        super().__init__(OpType.TERM)
        self.__value = value

    def exec(self, context):
        label = get_label(self.__class__.__name__)
        context['literal'][label] = self.__value
        return 'literal', label

    def __repr__(self):
        if isinstance(self.__value, str):
            value = "'" + self.__value + "'"
        else:
            value = str(self.__value)

        return self.__class__.__name__[:-8] + ": " + value


class AddOperator(BinaryOperator):
    def eval(self, lope, rope):
        return pd.eval('lope + rope')


class SubOperator(BinaryOperator):
    def eval(self, lope, rope):
        return pd.eval('lope - rope')


class MulOperator(BinaryOperator):
    def eval(self, lope, rope):
        return pd.eval('lope * rope')


class DivOperator(BinaryOperator):
    def eval(self, lope, rope):
        return pd.eval('lope / rope')


class LessOperator(BinaryOperator):
    def eval(self, lope, rope):
        return lope < rope


class ShiftOperator(TimeSeriesOperator):
    def eval(self, series, lag):
        return series.shift(lag)


class TimeSeriesMaxOperator(TimeSeriesOperator):
    def eval(self, series, lag):
        return series.rolling(lag).max()


class TimeSeriesMinOperator(TimeSeriesOperator):
    def eval(self, series, lag):
        return series.rolling(lag).min()


class EWMOperator(TimeSeriesOperator):
    def eval(self, series: pd.Series, lag):
        return series.ewm(span=lag, min_periods=lag-1).mean()


class MovingAverageOperator(TimeSeriesOperator):
    def eval(self, series, window):
        s = pd.Series(bt.rolling_mean(series.to_numpy(), window), index=series.index)
        return s


class MovingStdOperator(TimeSeriesOperator):
    def eval(self, series, window):
        return pd.Series(bt.rolling_std(series.to_numpy(), window), index=series.index)


class WhereOperator(TernaryOperator):
    @panel_wrapper
    def exec(self, con, val1, val2):
        return np.where(con, val1, val2)


class MovingCovOperator(DoubleSeriesOperator):
    def eval(self, s1, s2, lag):
        v = pd.Series(bt.rolling_cov(s1.to_numpy(), s2.to_numpy(), lag), index=s1.index)
        return v


class MovingCorrOperator(DoubleSeriesOperator):
    def eval(self, s1, s2, lag):
        v = pd.Series(bt.rolling_corr(s1.to_numpy(), s2.to_numpy(), lag), index=s1.index)
        return v


class RankOperator(CrossSectionalOperator):
    def eval(self, cross):
        return cross.rank()


class OperatorDict:
    def __init__(self):
        self.mapping = {}

    def register(self, key, op_cls):
        try:
            t = self.mapping[key]
            warnings.warn(f"Operator {key} is overridden.")
        except KeyError:
            pass
        finally:
            self.mapping[key] = op_cls

    def unregister(self, key):
        del self.mapping[key]

    def __getitem__(self, key):
        try:
            return self.mapping[key]
        except KeyError:
            raise KeyError(f"Undefined operator {key}.")


global_operator_dict = OperatorDict()

global_operator_dict.register("Add", AddOperator)
global_operator_dict.register("Sub", SubOperator)
global_operator_dict.register("Mul", MulOperator)
global_operator_dict.register("Div", DivOperator)
global_operator_dict.register("Extract", ExtractOperator)
global_operator_dict.register("Literal", LiteralOperator)
global_operator_dict.register("Shift", ShiftOperator)
global_operator_dict.register("MovingAverage", MovingAverageOperator)
global_operator_dict.register("MovingStd", MovingStdOperator)
global_operator_dict.register("MovingCov", MovingCovOperator)
global_operator_dict.register("MovingCorr", MovingCorrOperator)
global_operator_dict.register("EWM", EWMOperator)
global_operator_dict.register("Where", WhereOperator)
global_operator_dict.register("Less", LessOperator)
global_operator_dict.register("Rank", RankOperator)
global_operator_dict.register("TimeSeriesMax", TimeSeriesMaxOperator)
global_operator_dict.register("TimeSeriesMin", TimeSeriesMinOperator)