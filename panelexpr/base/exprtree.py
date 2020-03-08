from panelexpr.base.node import BaseNode
from panelexpr.base.operator import SlotOperator, ExtractOperator, drop_med, \
    global_operator_dict
import copy
from panelexpr.base.context import context_builder


def default_tree_builder(node, op_dict, context, data_provider, node_cls=BaseNode, **kwargs):
    if node is not None:
        try:
            name = node['name']
        except KeyError:
            name = None

        try:
            args = node['args']
        except KeyError:
            args = {}

        try:
            children = [default_tree_builder(child, op_dict, context, data_provider, node_cls, **kwargs) for child in node['children']]
        except KeyError:
            children = []
        op = op_dict[node['op']](**args)
        if isinstance(op, ExtractOperator):
            op.load(data_provider)
        return node_cls(name, op, args, None, children, context, **kwargs)
    # name = None, op = None, args_bak = None, parent = None, children = None, context = None
    return None


class ExpressionTree:
    def __init__(self, expression=None, data_provider=None,
                 op_dict=None, tree_builder=default_tree_builder,
                 expr_tree=None, cols=None):
        """

        :param expression: 表达式描述树
        :param tree_builder: 执行建树操作的函数
        :param op_dict: 描述符到操作符的映射
        :param expr_tree: （可选）已经转换为树状组织但尚未包装成为ExpressionTree的表达式
        """
        if op_dict is None:
            # op_dict = OperationDict()
            op_dict = global_operator_dict

        if data_provider is None:
            raise ValueError("No data is provided")

        self.data_provider = data_provider
        self._context = context_builder()
        if expression:
            expression = copy.deepcopy(expression)
            expression['name'] = "factor"
            self._expr_tree = tree_builder(expression, op_dict, self._context, self.data_provider)
        elif expr_tree:
            self._expr_tree = expr_tree
            self._expr_tree.parent = None
        else:
            raise ValueError("parameter 'expression' and 'expr_tree' can not be both None.")

        self.height = self._expr_tree.height
        self.count = self._expr_tree.count
        self._traverse_counter = 0
        self._post_order_list = None
        self.__values = None
        self.__slots = None
        self.__cols = cols

    @property
    def expr_tree(self):
        return self._expr_tree

    @property
    def values(self):
        if self.__values is None:
            self.__values = self._expr_tree.values()
            if self.__cols:
                self.__values = self.__values[self.__cols]
            self._expr_tree.reset()
        return self.__values

    def tolist(self):
        self._check_post_order_list()
        return self._post_order_list

    def to_dict(self):
        return self._expr_tree.to_dict()

    # @profile
    def cut_(self, item):
        """
        会修改自身的剪切方法
        :param item:
        :return:
        """
        self.reset()
        child = self._post_order_list[item]
        parent = child.parent
        if parent is None:

            branch = self.data_free_deepcopy()
            self._expr_tree = BaseNode(name=self._expr_tree.name, op=SlotOperator(), parent=None)
            self.reset()
            branch.reset()
            return self, branch

        child_rank = parent.find_child(child)
        parent.children[child_rank] = BaseNode(name=child.name, op=SlotOperator(), parent=parent)

        branch = ExpressionTree(data_provider=self.data_provider, expr_tree=child)

        # 清空过去保存的计算结果
        self.reset()
        branch.reset()

        # 返回剪切后的树和剪下来的计算树枝
        return self, branch

    def cut(self, item):
        tree = self.data_free_deepcopy()
        return tree.cut_(item)

    # @profile
    def graft_(self, branch):
        """
        注意，此操作可能导致data_provider不一致，因此在reset中增加统一dp的操作
        :param branch:
        :return:
        """
        self.__update_slots()
        if self.__slots:
            s = self.__slots[0]
        else:
            raise ValueError("There is no slot in the expression tree.")

        # self.reset()
        branch = branch.data_free_deepcopy()
        branch.reset()
        p = s.parent
        if p is None:
            name = self._expr_tree.name
            self._expr_tree = branch.expr_tree
            self._expr_tree.name = name
            self.reset()
            return self

        child_rank = p.find_child(s)
        child = branch.expr_tree
        p.children[child_rank] = child

        # 清空过去保存的计算结果
        self.reset()
        return self

    def graft(self, branch):
        tree = self.data_free_deepcopy()
        return tree.graft_(branch)

    def get_slots(self):
        self.__update_slots()
        return self.__slots

    def reset(self):
        self._expr_tree.parent = None
        self.__update_post_order_list()
        self.__update_slots()
        self.__values = None
        self.unify_data_provider()
        self._expr_tree.reset()
        self.data_provider.reset()

    # @profile
    def data_free_deepcopy(self):
        d = self.unlink_data()

        v = self.__values
        self.__values = None
        # s = asizeof.asizeof(self)
        # sh = self.data_provider.is_holding_data()

        cp = copy.deepcopy(self)
        # ch = cp.data_provider.is_holding_data()

        self.link_data(d)
        self.__values = v
        cp.link_data(d)
        return cp

    def unlink_data(self):
        d = self.data_provider.unlink_data()
        return d

    def link_data(self, d):
        self.data_provider.link_data(d)

    def unify_data_provider(self):
        self._expr_tree.unify_data_provider(self.data_provider)

    def __update_slots(self):
        self._check_post_order_list()
        self.__slots = [s for s in self._post_order_list if isinstance(s.op, SlotOperator)]

    def __update_post_order_list(self):
        self.__build_traverse_list()

    def __build_traverse_list(self):
        self._traverse_counter = 0
        self._post_order_list = []
        self.__post_order_traverse(self._expr_tree)

    def __post_order_traverse(self, expr_tree):
        if not expr_tree:
            return
        for child in expr_tree.children:
            self.__post_order_traverse(child)
        self._post_order_list.append(expr_tree)

    def _check_post_order_list(self):
        if not self._post_order_list:
            self.__build_traverse_list()

    # def __getitem__(self, item):
    #     return self.value()[item]

    def __repr__(self):
        return str(self.values)


class DataProvider:
    def __init__(self, data, use_copy=False):
        self._data = data
        self._use_copy = use_copy

    def __call__(self, cols = None):
        if cols is None:
            if self._use_copy:
                return self._data.copy()
            else:
                return self._data
        return self._data[cols]

    def unlink_data(self):
        data = self._data
        self._data = None
        return data

    def is_holding_data(self):
        return self._data is not None

    def link_data(self, data):
        self._data = data

    def reset(self):
        if not self._use_copy:
            drop_med(self._data)


