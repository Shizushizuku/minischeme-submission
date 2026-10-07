"""Read Scheme expressions as values and pair chains, including dotted data."""

import re

from .errors import SchemeError
from .lexer import tokenize
from .values import NIL, Symbol, make_list


INTEGER = re.compile(r"[+-]?[0-9]+\Z")
FLOAT = re.compile(
    r"[+-]?(?:(?:[0-9]+\.[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?"
    r"|[0-9]+[eE][+-]?[0-9]+)\Z"
)


class Reader:
    def __init__(self, source):
        self.tokens = iter(tokenize(source))
        self.current = next(self.tokens, None)

    def take(self):
        token = self.current
        if token is None:
            raise SchemeError("unexpected end of input")
        self.current = next(self.tokens, None)
        return token

    def read(self):
        token = self.take()
        if token.kind == "'":
            return make_list([Symbol("quote"), self.read()])
        if token.kind == "(":
            items = []
            tail = NIL
            while self.current is not None and self.current.kind != ")":
                if self.current.kind == ".":
                    if not items:
                        raise SchemeError(f"line {token.line}: dot must follow an element")
                    self.take()
                    tail = self.read()
                    if self.current is None or self.current.kind != ")":
                        raise SchemeError(f"line {token.line}: expected ')' after dotted tail")
                    break
                items.append(self.read())
            if self.current is None:
                raise SchemeError(f"line {token.line}: unclosed list")
            self.take()
            return make_list(items, tail)
        if token.kind in (")", "."):
            raise SchemeError(f"line {token.line}, column {token.column}: unexpected {token.value}")
        if token.kind == "string":
            return token.value
        if token.value in ("#t", "#f"):
            return token.value == "#t"
        if INTEGER.fullmatch(token.value):
            return int(token.value)
        if FLOAT.fullmatch(token.value):
            return float(token.value)
        return Symbol(token.value)


def parse(source):
    """Yield top-level expressions in source order."""
    reader = Reader(source)
    while reader.current is not None:
        yield reader.read()
