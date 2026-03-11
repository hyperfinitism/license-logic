# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass

from pysat.formula import CNF

from .formula import And, Node, Not, Or, Var

Literal = int  # positive for variable, negative for negation


@dataclass
class TseitinResult:
    cnf: CNF
    varmap: dict[str, int]  # original atom -> var id
    root: Literal  # literal representing the whole formula


class _IdPool:
    def __init__(self):
        self.next_id = 1
        self.atom_map: dict[str, int] = {}

    def atom(self, name: str) -> int:
        if name in self.atom_map:
            return self.atom_map[name]
        i = self.next_id
        self.next_id += 1
        self.atom_map[name] = i
        return i

    def fresh(self) -> int:
        i = self.next_id
        self.next_id += 1
        return i


def encode_tseitin_cnf(node: Node) -> TseitinResult:
    """
    Tseitin encoding of an arbitrary boolean formula into CNF.
    Returns CNF + mapping of atom vars + root literal.
    Satisfiability of (root = True) corresponds to satisfiability of node.
    """
    pool = _IdPool()
    cnf = CNF()

    def enc(n: Node) -> Literal:
        if isinstance(n, Var):
            return pool.atom(n.name)
        if isinstance(n, Not):
            a = enc(n.child)
            x = pool.fresh()
            # x <-> ¬a
            # (¬x ∨ ¬a) ∧ (x ∨ a)
            cnf.append([-x, -a])
            cnf.append([x, a])
            return x
        if isinstance(n, And):
            a = enc(n.left)
            b = enc(n.right)
            x = pool.fresh()
            # x <-> (a ∧ b)
            # (¬x ∨ a) ∧ (¬x ∨ b) ∧ (x ∨ ¬a ∨ ¬b)
            cnf.append([-x, a])
            cnf.append([-x, b])
            cnf.append([x, -a, -b])
            return x
        if isinstance(n, Or):
            a = enc(n.left)
            b = enc(n.right)
            x = pool.fresh()
            # x <-> (a ∨ b)
            # (¬a ∨ x) ∧ (¬b ∨ x) ∧ (¬x ∨ a ∨ b)
            cnf.append([-a, x])
            cnf.append([-b, x])
            cnf.append([-x, a, b])
            return x
        raise TypeError(n)

    root = enc(node)
    return TseitinResult(cnf=cnf, varmap=dict(pool.atom_map), root=root)
