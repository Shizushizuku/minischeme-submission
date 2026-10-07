"""The built-in library, with Scheme-specific type and arithmetic semantics."""

import operator
import sys
from functools import reduce

from .environment import Environment
from .errors import SchemeError
from .printer import format_value
from .values import (
    NIL, Builtin, Closure, Pair, Symbol, is_number, is_true, list_items, make_list,
)


def require_number(value):
    if not is_number(value):
        raise SchemeError("expected a number")
    return value


def require_integer(value):
    if type(value) is not int:
        raise SchemeError("expected an integer")
    return value


def numeric(function):
    def checked(*args):
        for arg in args:
            require_number(arg)
        return function(*args)
    return checked


def truncate_quotient(left, right):
    require_integer(left)
    require_integer(right)
    # Do not convert to float: that loses precision for large Scheme integers.
    quotient = abs(left) // abs(right)
    return -quotient if (left < 0) != (right < 0) else quotient


def divide(first, *rest):
    if not rest:
        return 1 / first
    result = first
    for value in rest:
        if type(result) is int and type(value) is int:
            result = truncate_quotient(result, value)
        else:
            result /= value
    return result


def compare(relation):
    def chained(*args):
        if not (all(is_number(arg) for arg in args)
                or all(isinstance(arg, Symbol) for arg in args)):
            raise SchemeError("comparison expects numbers or symbols of compatible types")
        return all(relation(left, right) for left, right in zip(args, args[1:]))
    return chained


def eq(left, right):
    if is_number(left) and is_number(right):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, (Symbol, bool)):
        return left == right
    return left is right


def equal(left, right):
    # An explicit worklist also handles long lists without Python recursion.
    pending = [(left, right)]
    while pending:
        left, right = pending.pop()
        if isinstance(left, Pair) and isinstance(right, Pair):
            pending.append((left.cdr, right.cdr))
            pending.append((left.car, right.car))
        elif type(left) is str and type(right) is str:
            if left != right:
                return False
        elif not eq(left, right):
            return False
    return True


def require_pair(value):
    if not isinstance(value, Pair):
        raise SchemeError("expected a pair")
    return value


def is_list(value):
    while isinstance(value, Pair):
        value = value.cdr
    return value is NIL


def append(*lists):
    if not lists:
        return NIL
    # Copy the prefixes and retain the last tail, as in Scheme append.
    result = lists[-1]
    for value in reversed(lists[:-1]):
        result = make_list(list_items(value), result)
    return result


def create_global_environment(output=None):
    output = sys.stdout if output is None else output
    environment = Environment()

    def register(name, function, minimum=0, maximum=None):
        environment.define(Symbol(name), Builtin(name, function, minimum, maximum))

    register("+", numeric(lambda *args: sum(args)))
    register("*", numeric(lambda *args: reduce(operator.mul, args, 1)))
    register("-", numeric(lambda first, *rest: first - sum(rest) if rest else -first), 1)
    register("/", numeric(divide), 1)
    register("modulo", lambda a, b: require_integer(a) % require_integer(b), 2, 2)
    register("quotient", truncate_quotient, 2, 2)
    register("expt", numeric(pow), 2, 2)
    register("abs", numeric(abs), 1, 1)
    for name, relation in (("=", operator.eq), ("<", operator.lt), (">", operator.gt),
                           ("<=", operator.le), (">=", operator.ge)):
        register(name, compare(relation), 2)
    register("not", lambda value: not is_true(value), 1, 1)
    register("cons", Pair, 2, 2)
    register("car", lambda value: require_pair(value).car, 1, 1)
    register("cdr", lambda value: require_pair(value).cdr, 1, 1)
    register("list", lambda *values: make_list(values))
    register("length", lambda value: len(list_items(value)), 1, 1)
    register("append", append)
    predicates = {
        "null?": lambda value: value is NIL,
        "pair?": lambda value: isinstance(value, Pair),
        "list?": is_list,
        "number?": is_number,
        "boolean?": lambda value: type(value) is bool,
        "symbol?": lambda value: isinstance(value, Symbol),
        "string?": lambda value: type(value) is str,
        "procedure?": lambda value: isinstance(value, (Builtin, Closure)),
        "zero?": numeric(lambda value: value == 0),
        "even?": numeric(lambda value: value % 2 == 0),
        "odd?": numeric(lambda value: value % 2 != 0),
    }
    for name, function in predicates.items():
        register(name, function, 1, 1)
    register("eq?", eq, 2, 2)
    register("equal?", equal, 2, 2)

    def display(value):
        output.write(format_value(value, display=True))

    def newline():
        output.write("\n")

    register("display", display, 1, 1)
    register("newline", newline, 0, 0)
    return environment
