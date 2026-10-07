"""Runtime values shared by the reader, evaluator, and standard library."""

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from .errors import SchemeError


class Symbol(str):
    """A name, deliberately distinct from a Scheme string."""


class Nil:
    """The unique empty list; Scheme considers it true."""


NIL = Nil()


@dataclass(eq=False)
class Pair:
    car: Any
    cdr: Any


def make_list(items: Iterable, tail=NIL):
    for item in reversed(list(items)):
        tail = Pair(item, tail)
    return tail


def list_items(value):
    """Unpack a proper list, rejecting improper tails."""
    items = []
    while isinstance(value, Pair):
        items.append(value.car)
        value = value.cdr
    if value is not NIL:
        raise SchemeError("expected a proper list")
    return items


def is_number(value):
    # Python bool subclasses int, but Scheme booleans are not numbers.
    return type(value) in (int, float)


def is_true(value):
    return value is not False


@dataclass(eq=False)
class Builtin:
    name: str
    function: Callable
    minimum: int = 0
    maximum: Any = None

    def invoke(self, args):
        if len(args) < self.minimum or (
            self.maximum is not None and len(args) > self.maximum
        ):
            raise SchemeError(f"{self.name}: wrong number of arguments")
        try:
            return self.function(*args)
        except (ArithmeticError, TypeError, ValueError) as error:
            raise SchemeError(f"{self.name}: {error}") from error


@dataclass(eq=False)
class Closure:
    parameters: list
    body: list
    environment: Any
