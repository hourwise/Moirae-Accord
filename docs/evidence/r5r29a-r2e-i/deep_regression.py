"""Replay R2e deep-schema and deep-value probes with the installed canonical evaluator."""

import importlib.util
import json
import sys

from preflight import CANON, C2, EXPECTED, HERE, LAW_REL, check, filehash


sys.setrecursionlimit(30000)
EVAL = CANON / LAW_REL / "audit/evaluate_r5r4.py"
spec = importlib.util.spec_from_file_location("canonical_r2e_deep", EVAL)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
check(filehash(EVAL), EXPECTED["primary"], "installed evaluator for deep regression")
bootstrap = mod._run_evaluation(mod._selftest_args(CANON, C2 / "inputs/verification-input.json", EXPECTED["package"]))
check(bootstrap["status"], "PASS", "deep regression bootstrap")


def chain(depth, leaf):
    out = leaf
    for _ in range(depth):
        out = {"x": out}
    return out


rows = []
for depth in (600, 1200, 2000):
    schema = {"type": "integer"}
    for _ in range(depth):
        schema = {"type": "object", "properties": {"x": schema}, "required": ["x"]}
    for kind, value, expected in [
        ("valid", chain(depth, 4), True),
        ("invalid_near_root", {"x": "wrong"}, False),
        ("invalid_deepest", chain(depth, "wrong"), False),
    ]:
        observed = bool(mod.schema_valid(schema, value, "INSTANCE"))
        check(observed, expected, f"deep schema {depth} {kind}")
        rows.append({"depth": depth, "kind": kind, "observed": observed})
for depth in (600, 1200):
    schema = {"type": "integer"}
    for _ in range(depth):
        schema = {"type": "object", "properties": {"x": schema}}
    check(mod.schema_valid(schema, None, "META_SCHEMA"), True, f"deep meta-valid {depth}")
    rows.append({"depth": depth, "kind": "meta_valid", "observed": True})
for depth in (900, 1200):
    value = chain(depth, True)
    copied = mod._copy_json_value(value)
    check(mod._json_equal(value, copied), True, f"deep copy/equality {depth}")
    check(mod.schema_valid(True, value, "INSTANCE"), True, f"deep boolean schema {depth}")
    rows.append({"depth": depth, "kind": "runtime_copy_equal_boolean_schema", "observed": True})
result = {"status": "PASS", "installed_primary_sha256": EXPECTED["primary"],
          "bootstrap_status": bootstrap["status"], "results": rows}
(HERE / "deep-regression-results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "PASS", "cases": len(rows), "max_schema_depth": 2000, "max_runtime_depth": 1200}))
