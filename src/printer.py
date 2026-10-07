"""Scheme output formatting; never expose Python representations."""

from .values import NIL, Builtin, Closure, Pair, Symbol


def format_value(value, display=False):
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if value is NIL:
        return "()"
    if isinstance(value, Symbol):
        return str(value)
    if isinstance(value, str):
        if display:
            return value
        escaped = (value.replace("\\", "\\\\").replace('"', '\\"')
                   .replace("\n", "\\n").replace("\t", "\\t"))
        return '"' + escaped + '"'
    if isinstance(value, Pair):
        items = []
        while isinstance(value, Pair):
            items.append(format_value(value.car, display=display))
            value = value.cdr
        if value is not NIL:
            items.extend([".", format_value(value, display=display)])
        return "(" + " ".join(items) + ")"
    if isinstance(value, (Builtin, Closure)):
        return "#<procedure>"
    if value is None:
        return "#<unspecified>"
    return str(value)
