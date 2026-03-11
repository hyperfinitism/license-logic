# SPDX-License-Identifier: MIT

from license_logic.sat import equivalent, implies
from license_logic.spdx import parse


def test_equiv_commutativity():
    assert equivalent(parse("NOT A OR NOT B"), parse("NOT (A AND B)"))


def test_implies():
    assert implies(parse("A AND B"), parse("A"))
    assert not implies(parse("A"), parse("A AND B"))


def test_demorgan():
    assert equivalent(parse("NOT (A AND B)"), parse("NOT A OR NOT B"))
