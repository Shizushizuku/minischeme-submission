"""Tokenize comments, punctuation, atoms, and escaped strings."""

from dataclasses import dataclass

from .errors import SchemeError


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    column: int


def tokenize(source):
    index, line, column = 0, 1, 1

    def advance():
        nonlocal index, line, column
        char = source[index]
        index += 1
        if char == "\n":
            line, column = line + 1, 1
        else:
            column += 1
        return char

    while index < len(source):
        char = source[index]
        if char.isspace():
            advance()
            continue
        if char == ";":
            while index < len(source) and source[index] != "\n":
                advance()
            continue
        start_line, start_column = line, column
        if char in "()'":
            yield Token(char, advance(), start_line, start_column)
        elif char == '"':
            advance()
            chars = []
            escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
            while index < len(source) and source[index] != '"':
                char = advance()
                if char == "\\":
                    if index >= len(source):
                        break
                    char = advance()
                    if char not in escapes:
                        raise SchemeError(
                            f"line {line}, column {column - 1}: unknown escape \\{char}"
                        )
                    char = escapes[char]
                chars.append(char)
            if index >= len(source):
                raise SchemeError(f"line {start_line}: unterminated string")
            advance()
            yield Token("string", "".join(chars), start_line, start_column)
        else:
            chars = []
            while index < len(source):
                char = source[index]
                if char.isspace() or char in "()'\";":
                    break
                chars.append(advance())
            value = "".join(chars)
            yield Token("." if value == "." else "atom", value, start_line, start_column)
