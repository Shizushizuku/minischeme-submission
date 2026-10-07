"""Evaluate special forms and procedure calls in lexical environments."""

from .environment import Environment
from .errors import SchemeError
from .values import Builtin, Closure, Pair, Symbol, is_true, list_items


def check_count(items, minimum, maximum=None):
    if len(items) < minimum or (maximum is not None and len(items) > maximum):
        raise SchemeError("wrong number of expressions")


def require_symbol(value):
    if not isinstance(value, Symbol):
        raise SchemeError("expected a symbol")
    return value


def make_closure(parameters, body, environment):
    names = [require_symbol(name) for name in list_items(parameters)]
    if len(set(names)) != len(names):
        raise SchemeError("duplicate parameter name")
    check_count(body, 1)
    return Closure(names, body, environment)


def prepare_body(body, environment):
    """Run preceding expressions; return the last for the evaluator's loop."""
    if not body:
        return None
    for expression in body[:-1]:
        evaluate(expression, environment)
    return body[-1]


def apply(procedure, arguments):
    """Call a builtin, or return a closure's final expression and local frame."""
    if isinstance(procedure, Builtin):
        return procedure.invoke(arguments)
    if not isinstance(procedure, Closure):
        raise SchemeError("attempt to call a non-procedure")
    if len(arguments) != len(procedure.parameters):
        raise SchemeError("procedure: wrong number of arguments")
    local = Environment(procedure.environment)
    for name, value in zip(procedure.parameters, arguments):
        local.define(name, value)
    return prepare_body(procedure.body, local), local


def evaluate(expression, environment):
    # Tail positions reuse this loop, so simple tail recursion is stack-safe.
    while True:
        if isinstance(expression, Symbol):
            return environment.lookup(expression)
        if not isinstance(expression, Pair):
            return expression
        operator = expression.car
        operands = list_items(expression.cdr)
        form = str(operator) if isinstance(operator, Symbol) else None

        if form == "quote":
            check_count(operands, 1, 1)
            return operands[0]
        if form == "if":
            check_count(operands, 2, 3)
            if is_true(evaluate(operands[0], environment)):
                expression = operands[1]
            else:
                expression = operands[2] if len(operands) == 3 else None
        elif form == "cond":
            expression = None
            for clause in operands:
                parts = list_items(clause)
                check_count(parts, 1)
                is_else = isinstance(parts[0], Symbol) and parts[0] == "else"
                test = True if is_else else evaluate(parts[0], environment)
                if is_true(test):
                    if len(parts) == 1:
                        return test
                    expression = prepare_body(parts[1:], environment)
                    break
        elif form in ("and", "or"):
            if not operands:
                return form == "and"
            for operand in operands[:-1]:
                result = evaluate(operand, environment)
                if (form == "and" and not is_true(result)) or (
                    form == "or" and is_true(result)
                ):
                    return result
            expression = operands[-1]
        elif form == "define":
            check_count(operands, 2)
            target = operands[0]
            if isinstance(target, Pair):
                name = require_symbol(target.car)
                value = make_closure(target.cdr, operands[1:], environment)
            else:
                check_count(operands, 2, 2)
                name = require_symbol(target)
                value = evaluate(operands[1], environment)
            environment.define(name, value)
            return name
        elif form == "lambda":
            check_count(operands, 2)
            return make_closure(operands[0], operands[1:], environment)
        elif form == "let":
            check_count(operands, 2)
            bindings = []
            for binding in list_items(operands[0]):
                parts = list_items(binding)
                check_count(parts, 2, 2)
                name = require_symbol(parts[0])
                bindings.append((name, parts[1]))
            # Every initializer sees the outer environment, never the new frame.
            values = [(name, evaluate(value, environment)) for name, value in bindings]
            environment = Environment(environment)
            for name, value in values:
                environment.define(name, value)
            expression = prepare_body(operands[1:], environment)
        elif form == "begin":
            expression = prepare_body(operands, environment)
        else:
            procedure = evaluate(operator, environment)
            arguments = [evaluate(operand, environment) for operand in operands]
            result = apply(procedure, arguments)
            if isinstance(procedure, Builtin):
                return result
            expression, environment = result
