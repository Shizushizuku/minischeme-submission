"""Specification-based regression tests, independent of the supplied grader.

Run from the project root: python -m unittest discover -s tests -v
"""

import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.errors import SchemeError
from src.main import run
from src.primitives import create_global_environment


ROOT = Path(__file__).resolve().parents[1]


def interpret(source):
    output = io.StringIO()
    run(source, create_global_environment(output), output)
    return output.getvalue()


class SpecificationTests(unittest.TestCase):
    def check(self, source, expected):
        self.assertEqual(interpret(source), expected)

    def test_arithmetic(self):
        self.check("""
            (+) (*) (+ 1 2 3) (- 5) (- 10 4 1) (* -2 3 4)
            (/ 7 2) (/ -7 2) (/ 7 -2) (/ -7 -2) (/ 100 3 2)
            (/ 2) (modulo 17 5) (modulo -17 5)
            (quotient -7 2) (expt 2 10) (abs -4)
        """, "0\n1\n6\n-5\n5\n-24\n3\n-3\n-3\n3\n16\n0.5\n2\n3\n-3\n1024\n4\n")

    def test_large_integer_division_is_exact(self):
        value = 10 ** 100 + 17
        self.check(f"(/ {value} 3) (quotient {-value} 3)",
                   f"{value // 3}\n{- (value // 3)}\n")

    def test_optional_floats(self):
        self.check("1.5 -0.25 .5 1e2 2.5e-1 (/ 7.0 2) (+ 1 0.5)",
                   "1.5\n-0.25\n0.5\n100.0\n0.25\n3.5\n1.5\n")

    def test_comparisons(self):
        self.check("""
            (= 3 3 3) (= 3 3 4) (< 1 2 3) (< 1 3 2)
            (> 3 2 1) (<= 1 1 2) (>= 3 3 2) (> 2 2)
            (< 'a 'b 'c) (= 'name 'name) (>= 'b 'a)
        """, "#t\n#f\n#t\n#f\n#t\n#t\n#t\n#f\n#t\n#t\n#t\n")

    def test_truthiness_and_short_circuit(self):
        self.check("""
            (and) (or) (and #f (/ 1 0)) (or 'ok (/ 1 0))
            (and 0 '() "") (or #f 0 missing) (not 0) (not '())
            (not "") (not #f) (if '() 1 missing) (if "" 2 missing)
        """, '#t\n#f\n#f\nok\n""\n0\n#f\n#f\n#f\n#t\n1\n2\n')

    def test_if_and_no_value(self):
        self.check("""
            (if #f 99) (if #t 1 missing) (if #f missing 2)
            (begin) (cond) (cond (#f 1))
            (if (if #f 0) 3 4)
        """, "1\n2\n3\n")

    def test_cond_sequence_and_test_only_clause(self):
        self.check("""
            (cond (#f missing) ((+ 1 2)))
            (cond ((begin (display "t") 0) (display "b") 7) (else missing))
            (cond (#f 1) (else (define x 3) (+ x 2)))
            (cond ('(a b)))
        """, "3\ntb7\n5\n(a b)\n")

    def test_define_and_multiple_body_expressions(self):
        self.check("""
            (define x 4) (define x (+ x 1)) x
            (define (f a) (define b (+ a 1)) (* a b)) (f 3)
            ((lambda () (display "x") 9))
            (begin (define z 4) (define z 5) z)
        """, "x\nx\n5\nf\n12\nx9\n5\n")

    def test_lexical_closures(self):
        self.check("""
            (define x 10) (define (f y) (+ x y))
            (let ((x 100)) (f 1))
            (define (make n) (lambda (x) (+ n x)))
            (define a (make 3)) (define b (make 8))
            (a 2) (b 2) (a 2)
            (let ((n 500)) (a 2))
        """, "x\nf\n11\nmake\na\nb\n5\n10\n5\n5\n")

    def test_let_parallel_bindings_and_scope(self):
        self.check("""
            (define x 10)
            (let ((x 1) (y x)) (define z (+ x y)) z)
            x (let () 1 2 3)
            (let ((a 2)) (let ((a 5) (b a)) (+ a b)))
            (let ((x 1) (x (+ x 2))) x)
        """, "x\n11\n10\n3\n7\n12\n")

    def test_operator_and_arguments_evaluate_left_to_right(self):
        self.check("""
            ((begin (display "f") +)
             (begin (display "a") 1) (begin (display "b") 2))
            (let ((x (begin (display "x") 1))
                  (y (begin (display "y") 2))) (+ x y))
        """, "fab3\nxy3\n")

    def test_recursive_and_mutually_recursive_functions(self):
        self.check("""
            (define (fact n) (if (= n 0) 1 (* n (fact (- n 1)))))
            (fact 10)
            (define (ev n) (if (= n 0) #t (od (- n 1))))
            (define (od n) (if (= n 0) #f (ev (- n 1))))
            (ev 30) (od 31)
            (define (sum n acc) (if (= n 0) acc (sum (- n 1) (+ n acc))))
            (sum 5000 0)
        """, "fact\n3628800\nev\nod\n#t\n#t\nsum\n12502500\n")

    def test_pairs_and_list_operations(self):
        self.check("""
            '() '(1 (2 3) 4) (cons 1 2) '(1 2 . 3)
            (car '(1 2)) (cdr '(1 2)) (cdr (cons 1 2))
            (list) (list 1 (+ 1 1)) (length '()) (length '(a b c))
            (append) (append '() '(1 2) '() '(3))
            (list? '(1 . 2)) (list? '(1 . (2 . ())))
            (null? '()) (null? '(1)) (pair? '(1)) (pair? '())
            (list? 1) (pair? (cons 1 2))
        """, "()\n(1 (2 3) 4)\n(1 . 2)\n(1 2 . 3)\n1\n(2)\n2\n()\n(1 2)\n0\n3\n()\n(1 2 3)\n#f\n#t\n#t\n#f\n#t\n#f\n#f\n#t\n")

    def test_quote_abbreviation_and_case_sensitive_symbols(self):
        self.check("""
            'x (quote (+ 1 2)) ''x
            (define foo 1) (define FOO 2) (list foo FOO)
            (define 正 8) 正
        """, "x\n(+ 1 2)\n(quote x)\nfoo\nFOO\n(1 2)\n正\n8\n")

    def test_predicates(self):
        self.check("""
            (number? 1) (number? #t) (number? 'x) (number? 0.5)
            (boolean? #f) (boolean? 0)
            (symbol? 'a) (symbol? "a") (string? "a") (string? 'a)
            (procedure? car) (procedure? (lambda () 1)) (procedure? 1)
            (zero? 0) (zero? 1) (even? -4) (odd? -3) (odd? 2)
        """, "#t\n#f\n#f\n#t\n#t\n#f\n#t\n#f\n#t\n#f\n#t\n#t\n#f\n#t\n#f\n#t\n#t\n#f\n")

    def test_identity_and_structural_equality(self):
        self.check("""
            (eq? '() '()) (eq? '(1) '(1))
            (define p (list 1 2)) (define alias p)
            (eq? p alias) (eq? p (list 1 2)) (equal? p (list 1 2))
            (eq? (cdr (cons 0 p)) p) (eq? 'a 'a) (eq? #t 1)
            (equal? #t 1) (equal? 'a "a") (eq? 0 #f)
            (equal? '(1 ("a" #f) . z) (cons 1 (cons (list "a" #f) 'z)))
            (equal? '(1 2) '(1 3)) (equal? '(1) '(1 2))
            (equal? "a" "a") (eq? + +) (equal? + -)
        """, "#t\n#f\np\nalias\n#t\n#f\n#t\n#t\n#t\n#f\n#f\n#f\n#f\n#t\n#f\n#f\n#t\n#t\n#f\n")

    def test_map_and_filter_defined_in_scheme(self):
        self.check("""
            (define (map f xs)
              (if (null? xs) '() (cons (f (car xs)) (map f (cdr xs)))))
            (define (filter f xs)
              (cond ((null? xs) '())
                    ((f (car xs)) (cons (car xs) (filter f (cdr xs))))
                    (else (filter f (cdr xs)))))
            (map (lambda (x) (* x x)) '(1 2 3 4))
            (filter odd? '(1 2 3 4 5)) (map abs '())
        """, "map\nfilter\n(1 4 9 16)\n(1 3 5)\n()\n")

    def test_strings_comments_and_output(self):
        self.check(r'''
            ; ignored unmatched delimiters: ( ' "
            "hello" "a\nb\tc\"d\\e" "; ( ) ' 中文"
            (display "a\nb\tc\"d\\e") (newline)
            (display 'symbol) (display #f) (display '(1 . 2)) (newline)
            (+ 1; comment splits tokens
               2)
        ''', '"hello"\n"a\\nb\\tc\\\"d\\\\e"\n"; ( ) \' 中文"\n'
             'a\nb\tc"d\\e\nsymbol#f(1 . 2)\n3\n')

    def test_empty_input(self):
        self.check(" ; only a comment\n\t", "")

    def test_bad_programs_report_scheme_errors(self):
        for source in ("(", ")", "'", '"unfinished', '"bad\\q"', "(. 1)",
                       "'(1 . 2 3)", "missing", "(1 2)", "(car '())",
                       "(+ #t 1)", "(lambda (x x) x)", "((lambda (x) x))",
                       "(let ((x)) x)", "(if #t)", "(/ 1 0)"):
            with self.subTest(source=source), self.assertRaises(SchemeError):
                interpret(source)


class CommandLineTests(unittest.TestCase):
    def invoke(self, *arguments, source="", cwd=ROOT):
        return subprocess.run(
            [sys.executable, str(ROOT / "src" / "main.py"), *map(str, arguments)],
            input=source.encode("utf-8"), capture_output=True, cwd=cwd, timeout=15,
        )

    def test_stdin_utf8_and_exact_output(self):
        result = self.invoke(source='(define 正 5) 正 (display "你好") (newline)')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "正\n5\n你好\n".encode("utf-8"))
        self.assertEqual(result.stderr, b"")

    def test_multiple_files_share_environment_from_any_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "one.scm", Path(directory) / "two.scm"
            first.write_text("(define x 7)", encoding="utf-8-sig")
            second.write_text("(+ x 5)", encoding="utf-8")
            result = self.invoke(first, second, cwd=directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b"x\n12\n")
        self.assertEqual(self.invoke(source="x").returncode, 1)

    def test_examples_match_documented_outputs(self):
        expected = {
            "01_arithmetic.scm": "3\n5\n12\n3\n2\n3\n1024\n4\n#t\n#t\n#f\n#f\n#t\n#t\n",
            "02_conditionals.scm": "yes\nb\n42\n#f\n#t\ntruthy\n",
            "03_functions.scm": "square\n49\ncube\n27\n7\nmake-adder\nadd5\n15\n107\n",
            "04_recursion.scm": "fact\n3628800\nfib\n610\nsum-to\n5050\n",
            "05_lists.scm": "1\n(2 3)\n(1 2 3)\n(1 . 2)\n(1 2 3)\n4\n(1 2 3 4)\nmap\n(1 4 9 16)\n",
            "06_io.scm": '3\nhello\n"hello"\n"a\\nb"\n',
        }
        for name, output in expected.items():
            with self.subTest(example=name):
                result = self.invoke(ROOT / "example" / name)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, output.encode("utf-8"))

    def test_errors_go_to_stderr(self):
        result = self.invoke(source="(car 1)")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")
        self.assertIn(b"Error:", result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
