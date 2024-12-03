import pytest
from functools import singledispatch
from collections.abc import Sequence
from example_code.expression_tools import postvisitor, evaluate
from expressions.expressions import Symbol, Number, \
    Operator, Add, Mul
try:
    from expressions.expressions import differentiate
except ImportError:
    pass


class ExpressionsError(Exception):
    pass


_test_expr = Symbol("x") / Number(1)
_operands_attr = None
for attr_name in dir(_test_expr):
    attr = getattr(_test_expr, attr_name)
    if (
        isinstance(attr, Sequence) and len(attr) == 2
        and type(attr[0]) is Symbol and str(attr[0]) == "x"
        and type(attr[1]) is Number and float(str(attr[1])) == 1.0
    ):
        _operands_attr = attr_name
        break


def try_eval(expression):
    """Evaluate an expression if it doesn't have any symbols."""
    try:
        return postvisitor(expression, evaluate, symbol_map={})
    except KeyError:
        return expression


def operands(expression):
    """Return the operands tuple of an expression."""
    if _operands_attr is None:
        raise ExpressionsError("Could not find operands tuple on expression.")
    return tuple(getattr(expression, _operands_attr))


@singledispatch
def expressions_equal(t1, t2):
    """Return true if two expressions are equal.
    
    This function takes into account commutative operators, but not the full
    class of equivalences between expressions.
    """
    try:
        if isinstance(t1, tuple) and isinstance(t2, tuple):
            return len(t1) == len(t2)\
                and all(expressions_equal(e1, e2) for e1, e2 in zip(t1, t2))
    except:
        return False
    return False  # By default, expressions don't match.


@expressions_equal.register(Number)
def _(e1, e2):
    #  Not the nicest way to do it, but `str` is the only way we have to
    #  extract the value.
    return float(str(e1)) == float(str(e2))


@expressions_equal.register(Symbol)
def _(e1, e2):
    return str(e1) == str(e2)


@expressions_equal.register(Operator)
def _(e1, e2):
    return type(e1) is type(e2)\
        and expressions_equal(operands(e1), operands(e2))


@expressions_equal.register(Add)
@expressions_equal.register(Mul)
def _(e1, e2):
    return type(e1) is type(e2)\
        and (
            expressions_equal(operands(e1), operands(e2))
            or expressions_equal(operands(e1), tuple(reversed(operands(e2))))
        ) or try_eval(e1) == try_eval(e2)


expressions_equal.register(tuple)
def _(t1, t2):
    return type(t1) is type(t2) and len(t1) == len(t2)\
        and all(expressions_equal(e1, e2) for e1, e2 in zip(t1, t2))


def test_diff_import():
    from expressions.expressions import differentiate


@pytest.fixture
def sample_diff_set():
    from expressions.expressions import Symbol
    x = Symbol('x')
    y = Symbol('y')
    tests = [(2 * x + 1, 'x', 1.5, 10, 2, 0.0 * x + 1.0 * 2 + 0.0),
             (3 * x + y, 'x', 1.5, 10, 3, 0.0 * x + 1.0 * 3 + 0.0),
             (x * y + x / y, 'y', 3, 2, 2.25,
              0.0 * y + 1.0 * x + (0.0 * y - x * 1.0) / (y ** 2)),
             (2 * x**3 + x**2 * y, 'x', 2, 3, 36,
              0.0 * x**3 + 3 * x**(3 - 1) * 1.0 * 2 + 2 * x**(2 - 1) * 1.0 * 
              y + 0.0 * x**2)
             ]
    return tests


@pytest.mark.parametrize("idx", [
    (0),
    (1),
    (2)
])
def test_diff_expr_recursive(sample_diff_set, idx):
    from expressions.expressions import differentiate
    from example_code.expression_tools import postvisitor
    expr, dvar, _, _, _, diff_expr = sample_diff_set[idx]
    derivative = postvisitor(expr, differentiate, var=dvar)
    assert expressions_equal(derivative, diff_expr), \
        f"Computing expression d/d{dvar}({expr}). Expected: \n {diff_expr}"\
        f"\n got: \n {derivative}"


@pytest.mark.parametrize("idx", [
    (0),
    (1),
    (2),
    (3)
])
def test_diff_val_recursive(sample_diff_set, idx):
    from expressions.expressions import differentiate
    from example_code.expression_tools import postvisitor, evaluate
    expr, dvar, x, y, val, _ = sample_diff_set[idx]
    dexpr = postvisitor(expr, differentiate, var=dvar)
    assert postvisitor(dexpr, evaluate, symbol_map={'x': x, 'y': y}) == val, \
        f"expected a value of {val} for expression d/d{dvar}({expr})" \
        f" evaluated at (x = {x}, y = {y})"


@pytest.mark.parametrize("idx", [
    (0),
    (1),
    (2)
])
def test_diff_expr(sample_diff_set, idx):
    from expressions.expressions import postvisitor, differentiate
    expr, dvar, _, _, _, diff_expr = sample_diff_set[idx]
    derivative = postvisitor(expr, differentiate, var=dvar)
    assert expressions_equal(derivative, diff_expr), \
        f"expected an expression of {diff_expr}"\
        f" for expression d/d{dvar}({expr}), got {derivative}"


@pytest.mark.parametrize("idx", [
    (0),
    (1),
    (2),
    (3)
])
def test_diff_val(sample_diff_set, idx):
    from expressions.expressions import postvisitor, differentiate
    from example_code.expression_tools import evaluate
    expr, dvar, x, y, val, _ = sample_diff_set[idx]
    dexpr = postvisitor(expr, differentiate, var=dvar)
    assert postvisitor(dexpr, evaluate, symbol_map={'x': x, 'y': y}) == val, \
        f"expected a value of {val} for expression d/d{dvar}({expr})" \
        f" evaluated at (x = {x}, y = {y})"
