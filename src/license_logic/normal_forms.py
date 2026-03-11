# SPDX-License-Identifier: MIT

from __future__ import annotations

from .formula import And, Node, Not, Or, Var

# Literal: (name, is_neg)
Literal = tuple[str, bool]  # (atom, negated?)
Clause = frozenset[Literal]  # OR of literals
CNF = list[Clause]  # AND of clauses
Term = frozenset[Literal]  # AND of literals
DNF = list[Term]  # OR of terms


def _neg_lit(lit: Literal) -> Literal:
    return (lit[0], not lit[1])


def _cnf_true() -> CNF:
    return []  # empty conjunction = True


def _cnf_false() -> CNF:
    return [frozenset()]  # one empty clause = False


def _dnf_true() -> DNF:
    return [frozenset()]  # one empty term = True


def _dnf_false() -> DNF:
    return []  # empty disjunction = False


def _simplify_cnf(cnf: CNF) -> CNF:
    # remove duplicate clauses
    uniq = list(dict.fromkeys(cnf))

    # if any clause contains both x and ¬x, it's a tautological clause; drop it
    cleaned = []
    for c in uniq:
        is_tautology = False
        for name, neg in c:
            if (name, not neg) in c:
                is_tautology = True
                break
        if not is_tautology:
            cleaned.append(c)

    # subsumption: if C ⊆ D then D redundant
    cleaned.sort(key=lambda c: (len(c), sorted(c)))
    out: list[Clause] = []
    for c in cleaned:
        if any(k.issubset(c) for k in out):
            continue
        out.append(c)
    return out


def _simplify_dnf(dnf: DNF) -> DNF:
    uniq = list(dict.fromkeys(dnf))

    # if term contains both x and ¬x, it's contradictory; drop it
    cleaned = []
    for t in uniq:
        is_contradictory = False
        for name, neg in t:
            if (name, not neg) in t:
                is_contradictory = True
                break
        if not is_contradictory:
            cleaned.append(t)

    # subsumption: if T ⊆ U then U redundant in DNF? (since OR of ANDs)
    cleaned.sort(key=lambda t: (len(t), sorted(t)))
    out: list[Term] = []
    for t in cleaned:
        if any(k.issubset(t) for k in out):
            continue
        out.append(t)
    return out


def _cnf_and(a: CNF, b: CNF) -> CNF:
    # True ∧ X = X ; False ∧ X = False
    if a == _cnf_false() or b == _cnf_false():
        return _cnf_false()
    return _simplify_cnf(a + b)


def _cnf_or(a: CNF, b: CNF) -> CNF:
    # Distribute: (∧Ai) ∨ (∧Bj) = ∧(Ai ∪ Bj)
    if a == _cnf_true():
        # True OR X = True  (empty conjunction denotes True)
        return _cnf_true()
    if b == _cnf_true():
        return _cnf_true()
    if a == _cnf_false():
        return b
    if b == _cnf_false():
        return a
    out: CNF = []
    for ca in a:
        for cb in b:
            out.append(frozenset(set(ca) | set(cb)))
    return _simplify_cnf(out)


def _dnf_or(a: DNF, b: DNF) -> DNF:
    # False ∨ X = X ; True ∨ X = True
    if a == _dnf_true() or b == _dnf_true():
        return _dnf_true()
    return _simplify_dnf(a + b)


def _dnf_and(a: DNF, b: DNF) -> DNF:
    # Distribute: (∨Ai) ∧ (∨Bj) = ∨(Ai ∪ Bj)
    if a == _dnf_false() or b == _dnf_false():
        return _dnf_false()
    if a == _dnf_true():
        return b
    if b == _dnf_true():
        return a
    out: DNF = []
    for ta in a:
        for tb in b:
            out.append(frozenset(set(ta) | set(tb)))
    return _simplify_dnf(out)


def _nnf(node: Node) -> Node:
    # push NOT down to variables (Negation Normal Form)
    if isinstance(node, Var):
        return node
    if isinstance(node, Not):
        c = node.child
        if isinstance(c, Var):
            return node
        if isinstance(c, Not):
            return _nnf(c.child)
        if isinstance(c, And):
            return Or(_nnf(Not(c.left)), _nnf(Not(c.right)))
        if isinstance(c, Or):
            return And(_nnf(Not(c.left)), _nnf(Not(c.right)))
        raise TypeError(c)
    if isinstance(node, And):
        return And(_nnf(node.left), _nnf(node.right))
    if isinstance(node, Or):
        return Or(_nnf(node.left), _nnf(node.right))
    raise TypeError(node)


def to_cnf(node: Node) -> CNF:
    """
    Exact CNF conversion by distributivity after converting to NNF.
    CNF is a list of clauses; clause is a frozenset of (atom, negated).
    """
    n = _nnf(node)

    def go(x: Node) -> CNF:
        if isinstance(x, Var):
            return [frozenset([(x.name, False)])]
        if isinstance(x, Not):
            assert isinstance(x.child, Var)
            v = x.child
            return [frozenset([(v.name, True)])]
        if isinstance(x, And):
            return _cnf_and(go(x.left), go(x.right))
        if isinstance(x, Or):
            return _cnf_or(go(x.left), go(x.right))
        raise TypeError(x)

    return go(n)


def to_dnf(node: Node) -> DNF:
    """
    Exact DNF conversion by distributivity after converting to NNF.
    DNF is a list of terms; term is a frozenset of (atom, negated).
    """
    n = _nnf(node)

    def go(x: Node) -> DNF:
        if isinstance(x, Var):
            return [frozenset([(x.name, False)])]
        if isinstance(x, Not):
            assert isinstance(x.child, Var)
            v = x.child
            return [frozenset([(v.name, True)])]
        if isinstance(x, Or):
            return _dnf_or(go(x.left), go(x.right))
        if isinstance(x, And):
            return _dnf_and(go(x.left), go(x.right))
        raise TypeError(x)

    return go(n)


def cnf_to_fml(cnf: CNF) -> Node:
    # empty conjunction = True, but we don't have True const; encode as (A OR NOT A)
    # caller should avoid cnf(True) for pretty output; API handles it specially.
    def lit_fml(lit: Literal) -> Node:
        name, neg = lit
        return Not(Var(name)) if neg else Var(name)

    if cnf == _cnf_true():
        return Var("TRUE")

    clauses: list[Node] = []
    for c in cnf:
        if len(c) == 0:
            return Var("FALSE")
        lits = [lit_fml(lit) for lit in sorted(c)]
        disj = lits[0]
        for t in lits[1:]:
            disj = Or(disj, t)
        clauses.append(disj)

    conj = clauses[0]
    for cl in clauses[1:]:
        conj = And(conj, cl)
    return conj


def dnf_to_fml(dnf: DNF) -> Node:
    def lit_fml(lit: Literal) -> Node:
        name, neg = lit
        return Not(Var(name)) if neg else Var(name)

    if dnf == _dnf_false():
        return Var("FALSE")

    terms: list[Node] = []
    for t in dnf:
        if len(t) == 0:
            return Var("TRUE")
        lits = [lit_fml(lit) for lit in sorted(t)]
        conj = lits[0]
        for u in lits[1:]:
            conj = And(conj, u)
        terms.append(conj)

    disj = terms[0]
    for tm in terms[1:]:
        disj = Or(disj, tm)
    return disj
