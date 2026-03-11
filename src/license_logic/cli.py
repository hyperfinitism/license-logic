# SPDX-License-Identifier: MIT

from __future__ import annotations

import argparse

from license_logic import (
    equivalent,
    implies,
    parse,
    to_cnf_string,
    to_dnf_string,
    to_string,
)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="license-logic")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_parse = sub.add_parser("parse", help="parse and pretty-print expression")
    ap_parse.add_argument("expr")

    ap_cnf = sub.add_parser("cnf", help="convert to exact CNF and print as expression")
    ap_cnf.add_argument("expr")

    ap_dnf = sub.add_parser("dnf", help="convert to exact DNF and print as expression")
    ap_dnf.add_argument("expr")

    ap_equiv = sub.add_parser("equiv", help="check logical equivalence")
    ap_equiv.add_argument("a")
    ap_equiv.add_argument("b")

    ap_impl = sub.add_parser("implies", help="check implication (a -> b)")
    ap_impl.add_argument("a")
    ap_impl.add_argument("b")

    ns = ap.parse_args(argv)

    if ns.cmd == "parse":
        fml = parse(ns.expr)
        print(to_string(fml))
        return

    if ns.cmd == "cnf":
        print(to_cnf_string(ns.expr))
        return

    if ns.cmd == "dnf":
        print(to_dnf_string(ns.expr))
        return

    if ns.cmd == "equiv":
        ok = equivalent(ns.a, ns.b)
        print("true" if ok else "false")
        print("true" if ok else "false")
        return 0 if ok else 1

    if ns.cmd == "implies":
        ok = implies(ns.a, ns.b)
        print("true" if ok else "false")
        return 0 if ok else 1

    raise SystemExit(2)
