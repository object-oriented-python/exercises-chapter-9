from functools import singledispatch
import numbers

class Expression:

    def __init__(self, *ops):
        self.operands = tuple(ops)

    def __add__(self, other):
        if isinstance(other, numbers.Number):
            return Add(self, Number(other))
        elif isinstance(other, Expression):
            return Add(self, other)
        else:
            raise NotImplementedError
            
    def __sub__(self, other):
        if isinstance(other, numbers.Number):
            return Sub(self, Number(other))
        elif isinstance(other, Expression):
            return Sub(self, other)
        else:
            raise NotImplementedError

    def __mul__(self, other):
        if isinstance(other, numbers.Number):
            return Mul(self, Number(other))
        elif isinstance(other, Expression):
            return Mul(self, other)
        else:
            raise NotImplementedError

    def __truediv__(self, other):
        if isinstance(other, numbers.Number):
            return Div(self, Number(other))
        elif isinstance(other, Expression):
            return Div(self, other)
        else:
            raise NotImplementedError

    def __pow__(self, other):
        if isinstance(other, numbers.Number):
            return Pow(self, Number(other))
        elif isinstance(other, Expression):
            return Pow(self, other)
        else:
            raise NotImplementedError

    def __radd__(self, other):
        return Add(Number(other), self)

    def __rsub__(self, other):
        return Sub(Number(other), self)

    def __rmul__(self, other):
        return Mul(Number(other), self)

    def __rtruediv__(self, other):
        return Div(Number(other), self)
    
    def __rpow__(self, other):
        return Pow(Number(other), self)


class Operator(Expression):

    def __repr__(self):
        return type(self).__name__ + repr(self.operands)

    def __str__(self):
        lhs = str(self.operands[0])
        rhs = str(self.operands[1])

        if self.operands[0].precedence < self.precedence:
            lhs = f"({self.operands[0]})"

        if self.operands[1].precedence < self.precedence:
            rhs = f"({self.operands[1]})"

        return " ".join([lhs, self.symbol, rhs])


class Add(Operator):
    
    precedence = 1
    symbol = "+"


class Sub(Operator):
    
    precedence = 1
    symbol = "-"


class Mul(Operator):
    
    precedence = 2
    symbol = "*"


class Div(Operator):
    
    precedence = 2
    symbol = "/"


class Pow(Operator):
    
    precedence = 3
    symbol = "^"


class Terminal(Expression):
    precedence = 4

    def __init__(self, value):
        super().__init__()
        self.value = value
        
    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)

class Number(Terminal):
    def __init__(self, value):
        super().__init__(value)
        try:
            type(self.value) == numbers.Number
        except:
            raise TypeError

class Symbol(Terminal):
    def __init__(self, value):
        super().__init__(value)
        try:
            type(self.value) == str
        except:
            raise TypeError

def postvisitor(expr, fn, **kwargs):
    stack = []
    visited = {}
    stack.append(expr)
    while stack:
        e = stack.pop()
        unvisited = []
        for o in e.operands:
            if o not in visited:
                unvisited.append(o)

        if unvisited:
            stack.append(e)
            for i in unvisited:
                stack.append(i)
        
        else:
            visited[e] = fn(e, *(visited[o] for o in e.operands), **kwargs)

    return visited[expr]

from expressions import expressions

@singledispatch
def differentiate(expr, *o, **var):
    pass

@differentiate.register(expressions.Number)
def _(expr, *o, **var):
    return 0


@differentiate.register(expressions.Symbol)
def _(expr, *o, **var):
    if expr == var:
        return 1
    else:
        return 0


@differentiate.register(expressions.Add)
def _(expr, *o, **var):
    return differentiate(expr.operands[0], **var) + differentiate(expr.operands[1], **var)


@differentiate.register(expressions.Sub)
def _(expr, *o, **var):
    return differentiate(expr.operands[0], **var) - differentiate(expr.operands[1], **var)


@differentiate.register(expressions.Mul)
def _(expr, *o, **var):
    return Add(Mul(expr.operands[0], differentiate(expr.operands[1], **var)),
        Mul(expr.operands[1], differentiate(expr.operands[0], **var)))


@differentiate.register(expressions.Div)
def _(expr, *o, **var):
    u = expr.operands[0]
    v = expr.operands[1]
    u1 = differentiate(u, **var)
    v1 = differentiate(v, **var)
    return Div(Sub(Mul(v, u1), Mul(u, v1)), Pow(v, 2))

@differentiate.register(expressions.Pow)
def _(expr, *o, **var):
    return Mul(Mul(expr.operands[1], Pow(expr.operands[0], expr.operands[1] - 1)),
    differentiate(expr.operands[1], **var))