# SPDX-License-Identifier: MIT

from __future__ import annotations

# AST node types — re-exported for users who build or inspect formula trees
from .formula import And, Node, Not, Or, Var

# Normal-form conversion (also available for direct import from .normal_forms)
from .normal_forms import cnf_to_fml, dnf_to_fml, to_cnf, to_dnf

# AST-level SAT functions (aliased privately; string-level wrappers defined below)
from .sat import equivalent as _equiv_ast
from .sat import implies as _impl_ast

# String-level parse and pretty-print
from .spdx import parse, to_string


def to_cnf_string(expr: str) -> str:
    fml = parse(expr)
    cnf = to_cnf(fml)
    fml2 = cnf_to_fml(cnf)
    return to_string(fml2)


def to_dnf_string(expr: str) -> str:
    fml = parse(expr)
    dnf = to_dnf(fml)
    fml2 = dnf_to_fml(dnf)
    return to_string(fml2)


def equivalent(expr1: str, expr2: str) -> bool:
    a = parse(expr1)
    b = parse(expr2)
    return _equiv_ast(a, b)


def implies(expr1: str, expr2: str) -> bool:
    a = parse(expr1)
    b = parse(expr2)
    return _impl_ast(a, b)


__all__ = [
    # AST node types
    "Node",
    "Var",
    "Not",
    "And",
    "Or",
    # String-level API
    "parse",
    "to_string",
    "to_cnf_string",
    "to_dnf_string",
    "equivalent",
    "implies",
]
