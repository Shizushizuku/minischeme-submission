"""Lexical environments: local bindings plus a reference to an outer frame."""

from .errors import SchemeError


class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.bindings = {}

    def define(self, name, value):
        self.bindings[name] = value

    def lookup(self, name):
        frame = self
        while frame is not None:
            if name in frame.bindings:
                return frame.bindings[name]
            frame = frame.parent
        raise SchemeError(f"undefined symbol: {name}")
