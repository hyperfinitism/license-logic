# license-logic

![SemVer](https://img.shields.io/badge/license--logic-pre--release-blue)
![MSPV](https://img.shields.io/badge/python-3.11+-orange.svg)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](https://opensource.org/licenses/MIT)

A propositional-logic toolkit for reasoning about composite license expressions.

It parses [SPDX-style](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/) compound license expressions (`AND`, `OR`, `WITH` and non-standard `NOT`) into a formula AST and provides:

- **Normal-form conversion** — exact CNF and DNF (by distributivity, not Tseitin)
- **Equivalence checking** — are two expressions logically equivalent?
- **Implication checking** — does one expression logically imply another?

These operations are powered by a SAT solver ([PySAT](https://pysathq.github.io/)) via Tseitin encoding.

## Installation

```
pip install git+https://github.com/hyperfinitism/license-logic
```

## Quick start

### CLI

```
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

Every atomic license identifier (e.g. `MIT`, `Apache-2.0`, `GPL-3.0-only`, `BSD-3-Clause WITH LLVM-exception`) is treated as a **propositional variable** — an opaque symbol with no built-in meaning. The connectives `AND`, `OR`, and `NOT` are the standard Boolean (classical logic) operators.

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

- Apache-2.0 vs. GPL-2.0-only
- CC-BY-NC-SA-4.0 vs. GPL-3.0-only
- …

Each conflict means "these two licenses cannot be chosen together." Represent the full set of conflicts as a **DNF** — a disjunction of conjunctions, where each conjunction is one forbidden pair:

```
(Apache-2.0 AND GPL-2.0-only) OR (CC-BY-NC-SA-4.0 AND GPL-3.0-only) OR ...
```

Call this expression **C** (for "conflicts").

Now, given a composite license expression **L** that you want to check, ask:

> Does **L** imply **C**?

```
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
