# SPDX-License-Identifier: MIT

from __future__ import annotations

import re

from .formula import And, Node, Not, Or, Var

# Identifiers include SPDX-like characters
TOKEN_RE = re.compile(
    r"""
    \s*(
        \(|\)|
        \s+AND\s+|\s+OR\s+|\s+NOT\s+|\s+WITH\s+|
        [A-Za-z0-9.\-+]+
    )\s*
    """,
    re.VERBOSE,
)


class ParseError(ValueError):
    pass


def _tokenize(expr: str) -> list[str]:
    if not expr or not expr.strip():
        raise ParseError("empty expression")
    toks = TOKEN_RE.findall(expr)
    if not toks:
        raise ParseError(f"cannot tokenize: {expr!r}")

    # validate full consumption (rough but effective)
    joined = "".join(re.findall(r"\S+", expr))
    joined2 = "".join(re.findall(r"\S+", "".join(toks)))
    if joined != joined2:
        raise ParseError(f"cannot tokenize completely: {expr!r}")
    return toks


class _Parser:
    def __init__(self, toks: list[str]):
        self.toks = toks
        self.i = 0

    def peek(self) -> str | None:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def eat(self, t: str) -> None:
        if self.peek() != t:
            raise ParseError(f"expected {t}, got {self.peek()}")
        self.i += 1

    # expr := term (OR term)*
    def parse_expr(self) -> Node:
        node = self.parse_term()
        while self.peek() == "OR":
            self.eat("OR")
            rhs = self.parse_term()
            node = Or(node, rhs)
        return node

    # term := unary (AND unary)*
    def parse_term(self) -> Node:
        node = self.parse_unary()
        while self.peek() == "AND":
            self.eat("AND")
            rhs = self.parse_unary()
            node = And(node, rhs)
        return node

    # unary := NOT unary | factor
    def parse_unary(self) -> Node:
        if self.peek() == "NOT":
            self.eat("NOT")
            return Not(self.parse_unary())
        return self.parse_factor()

    # factor := atom | '(' expr ')'
    def parse_factor(self) -> Node:
        t = self.peek()
        if t == "(":
            self.eat("(")
            node = self.parse_expr()
            if self.peek() != ")":
                raise ParseError("missing ')'")
            self.eat(")")
            return node
        return self.parse_atom()

    # atom := ID (WITH ID)?
    def parse_atom(self) -> Node:
        t = self.peek()
        if t is None:
            raise ParseError("unexpected end")
        if t in ("AND", "OR", "NOT", "WITH", "(", ")"):
            raise ParseError(f"unexpected token {t}")
        self.i += 1
        name = t
        if self.peek() == "WITH":
            self.eat("WITH")
            t2 = self.peek()
            if t2 is None or t2 in ("AND", "OR", "NOT", "WITH", "(", ")"):
                raise ParseError("WITH must be followed by an identifier")
            self.i += 1
            name = f"{name} WITH {t2}"
        return Var(name)


def parse(expr: str) -> Node:
    toks = _tokenize(expr)
    p = _Parser(toks)
    node = p.parse_expr()
    if p.peek() is not None:
        raise ParseError(f"trailing token {p.peek()} in {expr!r}")
    return node


def to_string(node: Node) -> str:
    # canonical-ish pretty printer with precedence:
    # NOT > AND > OR
    def prec(n: Node) -> int:
        if isinstance(n, Var):
            return 4
        if isinstance(n, Not):
            return 3
        if isinstance(n, And):
            return 2
        if isinstance(n, Or):
            return 1
        return 0

    def go(n: Node, parent_prec: int) -> str:
        if isinstance(n, Var):
            return n.name
        if isinstance(n, Not):
            s = f"NOT {go(n.child, prec(n))}"
            return s if prec(n) >= parent_prec else f"({s})"
        if isinstance(n, And):
            s = f"{go(n.left, prec(n))} AND {go(n.right, prec(n))}"
            return s if prec(n) >= parent_prec else f"({s})"
        if isinstance(n, Or):
            s = f"{go(n.left, prec(n))} OR {go(n.right, prec(n))}"
            return s if prec(n) >= parent_prec else f"({s})"
        raise TypeError(n)

    return go(node, 0)
