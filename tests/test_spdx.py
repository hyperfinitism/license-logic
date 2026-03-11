# SPDX-License-Identifier: MIT

from license_logic.spdx import parse, to_string


def test_roundtrip_smoke():
    s = "MIT OR (Apache-2.0 AND BSD-3-Clause)"
    ast = parse(s)
    out = to_string(ast)
    assert "MIT" in out
    assert "Apache-2.0" in out


def test_with_is_atomic():
    s = "MIT WITH LLVM-exception AND Apache-2.0"
    ast = parse(s)
    out = to_string(ast)
    assert "MIT WITH LLVM-exception" in out
