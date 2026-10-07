"""CLI: evaluate UTF-8 files in order, or read a program from standard input."""

import sys
from pathlib import Path

# Keep both `python src/main.py` and `python -m src.main` usable.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.errors import SchemeError
from src.evaluator import evaluate
from src.parser import parse
from src.primitives import create_global_environment
from src.printer import format_value


def run(source, environment, output):
    for expression in parse(source):
        value = evaluate(expression, environment)
        if value is not None:
            output.write(format_value(value) + "\n")


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    # Match UTF-8 input/output on Windows as well as POSIX, including pipes.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", newline="\n")
    environment = create_global_environment(sys.stdout)
    try:
        if arguments:
            for filename in arguments:
                run(Path(filename).read_text(encoding="utf-8-sig"), environment, sys.stdout)
        else:
            run(sys.stdin.read().removeprefix("\ufeff"), environment, sys.stdout)
    except (SchemeError, OSError, UnicodeError, RecursionError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
