# SPDX-License-Identifier: MIT

from __future__ import annotations

from pysat.solvers import Solver

from ._tseitin import encode_tseitin_cnf
from .formula import And, Node, Not, Or


def _sat(cnf, assumptions=None) -> bool:
    assumptions = assumptions or []
    with Solver(name="glucose3", bootstrap_with=cnf.clauses) as s:
        result = s.solve(assumptions=assumptions)
        return False if result is None else result


def equivalent(a: Node, b: Node) -> bool:
    """
    a <-> b  is valid  iff  (a XOR b) is UNSAT.
    """
    # XOR = (a ∧ ¬b) ∨ (¬a ∧ b)
    xor = Or(And(a, Not(b)), And(Not(a), b))
    enc = encode_tseitin_cnf(xor)
    # enforce root True
    return not _sat(enc.cnf, assumptions=[enc.root])


def implies(a: Node, b: Node) -> bool:
    """
    a -> b  is valid  iff  (a ∧ ¬b) is UNSAT.
    """
    bad = And(a, Not(b))
    enc = encode_tseitin_cnf(bad)
    return not _sat(enc.cnf, assumptions=[enc.root])
