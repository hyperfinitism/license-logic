# SPDX-License-Identifier: MIT

from license_logic.normal_forms import to_cnf, to_dnf
from license_logic.spdx import parse


def test_cnf_simple():
    ast = parse("A OR (B AND C)")
    cnf = to_cnf(ast)
    # expected: (A OR B) AND (A OR C)
    assert any(("A", False) in clause and ("B", False) in clause for clause in cnf)
    assert any(("A", False) in clause and ("C", False) in clause for clause in cnf)


def test_dnf_simple():
    ast = parse("(A OR B) AND C")
    dnf = to_dnf(ast)
    # expected: (A AND C) OR (B AND C)
    assert any(("A", False) in term and ("C", False) in term for term in dnf)
    assert any(("B", False) in term and ("C", False) in term for term in dnf)


def test_not_works():
    ast = parse("A AND NOT B")
    cnf = to_cnf(ast)
    assert any(("B", True) in clause for clause in cnf)  # ¬B somewhere
