from .operator import BaseOperator, ExtractOperator
from .operator import OpType
# from .operator import OperationDict
from panelexpr.base.operator import drop_med


class BaseNode:
    def __init__(self, name=None, op=None, args_bak=None, parent=None, children=None, context=None):
        self.__parent = parent
        if children is None:
            self.__children = []
        else:
            self.__children = children
        for child in self.__children:
            child.parent = self
        self._operator = op
        self._name = name
        self._kwargs_bak = args_bak
        self.__value = None
        self._height = None
        self._count = None
        self._context = context

    @property
    def height(self):
        if self._height is not None:
            return self._height
        if self.__children:
            self._height = max([t.height for t in self.__children]) + 1
        else:
            self._height = 0
        return self._height

    @property
    def count(self):
        if self._count is not None:
            return self._count
        if self.__children:
            self._count = sum([t.count for t in self.__children]) + 1
        else:
            self._count = 1
        return self._count

    @property
    def op(self):
        return self._operator

    @property
    def children(self):
        return self.__children

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, p):
        self.__parent = p

    def reset_context(self, context):
        self._context = context
        for c in self.__children:
            c.reset_context(context)

    def unify_data_provider(self, data_provider):
        if isinstance(self._operator, ExtractOperator):
            self._operator.load(data_provider)
        for c in self.__children:
            c.unify_data_provider(data_provider)

    def find_child(self, child):
        i = 0
        for c in self.__children:
            if c == child:
                break
            i += 1
        return i

    # @profile
    def calculate(self):
        t = self._operator.operator_type

        if t == OpType.TERM:
            v = self._operator.exec(self._context)
        else:
            params = [node.calculate() for node in self.__children]
            v = self._operator.exec(self._context, *params)
        # drop_med(v[1], ignore=[v[0]])
        self.__value = v
        return self.__value

    # @profile
    def reset(self):
        self.__value = None
        self._height = None
        self._count = None
        for child in self.__children:
            child.reset()

    # @profile
    def values(self):
        if self.__value is None:
            self.calculate()
        if self._name is not None:
            r = self._context[self.__value[0]][self.__value[1]]
            # r = self.__value[1].rename(columns={self.__value[0]:self._name})
        else:
            # r = self.__value[1]
            r = self._context[self.__value[0]][self.__value[1]]

        return r

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, n):
        self._name = n

    def to_dict(self):
        d = {
            "op": self._operator.name(),

        }
        if self._kwargs_bak:
            d["args"] = self._kwargs_bak
        children = [c.to_dict() for c in self.__children]
        if children:
            d["children"] = children
        return d

    def __repr__(self):
        return str(self._operator)


