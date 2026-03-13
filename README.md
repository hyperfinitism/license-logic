# license-logic

![SemVer](https://img.shields.io/badge/license--logic-pre--release-blue)
![MSPV](https://img.shields.io/badge/python-3.11+-orange.svg)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](https://opensource.org/licenses/MIT)

`license-logic` is a propositional-logic toolkit for reasoning about composite license expressions.

It parses [SPDX-style](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/) compound license expressions (`AND`, `OR`, `WITH` and non-standard `NOT`) into a formula AST and provides:

- **Normal-form conversion** — exact CNF and DNF (by distributivity, not Tseitin)
- **Equivalence checking** — are two expressions logically equivalent?
- **Implication checking** — does one expression logically imply another?

These operations are powered by a SAT solver ([PySAT](https://pysathq.github.io/)) via Tseitin encoding. In effect, `license-logic` also works as a **CLI wrapper around PySAT** — you feed it readable Boolean expressions instead of raw DIMACS clauses, and it handles tokenisation, parsing, Tseitin encoding, and solver invocation behind the scenes.

## Installation

```
pip install git+https://github.com/hyperfinitism/license-logic
```

## Quick start

### CLI

```sh
# Pretty-print a parsed expression
license-logic parse "MIT OR (Apache-2.0 AND BSD-3-Clause)"

# Convert to CNF / DNF
license-logic cnf "MIT OR (Apache-2.0 AND BSD-3-Clause)"
license-logic dnf "(MIT OR Apache-2.0) AND BSD-3-Clause"

# Check equivalence
license-logic equiv "NOT (A AND B)" "NOT A OR NOT B"

# Check implication (a → b)
license-logic implies "A AND B" "A"
```

### Python API

```python
from license_logic import (
    parse, to_string,
    to_cnf_string, to_dnf_string,
    equivalent, implies,
)

# Parse and round-trip
ast = parse("MIT OR (Apache-2.0 AND BSD-3-Clause)")
print(to_string(ast))

# Normal forms (string in, string out)
print(to_cnf_string("MIT OR (Apache-2.0 AND BSD-3-Clause)"))
print(to_dnf_string("(MIT OR Apache-2.0) AND BSD-3-Clause"))

# Logical queries
equivalent("NOT (A AND B)", "NOT A OR NOT B")  # True
implies("A AND B", "A")                        # True
```

## What this tool does

Every atomic license identifier (e.g. `Apache-2.0 WITH LLVM-exception`, `BSD-3-Clause`, `MIT`) is treated as a **propositional variable** — an opaque symbol with no built-in meaning. The connectives `AND`, `OR`, and `NOT` are the standard Boolean (classical logic) operators.

Given that abstraction the tool can answer purely **structural / logical** questions about composite license expressions:

| Operation | Example | Question answered |
|---|---|---|
| **CNF / DNF** | `cnf "A OR (B AND C)"` → `(A OR B) AND (A OR C)` | What is the canonical form of this expression? |
| **Equivalence** | `equiv "NOT (A AND B)" "NOT A OR NOT B"` → `true` | Are these two expressions satisfied by exactly the same truth assignments? |
| **Implication** | `implies "A AND B" "A"` → `true` | Does every truth assignment that satisfies the first also satisfy the second? |

Because the tool operates at the propositional level, it works with *any* set of identifiers — SPDX or otherwise.

## What this tool does not (yet) do

The tool has **no built-in knowledge of relationships between individual licenses**. It does not know, for example, that:

- `Apache-2.0` and `GPL-2.0-only` are legally incompatible,
- MIT is permissive and can be relicensed under GPL-3.0-or-later,
- `GPL-2.0-or-later` should subsume `GPL-3.0-only`, or
- the `-only` / `-or-later` suffixes carry special meaning.

Each license identifier is an **independent, uninterpreted propositional variable**. As far as the solver is concerned `Apache-2.0` and `GPL-3.0-only` are no more related than `P` and `Q`.

### Workaround: manually encoding license-license relationships

Even without built-in semantic rules, you can **encode domain knowledge yourself** and use the tool's implication checker to exploit it.

#### Example: detecting conflicting license combinations

Suppose you maintain a list of known pairwise-incompatible licenses:

- `Apache-2.0` vs. `GPL-2.0-only`
- `CC-BY-NC-SA-4.0` vs. `GPL-3.0-only`
- ...

Each conflict means "these two licenses cannot be chosen together." Represent the full set of conflicts as a **DNF** — a disjunction of conjunctions, where each conjunction is one forbidden pair:

```plaintext
(Apache-2.0 AND GPL-2.0-only) OR (CC-BY-NC-SA-4.0 AND GPL-3.0-only) OR ...
```

Call this expression **C** (for "conflicts").

Now, given a composite license expression **L** that you want to check, ask:

> Does **L** imply **C**?

```sh
license-logic implies "<L>" "<C>"
```

If the answer is **true**, then *every* way of satisfying **L** necessarily activates at least one conflict pair — meaning the composite license is **unsatisfiable under your conflict rules**.

If the answer is **false**, there exists at least one way to satisfy **L** without triggering any known conflict.

#### Concrete example

```sh
# Conflict database (DNF of forbidden pairs)
CONFLICTS="(Apache-2.0 AND GPL-2.0-only) OR (CC-BY-NC-SA-4.0 AND GPL-3.0-only)"

# A license expression that forces a conflict
license-logic implies "Apache-2.0 AND GPL-2.0-only AND MIT" "$CONFLICTS"
# => true  (every satisfying assignment includes the Apache/GPL pair)

# A license expression that does NOT force a conflict
license-logic implies "Apache-2.0 AND MIT" "$CONFLICTS"
# => false (Apache-2.0 AND MIT alone does not trigger any conflict pair)
```

The same technique generalises to any domain rule that can be expressed as a propositional formula: subsumption rules, licence-family inclusions, policy constraints, and so on. Encode the rule as a formula and use `equiv` or `implies` to query it.

## Discrepancy: logical equivalence ≠ licensing equivalence

The transformations provided by this toolkit are **logically** correct but not necessarily **legally** correct. A compound license expression uses `AND` and `OR` as syntactic conventions with domain-specific meaning that does not always coincide with their purely logical semantics.

### Concrete example: `aws-lc-sys`

The Rust crate [`aws-lc-sys` v0.38.0](https://crates.io/crates/aws-lc-sys) declares its license as:

```
ISC AND (Apache-2.0 OR ISC) AND OpenSSL
```

This expression reflects the crate's layered provenance:

| Component | License | Reason |
| --------- | ------- | ------ |
| **aws-lc-sys** | `Apache-2.0 OR ISC` | AWS's fork of BoringSSL. AWS-LC's own additions are dual-licensed under Apache-2.0 or ISC, at the user's choice. |
| **BoringSSL** | `ISC` | Google's fork of OpenSSL. BoringSSL's own additions are licensed under ISC. |
| **OpenSSL** | `OpenSSL` | The OpenSSL code is licensed under the OpenSSL license. |

The `AND` connective in the SPDX expression means "you must satisfy **all** of these simultaneously" — each clause governs a different portion of the codebase.

#### A note on versions

This example is based on `aws-lc-sys` v0.38.0 and its dependencies at that time. Note that the licenses of these components have changed in newer versions: both OpenSSL (since v3.x) and BoringSSL have since switched to `Apache-2.0`.

### Why simplification is wrong here

In classical logic (or Boolean algebra), the expression `ISC AND (Apache-2.0 OR ISC)` is equivalent to `ISC`. This library will therefore report:

```sh
license-logic equiv "ISC AND (Apache-2.0 OR ISC) AND OpenSSL" "ISC AND OpenSSL"
# => true
```

Logically this is correct. But from a **licensing** perspective the two expressions carry different information:

- **Original:** "The BoringSSL portion is ISC; the aws-lc-sys portion is Apache-2.0 **or** ISC (your choice); the OpenSSL portion is OpenSSL."
  This gives you **two** options:
  1. BoringSSL under ISC, aws-lc-sys under **Apache-2.0**, OpenSSL under OpenSSL
  2. BoringSSL under ISC, aws-lc-sys under **ISC**, OpenSSL under OpenSSL

- **Simplified:** "Everything (except OpenSSL) is ISC."
  This describes only **one** option, losing the fact that you may choose Apache-2.0 for the aws-lc-sys-specific code.

The simplification is **lossy** because `AND` in an SPDX compound expression does not mean that a single, combined license applies to the entire work. Each `AND`-clause is scoped to a different subset of the code, and the **identity of which clause covers which part** is meaningful — even when, from a truth-table standpoint, the clause is logically redundant.

### Limitation of propositional logic (and of SPDX license expressions)

The fundamental issue is that neither propositional logic nor the SPDX license expression syntax can express **which license applies to which part of the code**. In the `aws-lc-sys` example, the three `AND`-clauses implicitly refer to three disjoint subsets of the codebase, but this scoping information exists only in the commit history (or in accompanying documentation) — it is not, and cannot be, encoded in the expression itself.

Propositional logic treats every variable as a context-free atom. It has no notion of "this variable pertains to *this* part of the codebase and that variable pertains to *that* part." As a result, any transformation that is valid in propositional logic — such as the absorption law — may discard distinctions that are meaningful in the licensing domain but invisible to the logic.

This is equally a limitation of the SPDX compound expression format: `AND` and `OR` are overloaded to carry scoping information that the syntax has no way to make explicit. The SPDX specification itself [acknowledges](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/) that compound expressions describe the licensing of a **package as a whole**, not the internal mapping from files to licenses.
