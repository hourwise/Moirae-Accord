#!/usr/bin/env python3
"""Primary evaluator for the ACCORD-02E4R5R3 specification package.

Reports two distinct layers:

* INTERNAL_PACKAGE_CONFORMANCE -- the selected package bytes satisfy their
  complete normative contracts (package invariants plus bounded governance).
* TRUSTED_PACKAGE_IDENTITY -- an external caller-supplied trust anchor equals
  the recomputed candidate identity.  The anchor is never read from the
  candidate and is never reported PASS when it is absent.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import jsonschema
import rfc8785

REL = "docs/accord-02e4r5r3"
ROLE_RE = re.compile(r"^([a-z0-9_]+):/")
ROLE_OBJECT_KIND = {
    "authority": "AUTHORITY",
    "inputs": "NORMATIVE_INPUTS",
    "canonicalization": "CANONICALIZATION",
    "references": "CONTRACT",
    "registry": "REGISTRY",
    "partial": "POLICY",
    "target": "CONTRACT",
    "evidence": "EVIDENCE",
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def jcs_hash(value) -> str:
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def raw_sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pointer(value, ptr):
    if ptr in ("", "/"):
        return value
    for token in ptr.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def stamp(text: str):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def collect_roles(node, out: set) -> None:
    if isinstance(node, dict):
        for child in node.values():
            collect_roles(child, out)
    elif isinstance(node, list):
        for child in node:
            collect_roles(child, out)
    elif isinstance(node, str):
        match = ROLE_RE.match(node)
        if match:
            out.add(match.group(1))


def collect_key_pointers(node, key, out, at=""):
    if isinstance(node, dict):
        for name, child in node.items():
            if name == key:
                out.append(at + "/" + name)
            collect_key_pointers(child, key, out, at + "/" + name)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            collect_key_pointers(child, key, out, at + "/" + str(index))


class Engine:
    def __init__(self, root, external=None):
        self.root = Path(root).resolve()
        self.dir = self.root / REL
        self.external = external
        self.registry = read(self.dir / "object-registry.json")
        self.package = read(self.dir / "specification-package-0.2.json")
        self.rules = read(self.dir / "rule-registry.json")
        self.invariants = read(self.dir / "invariant-registry.json")
        self.procedures = read(self.dir / "procedure-registry.json")
        self.reference_model = read(self.dir / "reference-model.json")
        self.authority = read(self.dir / "authority-requirements.json")
        self.governance = read(self.dir / "governance-requirements.json")
        self.integrity_modes = read(self.dir / "integrity-modes.json")
        self.semantic_keys = read(self.dir / "semantic-key-authority.json")
        self.inputs = read(self.dir / "normative-inputs.json")
        self.bindings = read(self.dir / "accepted-source-bindings.json")
        self.canon = read(self.dir / "canonicalization-profile.json")
        self.policy = read(self.dir / "partial-effect-policy.json")
        self.target = read(self.dir / "v013-target.json")
        self.evidence = read(self.dir / "v013-evidence.json")
        self.v013 = read(self.dir / "v013-governance.json")
        self.propositions = read(self.dir / "proposition-inventory.json")
        self.source_binding = read(self.dir / "source-catalog-binding.json")
        self.ext_contract = read(self.dir / "external-verification-input.contract.json")
        self.objects = self.registry["objects"]
        self.index = {}
        for entry in self.objects:
            self.index.setdefault((entry["kind"], entry["id"], entry["version"]), []).append(entry)
        self.inv = {row["invariant_id"]: row for row in self.invariants["invariants"]}
        self.proc = {row["procedure_id"]: row for row in self.procedures["procedures"]}
        self.mode_map = {row["mode"]: row for row in self.integrity_modes["modes"]}

    # ------------------------------------------------------------- resolution
    def entry(self, ref):
        if not isinstance(ref, dict) or "kind" not in ref:
            raise LookupError("not a typed reference")
        hits = self.index.get((ref["kind"], ref["id"], ref["version"]), [])
        if len(hits) != 1:
            raise LookupError("resolution cardinality")
        if ref.get("member_id") and ref["member_id"] not in hits[0].get("members", []):
            raise LookupError("member resolution")
        return hits[0]

    def load(self, ref):
        return read(self.root / self.entry(ref)["path"])

    def active_normative(self):
        return [o for o in self.objects
                if o["status"] == "ACTIVE" and o["classification"] == "NORMATIVE"]

    # ------------------------------------------------------------- integrity
    def integrity_of(self, entry):
        """Dispatch solely from the declared integrity-mode vocabulary."""
        integ = entry["integrity"]
        mode = integ.get("mode")
        spec = self.mode_map.get(mode)
        if spec is None:
            return False, {"mode": mode, "error": "E4R5R3-INTEGRITY-MODE-UNKNOWN"}
        path = self.root / entry["path"]
        try:
            if mode == "SEMANTIC_JSON_CONTENT":
                ok = jcs_hash(read(path)) == integ.get("digest")
            elif mode == "RAW_FILE_BYTES":
                ok = raw_sha(path) == integ.get("digest")
            elif mode == "PACKAGE_PINNED_BOOTSTRAP":
                ok = jcs_hash(read(path)) == self.package.get("registry_semantic_sha256")
            elif mode == "SELF_DIGEST":
                document = read(path)
                expected = document["current_candidate_integrity"]["digest"]
                reduced = copy.deepcopy(document)
                del reduced["current_candidate_integrity"]["digest"]
                ok = jcs_hash(reduced) == expected
            elif mode == "DUAL_ACCEPTED_SOURCE":
                binding = self.load(integ["binding_ref"])
                match = next((s for s in binding["sources"] if s["path"] == entry["path"]), None)
                if match is None:
                    return False, {"mode": mode, "error": "E4R5R3-SOURCE-NOT-BOUND"}
                data = path.read_bytes()
                claim = match["integrity"]
                ok = (hashlib.sha256(data).hexdigest() == claim["raw_file_bytes_sha256"]
                      and jcs_hash(json.loads(data)) == claim["semantic_json_content_sha256"])
            else:
                ok = False
        except Exception as exc:
            return False, {"mode": mode, "error": type(exc).__name__ + ": " + str(exc)}
        return ok, {"mode": mode, "failure_code": spec["failure_code"]}

    # --------------------------------------------------------------- reference
    def reference_edges(self):
        shape = self.reference_model["shape_predicate"]
        required = set(shape["required_keys"])
        optional = set(shape["optional_keys"])
        allow_additional = shape["additional_keys"] == "ALLOW"
        edges = []

        def walk(value, source, at=""):
            if isinstance(value, dict):
                keys = set(value)
                if required <= keys and (allow_additional or keys <= required | optional) \
                        and all(isinstance(v, str) for v in value.values()):
                    edges.append((source["kind"], source["id"], source["version"], at,
                                  value["kind"], value["id"], value["version"],
                                  value.get("member_id", "")))
                for name, child in value.items():
                    walk(child, source, at + "/" + name.replace("~", "~0").replace("/", "~1"))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, source, at + "/" + str(index))

        for source in self.active_normative():
            walk(read(self.root / source["path"]), source)
        return sorted(set(edges))

    # ---------------------------------------------------------------- helpers
    def class_map(self):
        classes, valid, errors = {}, {}, {}
        for rule in self.rules["rules"]:
            if "invariant_binding" in rule:
                derived = "EXECUTABLE_CONFORMANCE_RULE"
                binding = rule["invariant_binding"]
                inv = self.inv.get(binding["invariant_id"])
                ok = (inv is not None and inv["status"] == "ACTIVE"
                      and set(binding["arguments"]) == {r["role"] for r in inv["input_roles"] if r["required"]}
                      and binding["arguments"] == inv["default_arguments"]
                      and rule["inherited_failure_code"] in inv["compatible_failure_codes"]
                      and "subjects" not in rule)
                if ok:
                    for spec in inv["input_roles"]:
                        arg = binding["arguments"].get(spec["role"])
                        ok = ok and arg is not None and arg.get("kind") == spec["kind"]
                        try:
                            self.entry(arg)
                        except Exception:
                            ok = False
                valid[rule["rule_id"]] = bool(ok)
            elif "internal_check" in rule and "invariant_binding" not in rule:
                derived = "INTERNAL_DESIGN_INVARIANT"
                valid[rule["rule_id"]] = True
            elif (rule.get("missing_subject_roles") and rule.get("later_lifecycle_stage")
                  and "invariant_binding" not in rule and "internal_check" not in rule):
                derived = "DEFERRED_NO_SUBJECT_ARTIFACT"
                valid[rule["rule_id"]] = True
            else:
                derived = "INVALID"
                valid[rule["rule_id"]] = False
            classes[rule["rule_id"]] = derived
            if derived != rule["declared_class"] or not valid[rule["rule_id"]]:
                errors[rule["rule_id"]] = {"declared": rule["declared_class"],
                                           "derived": derived,
                                           "compatible": valid[rule["rule_id"]]}
        return classes, errors

    def arity(self):
        trace, ok_all = {}, True
        for iid, inv in self.inv.items():
            proc = self.proc.get(inv["procedure_id"])
            declared = {r["role"] for r in inv["input_roles"] if r["required"]}
            arguments = {a["name"] for a in proc["arguments"] if a["required"]} if proc else set()
            ok = (declared == arguments and set(inv["default_arguments"]) == declared
                  and inv["fail_closed"] is True)
            trace[iid] = {"declared_roles": sorted(declared),
                          "procedure_arguments": sorted(arguments),
                          "status": "PASS" if ok else "FAIL"}
            ok_all = ok_all and ok
        return ok_all, trace

    # ------------------------------------------------------------- operations
    def op_schema_universe(self):
        schemas, result = {}, {}
        for entry in self.objects:
            if entry["kind"] == "SCHEMA" and entry["status"] == "ACTIVE":
                document = read(self.root / entry["path"])
                try:
                    jsonschema.Draft202012Validator.check_schema(document)
                    schemas[(entry["id"], entry["version"])] = document
                    result[entry["id"]] = "PASS"
                except Exception as exc:
                    result[entry["id"]] = "FAIL"
                    return False, {"schemas": result, "detail": str(exc)}
        for entry in self.active_normative():
            if entry["kind"] == "SCHEMA":
                continue
            ref = entry.get("schema_ref")
            try:
                jsonschema.validate(read(self.root / entry["path"]),
                                    schemas[(ref["id"], ref["version"])])
                result[entry["id"]] = "PASS"
            except Exception as exc:
                result[entry["id"]] = "FAIL"
                return False, {"schemas": result, "detail": str(exc)}
        return True, {"schemas": result}

    def op_lineage(self, iid):
        if iid == "PACKAGE_LINEAGE":
            required = self.authority["package_requirements"]
            lineage = [{k: row[k] for k in ("revision", "commit") if k in row}
                       for row in self.package["rejected_candidate_lineage"]]
            wanted = required["required_rejected_revision"]
            ok = (self.package["package_id"] == required["family"]
                  and self.package["package_version"] == required["version"]
                  and self.package["status"] == required["status"]
                  and wanted in lineage)
            return ok, {"required": wanted, "lineage_matched": wanted in lineage}
        if iid == "PROFILE_REFERENCE_PINNING":
            ok = self.inputs["profile"]["object_version"] == self.authority["package_requirements"]["version"]
            return ok, {"profile_version": self.inputs["profile"]["object_version"]}
        raise ValueError("unhandled SECTION_ENTAILMENT")

    def op_dual_integrity(self):
        detail, ok_all = {}, True
        for source in self.bindings["sources"]:
            path = self.root / source["path"]
            data = path.read_bytes()
            claim = source["integrity"]
            raw = hashlib.sha256(data).hexdigest()
            semantic = jcs_hash(json.loads(data))
            ok = raw == claim["raw_file_bytes_sha256"] \
                and semantic == claim["semantic_json_content_sha256"]
            detail[source["path"]] = {"status": "PASS" if ok else "FAIL",
                                      "raw": raw, "semantic": semantic}
            ok_all = ok_all and ok
        return ok_all, detail

    def op_digest(self):
        detail, ok_all = {}, True
        for entry in self.active_normative():
            ok, extra = self.integrity_of(entry)
            detail[entry["id"]] = {"status": "PASS" if ok else "FAIL", **extra}
            ok_all = ok_all and ok
        return ok_all, detail

    def op_unique_key(self):
        keys = [(o["kind"], o["id"], o["version"]) for o in self.objects]
        return len(keys) == len(set(keys)), {"keys": len(keys), "unique": len(set(keys))}

    def op_reference(self):
        edges = self.reference_edges()
        bad = []
        for edge in edges:
            ref = {"kind": edge[4], "id": edge[5], "version": edge[6]}
            if edge[7]:
                ref["member_id"] = edge[7]
            try:
                self.entry(ref)
            except Exception as exc:
                bad.append({"edge": list(edge), "error": str(exc)})
        return not bad, {"edges": [list(e) for e in edges], "unresolved_or_ambiguous": bad}

    def op_set_equality(self, iid):
        if iid == "DEPENDENCY_GRAPH_EQUAL":
            left = {(row["rule_id"], dep)
                    for row in self.inputs["rule_dependencies"] for dep in row["depends_on"]}
            right = {(e["from"], e["to"]) for e in self.inputs["dependency_edges"]}
            return left == right, {"left": sorted(left), "right": sorted(right)}
        left = {row["vector_id"]: row["expected"] for row in self.inputs["vector_expectations"]}
        accepted = self.load({"kind": "SOURCE_VECTOR_CATALOG",
                              "id": "urn:moirae:accord-02r5:source-vector-catalog",
                              "version": "0.1"})
        right = {row["vector_id"]: row["expected"] for row in accepted["vectors"]}
        ok = left == right
        return ok, {"vector_ids": len(left),
                    "changed": sorted(k for k in set(left) | set(right)
                                      if left.get(k) != right.get(k))}

    def op_policy_agreement(self, iid):
        if iid == "PREDICATE_AUTHORITY_CLOSURE":
            required = self.authority["stage_policy_requirements"]
            allowed = self.authority["stage_policy_authorization"]
            ok = self.inputs["predicate_policy"] == required \
                and all(required[k] in allowed[k] for k in required)
            return ok, {"required": required, "authorized": allowed}
        if iid == "CANONICALIZATION_AUTHORITY_CLOSURE":
            required = self.authority["canonicalization_requirements"]
            projected = {k: self.canon[k] for k in required}
            return projected == required, {"projected": projected, "required": required}
        required = self.authority["partial_effect_requirements"]
        ok = (self.policy["same_effect_required"] == required["same_effect_required"]
              and self.policy["direct_predecessor_required"] == required["direct_predecessor_required"]
              and self.policy["decisions"][required["merged_decision_key"]]
              == required["merged_decision_value"])
        return ok, {"decision": self.policy["decisions"][required["merged_decision_key"]]}

    def op_source_catalog_binding(self):
        cand = self.source_binding["candidate_binding"]
        mapping = self.source_binding["field_vocabulary_mapping"]
        checks = {}
        catalog_entries = [o for o in self.objects if o["kind"] == "SOURCE_VECTOR_CATALOG"]
        checks["registry_identity"] = (len(catalog_entries) == 1
                                       and cand["assigned_kind"] == catalog_entries[0]["kind"]
                                       and cand["assigned_id"] == catalog_entries[0]["id"]
                                       and cand["assigned_version"] == catalog_entries[0]["version"])
        accepted = next((s for s in self.bindings["sources"]
                         if s["ref"]["kind"] == "SOURCE_VECTOR_CATALOG"), None)
        if accepted is None:
            return False, {"checks": {"accepted_binding_present": False}}
        checks["accepted_binding_present"] = True
        checks["path_equals_accepted"] = cand["repository_root_path"] == accepted["path"]
        matching = [o for o in self.objects if o["path"] == cand["repository_root_path"]]
        checks["path_resolves_exactly_once"] = (len(matching) == 1
                                                and matching[0]["kind"] == "SOURCE_VECTOR_CATALOG")
        checks["registered_path_equals_accepted"] = (
            len(matching) == 1 and matching[0]["path"] == accepted["path"])
        try:
            data = (self.root / cand["repository_root_path"]).read_bytes()
            recomputed_semantic = jcs_hash(json.loads(data))
            recomputed_raw = hashlib.sha256(data).hexdigest()
            checks["path_readable"] = True
        except Exception as exc:
            checks["path_readable"] = False
            return False, {"checks": checks, "detail": str(exc)}
        checks["candidate_semantic_equals_recomputed"] = \
            cand["semantic_json_content_sha256"] == recomputed_semantic
        checks["accepted_semantic_equals_recomputed"] = \
            accepted["integrity"]["semantic_json_content_sha256"] == recomputed_semantic
        checks["candidate_semantic_equals_accepted"] = \
            cand["semantic_json_content_sha256"] == accepted["integrity"]["semantic_json_content_sha256"]
        checks["candidate_raw_equals_recomputed"] = cand["raw_file_bytes_sha256"] == recomputed_raw
        checks["accepted_raw_equals_recomputed"] = \
            accepted["integrity"]["raw_file_bytes_sha256"] == recomputed_raw
        checks["candidate_raw_equals_accepted"] = \
            cand["raw_file_bytes_sha256"] == accepted["integrity"]["raw_file_bytes_sha256"]
        mode = self.mode_map.get(cand["declared_integrity_class"])
        checks["integrity_class_declared"] = mode is not None
        if mode is not None:
            checks["canonicalization_matches_vocabulary"] = \
                cand["declared_canonicalization"] == mode[mapping["declared_canonicalization"]]
            checks["algorithm_matches_vocabulary"] = \
                cand["declared_algorithm"] == mode[mapping["declared_algorithm"]]
        else:
            checks["canonicalization_matches_vocabulary"] = False
            checks["algorithm_matches_vocabulary"] = False
        return all(checks.values()), {"checks": checks}

    # ------------------------------------------------------------------- V013
    def evaluate_requirement(self, requirement, policy):
        target, evidence = self.target, self.evidence
        procedure = requirement["procedure"]
        if procedure == "EXACT_EQUAL":
            fields = requirement["source_fields"]
            scope = {"target": target, "evidence": evidence}
            left = pointer(scope, "/" + fields[0].replace(".", "/"))
            right = pointer(scope, "/" + fields[1].replace(".", "/"))
            return left == right, {"left": left, "right": right}
        if procedure == "TUPLE_EQUAL":
            return target["scope"] == evidence["scope"], {}
        if procedure == "RFC3339_ORDER_INCLUSIVE":
            window = evidence["observed_interval"]
            return stamp(window["not_before"]) <= stamp(window["as_of"]), {}
        if procedure == "INTERVAL_COVERAGE_INCLUSIVE_BOTH_ENDS":
            want, got = target["required_interval"], evidence["observed_interval"]
            return (stamp(got["not_before"]) <= stamp(want["not_before"])
                    and stamp(want["as_of"]) <= stamp(got["as_of"])), {}
        if procedure == "RETENTION_GTE_MAX_SPAN_AND_PROFILE_MIN":
            want = target["required_interval"]
            span = (stamp(want["as_of"]) - stamp(want["not_before"])).total_seconds()
            bound = max(span, policy["minimum_retention_seconds"])
            return evidence["retention_window_seconds"] >= bound, {"bound": bound}
        if procedure == "MEMBERSHIP":
            if requirement["requirement_id"] == "CONSISTENCY_ALLOWED":
                return evidence["consistency_level"] in policy["allowed_consistency_levels"], {}
            return evidence["evidence_class"] in policy["allowed_source_classes"], {}
        if procedure == "AGE_WITHIN_PROFILE_MAX":
            age = (stamp(evidence["verification_time"])
                   - stamp(evidence["observed_at"])).total_seconds()
            return 0 <= age <= policy["freshness_max_age_seconds"], {"age": age}
        if procedure == "COMPLETE_READ_REQUIRED":
            ok = (policy["complete_read_requirement"] == "COMPLETE_LEDGER_QUERY_REQUIRED"
                  and evidence["read_scope_complete"] is True
                  and evidence["read_semantics"] == "COMPLETE_LEDGER_QUERY")
            return ok, {}
        if procedure == "ADMISSIBLE_POSITIVE_SAME_TARGET_COUNT_ZERO":
            if policy["contradiction_rule"] != "FORBID_ADMISSIBLE_SAME_TARGET_POSITIVE":
                return False, {"contradiction_rule": policy["contradiction_rule"]}
            target_key = (target["effect_id"], target["negated_predicate_id"],
                          target["negated_stage"], target["scope"])
            seen, hits = set(), 0
            for item in evidence["evidence_universe"]:
                key = (item["effect_id"], item["predicate_id"], item["stage"], item["scope"])
                if not item["admissible"] or item["polarity"] != "POSITIVE" or key != target_key:
                    continue
                if item["evidence_id"] in seen:
                    continue
                seen.add(item["evidence_id"])
                hits += 1
            return hits == 0, {"admissible_positive_same_target": hits}
        if procedure == "OBSERVATION_NOT_IN_FUTURE":
            declared = policy["future_observation_result"]
            if declared not in self.v013["result_vocabulary"] \
                    or declared == self.v013["pass_result"]:
                return False, {"future_observation_result": declared}
            ok = stamp(evidence["observed_at"]) <= stamp(evidence["verification_time"])
            return ok, {"observed_at": evidence["observed_at"]}
        if procedure == "OBSERVATION_NOT_STALE":
            declared = policy["stale_result"]
            if declared not in self.v013["result_vocabulary"] \
                    or declared == self.v013["pass_result"]:
                return False, {"stale_result": declared}
            age = (stamp(evidence["verification_time"])
                   - stamp(evidence["observed_at"])).total_seconds()
            return age <= policy["freshness_max_age_seconds"], {"age": age}
        if procedure == "UNIVERSE_ITEMS_TYPED_CLOSED":
            required = {"evidence_id", "effect_id", "predicate_id", "stage", "scope",
                        "polarity", "relationship", "admissible", "observed_interval",
                        "consistency_level", "source_class"}
            for item in evidence["evidence_universe"]:
                if set(item) != required or not isinstance(item["admissible"], bool):
                    return False, {"item": item.get("evidence_id")}
            return True, {}
        if procedure == "CALLER_SUPPLIED_COUNT_FORBIDDEN":
            forbidden = self.v013["requirement_map"]["forbidden_requirements"]
            present = [field for field in forbidden
                       if field in self.target or field in self.evidence]
            return not present, {"present": present}
        raise ValueError("unsupported V013 procedure " + procedure)

    def requirement_map_result(self):
        requirement_map = self.v013["requirement_map"]
        policy = self.inputs["profile"]["negative_policy"]
        ids = [r["requirement_id"] for r in requirement_map["requirements"]]
        order = requirement_map["evaluation_order"]
        required = requirement_map["required_requirement_ids"]
        structural = {
            "required_ids_exact": sorted(set(ids)) == sorted(set(required)),
            "no_duplicate_ids": len(ids) == len(set(ids)),
            "evaluation_order_covers_once": len(order) == len(set(order)) and set(order) == set(ids),
            "policy_fields_covered": sorted(self.v013["policy_field_roles"]) == sorted(policy),
        }
        by_id = {r["requirement_id"]: r for r in requirement_map["requirements"]}
        detail, ok = {}, all(structural.values())
        for rid in order:
            requirement = by_id.get(rid)
            if requirement is None:
                detail[rid] = {"status": "FAIL", "reason": "MISSING_REQUIREMENT"}
                ok = False
                continue
            try:
                passed, witness = self.evaluate_requirement(requirement, policy)
            except Exception as exc:
                passed, witness = False, {"exception": type(exc).__name__ + ": " + str(exc)}
            detail[rid] = {"status": "PASS" if passed else "FAIL", "witness": witness,
                           "failure_code": requirement["failure_code"]}
            ok = ok and passed
        return ok, {"structural": structural, "requirements": detail,
                    "result": self.v013["pass_result"] if ok else self.v013["fail_result"]}

    # -------------------------------------------------------------- governance
    def op_authority_completeness(self):
        classes, class_errors = self.class_map()
        active = {k for k, v in self.inv.items() if v["status"] == "ACTIVE"}
        required = set(self.package["required_invariant_ids"])
        referenced = {r["invariant_binding"]["invariant_id"]
                      for r in self.rules["rules"] if "invariant_binding" in r}
        non_bound = {k for k, v in self.inv.items() if v["usage"] != "CONFORMANCE_BOUND"}
        ok = not class_errors and active == required and required == referenced | non_bound
        return ok, {"class_errors": class_errors, "active": sorted(active),
                    "required": sorted(required),
                    "referenced_or_non_bound": sorted(referenced | non_bound)}

    def op_proposition_inventory(self):
        collection = self.propositions["collection_propositions"]
        members = self.propositions["member_propositions"]
        projection = self.propositions["projection_propositions"]
        informational = self.propositions["informational"]
        declared = [p["proposition_id"]
                    for p in collection + members + projection + informational]
        vector_ids = [row["vector_id"] for row in self.inputs["vector_expectations"]]
        collection_ids = {c["proposition_id"] for c in collection if c["normative"]}
        member_ids = {m["proposition_id"] for m in members if m["normative"]}
        projection_ids = {p["proposition_id"] for p in projection if p["normative"]}
        normative = collection_ids | member_ids | projection_ids
        required = set(vector_ids) | collection_ids | projection_ids
        ok = (len(declared) == len(set(declared))
              and len(vector_ids) == len(set(vector_ids))
              and normative == required
              and member_ids == set(vector_ids)
              and all(m["member_of"] in collection_ids for m in members)
              and all(p["collection_proposition_id"] in collection_ids for p in projection))
        return ok, {"declared": sorted(declared), "required": sorted(required),
                    "normative": sorted(normative)}

    def op_v013_basis(self):
        target = self.target
        basis = target["relationship_basis"]
        locator = self.v013["accepted_v013_locator"]
        accepted = self.load(locator["source_ref"])
        member = next(v for v in accepted["vectors"]
                      if v["vector_id"] == locator["accepted_member_id"])
        schema = self.v013["relationship_basis_schema"]
        checks = {"relationship_in_vocabulary":
                  target["relationship"] in self.v013["relationship_vocabulary"]}
        for binding in basis["accepted"]:
            if binding["accepted_pointer"].endswith("/*"):
                values = pointer(member, binding["accepted_pointer"][:-2])
                checks[binding["field_id"]] = binding["must_contain"] in values
            else:
                checks[binding["field_id"]] = \
                    pointer(member, binding["accepted_pointer"]) == binding["must_equal"]
        accepted_fields = {b["field_id"] for b in basis["accepted"]}
        candidate_fields = {b["field_id"] for b in basis["candidate_supplied"]}
        overlap = accepted_fields & candidate_fields
        checks["no_forbidden_overlap"] = len(overlap) == 0
        for binding in basis["candidate_supplied"]:
            checks["candidate_" + binding["field_id"]] = (
                binding["provenance"] == "CANDIDATE_LOCAL_NOT_HISTORY"
                and pointer(target, binding["candidate_pointer"]) is not None)
        checks["accepted_pointer_prefix"] = all(
            b["accepted_pointer"].startswith(schema["accepted_pointer_prefix"])
            for b in basis["accepted"])
        checks["candidate_pointer_prefix"] = all(
            b["candidate_pointer"].startswith(schema["candidate_pointer_prefix"])
            for b in basis["candidate_supplied"])
        return all(checks.values()), {"checks": checks}

    def op_fail_closed(self):
        violations = {inv["invariant_id"]: "NOT_FAIL_CLOSED"
                      for inv in self.invariants["invariants"]
                      if inv["acceptance_critical"] and inv["fail_closed"] is not True}
        return not violations, {"non_fail_closed": violations}

    def op_subject_roles(self):
        violations = {}
        for inv in self.invariants["invariants"]:
            roles = {r["role"] for r in inv["input_roles"] if r["required"]}
            bad = [s for s in inv["subject_roles"] if s not in roles]
            if bad or not inv["subject_roles"]:
                violations[inv["invariant_id"]] = bad
        return not violations, {"uncovered_subject_roles": violations}

    def op_default_arguments(self):
        violations = {}
        for inv in self.invariants["invariants"]:
            proc = self.proc.get(inv["procedure_id"])
            declared = {r["role"] for r in inv["input_roles"] if r["required"]}
            arguments = {a["name"] for a in proc["arguments"]} if proc else set()
            symmetric = set(inv["default_arguments"]) ^ declared
            unresolved = []
            for role, ref in inv["default_arguments"].items():
                spec = next((r for r in inv["input_roles"] if r["role"] == role), None)
                if spec is None or ref.get("kind") != spec.get("kind"):
                    unresolved.append(role)
                    continue
                try:
                    self.entry(ref)
                except Exception:
                    unresolved.append(role)
            if symmetric or unresolved or declared != arguments:
                violations[inv["invariant_id"]] = {"symmetric_difference": sorted(symmetric),
                                                   "unresolved": sorted(unresolved)}
        return not violations, {"violations": violations}

    def op_derivation_role_closure(self):
        violations = {}
        for inv in self.invariants["invariants"]:
            proc = self.proc.get(inv["procedure_id"])
            if proc is None:
                violations[inv["invariant_id"]] = "NO_PROCEDURE"
                continue
            used = set()
            collect_roles(proc["derivation"], used)
            declared = {r["role"] for r in inv["input_roles"] if r["required"]}
            arguments = {a["name"] for a in proc["arguments"] if a["required"]}
            if not (declared == arguments == used):
                violations[inv["invariant_id"]] = {
                    "invariant_required_input_roles": sorted(declared),
                    "procedure_required_arguments": sorted(arguments),
                    "derivation_referenced_roles": sorted(used)}
        return not violations, {"violations": violations}

    def op_operation_supported(self):
        supported = set(self.governance["supported_operations"])
        unsupported = {row["procedure_id"]: row["derivation"]["operation"]
                       for row in self.procedures["procedures"]
                       if row["derivation"]["operation"] not in supported}
        return not unsupported, {"unsupported": unsupported}

    def op_behavior(self, key):
        vocabulary = self.governance["behavior_vocabulary"][key]
        unsupported = {row["procedure_id"]: row[key]
                       for row in self.procedures["procedures"] if row[key] not in vocabulary}
        return not unsupported, {"field": key, "unsupported": unsupported}

    def op_discovery_scope(self):
        scope = self.reference_model["discovery_scope"]
        universe = [o for o in self.objects if o["status"] == scope["registry_status"]
                    and o["classification"] == scope["classification"]]
        return bool(universe), {"universe_size": len(universe)}

    def op_shape_predicate(self):
        shape = self.reference_model["shape_predicate"]
        requirement = self.governance["shape_predicate_requirement"]
        ok = (shape["additional_keys"] in requirement["allowed_additional_keys"]
              and shape["additional_keys"] == requirement["additional_keys_authority"])
        return ok, {"additional_keys": shape["additional_keys"]}

    def op_uniqueness_key(self):
        identity = self.governance["uniqueness_key_requirement"]["identity_fields"]
        ok = self.registry["uniqueness_key"] == identity \
            and self.registry["identity_fields"] == identity
        keys = [tuple(o[f] for f in self.registry["uniqueness_key"]) for o in self.objects]
        return ok and len(keys) == len(set(keys)), {"key": self.registry["uniqueness_key"]}

    def op_role_model(self):
        requirement = self.governance["role_model_requirement"]
        vocabulary = set(self.registry["role_vocabulary"])
        unknown = {o["id"]: [r for r in o["roles"] if r not in vocabulary]
                   for o in self.objects if any(r not in vocabulary for r in o["roles"])}
        ok = self.registry["role_model"] == requirement["required_role_model"] and not unknown
        return ok, {"role_model": self.registry["role_model"], "unknown_roles": unknown}

    def op_schema_identity(self):
        schemas = {o["id"]: o for o in self.objects if o["kind"] == "SCHEMA"}
        mismatches = {}
        for entry in self.objects:
            ref = entry.get("schema_ref")
            if ref is None:
                continue
            target = schemas.get(ref["id"])
            if target is None:
                mismatches[entry["id"]] = "MISSING_SCHEMA"
                continue
            expected = "urn:moirae:accord-02r5r3:schema:" + \
                Path(target["path"]).name[:-len(".schema.json")]
            document = read(self.root / target["path"])
            if target["id"] != expected or document.get("$id") != f"{expected}:0.2":
                mismatches[entry["id"]] = {"registered": target["id"], "expected": expected,
                                           "document_id": document.get("$id")}
        return not mismatches, {"mismatches": mismatches}

    def op_rule_coverage(self):
        required = self.rules["provenance"]["required_rule_ids"]
        actual = [row["rule_id"] for row in self.rules["rules"]]
        ok = (len(actual) == len(set(actual)) and set(actual) == set(required)
              and len(actual) == len(required))
        return ok, {"required": len(required), "actual": len(actual),
                    "missing": sorted(set(required) - set(actual)),
                    "unexpected": sorted(set(actual) - set(required))}

    def op_invariant_set_exact(self):
        required = self.package["required_invariant_ids"]
        active = [r["invariant_id"] for r in self.invariants["invariants"]
                  if r["status"] == "ACTIVE"]
        ok = len(required) == len(set(required)) and set(required) == set(active)
        return ok, {"required": len(required), "active": len(active),
                    "missing": sorted(set(required) - set(active)),
                    "unexpected": sorted(set(active) - set(required))}

    def op_governing_authority(self):
        roots = self.v013["authority_roots"]
        detail = {}
        for requirement in self.v013["requirement_map"]["requirements"]:
            if requirement["governing_authority"] not in roots:
                detail[requirement["requirement_id"]] = requirement["governing_authority"]
        ids = [r["requirement_id"] for r in self.v013["requirement_map"]["requirements"]]
        for field, role in self.v013["policy_field_roles"].items():
            if not role.startswith("COMPUTED:") or role.split(":", 1)[1] not in ids:
                detail["POLICY_FIELD:" + field] = role
        for mode in self.integrity_modes["modes"]:
            if not mode["failure_code"] or mode["algorithm"] not in ("SHA-256",):
                detail["INTEGRITY_MODE:" + mode["mode"]] = mode["failure_code"]
        return not detail, {"unresolved": detail}

    def op_governing_token_singleton(self):
        policy = self.semantic_keys["governing_token_singleton"]
        permitted = set(policy["permitted_exception_roles"])
        excluded_kinds = set(policy["scan_excludes_kinds"])
        excluded_prefixes = tuple(policy["scan_excluded_pointer_prefixes"])
        duplicates = {}
        for key in self.semantic_keys["semantic_keys"]:
            name = key["key"]
            allowed = set()
            if ":/" in key["authority_path"]:
                role, at = key["authority_path"].split(":/", 1)
                allowed.add((ROLE_OBJECT_KIND.get(role), "/" + at))
            for mirror in key["governed_mirror_paths"]:
                if ":/" in mirror:
                    role, at = mirror.split(":/", 1)
                    allowed.add((ROLE_OBJECT_KIND.get(role), "/" + at))
            for entry in self.active_normative():
                if entry["kind"] in excluded_kinds:
                    continue
                if permitted & set(entry.get("roles", [])):
                    continue
                found = []
                collect_key_pointers(read(self.root / entry["path"]), name, found)
                for at in found:
                    if at.startswith(excluded_prefixes):
                        continue
                    if (entry["kind"], at) not in allowed:
                        duplicates[f"{name}|{entry['kind']}|{entry['id']}|{at}"] = \
                            "DUPLICATE_INDEPENDENT_AUTHORITY"
        return not duplicates, {"duplicates": duplicates}

    # ---------------------------------------------------------------- trust
    def recomputed_identity(self):
        reduced = copy.deepcopy(self.package)
        del reduced["current_candidate_integrity"]["digest"]
        return {"package_id": self.package["package_id"],
                "package_version": self.package["package_version"],
                "package_digest": jcs_hash(reduced)}

    def trust_result(self):
        identity = self.recomputed_identity()
        if self.external is None:
            return {"status": "FAIL", "code": "MISSING_EXTERNAL_TRUST_INPUT",
                    "layer": "TRUSTED_PACKAGE_IDENTITY", "recomputed_identity": identity}
        root = self.external.get("trust_root") or {}
        if root.get("root_kind") == "REPLACED_TRUST_ROOT":
            return {"status": "DIFFERENT_PACKAGE_VERIFIED",
                    "sub_status": "OUT_OF_SCOPE_TRUST_ROOT_REPLACEMENT",
                    "layer": "TRUSTED_PACKAGE_IDENTITY", "recomputed_identity": identity}
        if root.get("root_kind") != "PINNED_ACCEPTED_TRUST_ROOT":
            return {"status": "FAIL", "code": "EXTERNAL_INPUT_INVALID",
                    "layer": "TRUSTED_PACKAGE_IDENTITY", "recomputed_identity": identity}
        if (self.external.get("package_id") != identity["package_id"]
                or self.external.get("package_version") != identity["package_version"]):
            return {"status": "FAIL", "code": "FOREIGN_PACKAGE_IDENTITY",
                    "layer": "TRUSTED_PACKAGE_IDENTITY", "recomputed_identity": identity}
        if self.external.get("package_digest") != identity["package_digest"]:
            return {"status": "FAIL", "code": "TRUSTED_IDENTITY_MISMATCH",
                    "layer": "TRUSTED_PACKAGE_IDENTITY", "recomputed_identity": identity}
        return {"status": "PASS",
                "reason": "EXTERNAL_TRUST_ANCHOR_EQUALS_RECOMPUTED_CANDIDATE_IDENTITY",
                "layer": "TRUSTED_PACKAGE_IDENTITY", "recomputed_identity": identity}

    # ------------------------------------------------------------- execution
    def execute(self, iid, arguments):
        if iid not in self.inv:
            return {"invariant_id": iid, "class": "MISSING", "status": "FAIL",
                    "procedure": None, "witness": {"error": "INVARIANT_NOT_REGISTERED"},
                    "failure_codes": [iid + "_FAILURE"]}
        inv = self.inv[iid]
        operation = self.proc[inv["procedure_id"]]["derivation"]["operation"]
        try:
            for role, ref in arguments.items():
                self.entry(ref)
        except Exception as exc:
            return {"invariant_id": iid, "class": inv["class"], "status": "FAIL",
                    "procedure": inv["procedure_id"],
                    "witness": {"exception": "ARGUMENT_RESOLUTION: " + str(exc)},
                    "failure_codes": inv["compatible_failure_codes"]}
        ok, witness = False, {}
        try:
            if operation == "VALIDATE_ACTIVE_UNIVERSE":
                ok, witness = self.op_schema_universe()
            elif operation == "SECTION_ENTAILMENT":
                ok, witness = self.op_lineage(iid)
            elif operation == "DIGEST_RECOMPUTE":
                ok, witness = (self.op_dual_integrity()
                               if iid in ("ACCEPTED_BASE_DUAL_INTEGRITY",
                                          "ACCEPTED_SOURCE_DUAL_INTEGRITY")
                               else self.op_digest())
            elif operation == "UNIQUE_KEY":
                ok, witness = self.op_unique_key()
            elif operation == "REFERENCE_RESOLUTION":
                ok, witness = self.op_reference()
            elif operation == "SET_EQUALITY":
                ok, witness = self.op_set_equality(iid)
            elif operation == "POLICY_AGREEMENT":
                ok, witness = self.op_policy_agreement(iid)
            elif operation == "SOURCE_CATALOG_BINDING_MATCH":
                ok, witness = self.op_source_catalog_binding()
            elif operation == "REQUIREMENT_MAP_EVAL":
                ok, witness = self.requirement_map_result()
            elif operation == "AUTHORITY_COMPLETENESS":
                ok, witness = self.op_authority_completeness()
            elif operation == "PROPOSITION_INVENTORY_BOUND":
                ok, witness = self.op_proposition_inventory()
            elif operation == "ARITY_AGREEMENT":
                ok, witness = self.arity()
            elif operation == "SCHEMA_NON_VACUITY":
                detail = {}
                for entry in self.objects:
                    if entry["kind"] == "SCHEMA" and entry["status"] == "ACTIVE":
                        errors = list(jsonschema.Draft202012Validator(
                            read(self.root / entry["path"])).iter_errors({"zzz": 1}))
                        detail[entry["id"]] = "PASS" if errors else "FAIL"
                ok = all(v == "PASS" for v in detail.values())
                witness = detail
            elif operation == "CURRENT_PACKAGE_IDENTITY":
                required = self.authority["package_requirements"]
                hits = self.index.get(("PACKAGE", required["family"], required["version"]), [])
                ok = (len(hits) == 1
                      and hits[0]["path"] == self.entry(arguments["package"])["path"])
                witness = {"hits": [h["path"] for h in hits]}
            elif operation == "SELF_DIGEST":
                expected = self.package["current_candidate_integrity"]["digest"]
                reduced = copy.deepcopy(self.package)
                del reduced["current_candidate_integrity"]["digest"]
                ok = jcs_hash(reduced) == expected
                witness = {"expected": expected, "actual": jcs_hash(reduced)}
            elif operation == "INTEGRITY_MODE_DISPATCH":
                ok, witness = self.op_digest()
            elif operation == "V013_BASIS_VALID":
                ok, witness = self.op_v013_basis()
            elif operation == "FAIL_CLOSED_ENFORCED":
                ok, witness = self.op_fail_closed()
            elif operation == "SUBJECT_ROLE_COVERAGE":
                ok, witness = self.op_subject_roles()
            elif operation == "DEFAULT_ARGUMENT_COVERAGE":
                ok, witness = self.op_default_arguments()
            elif operation == "DERIVATION_ROLE_CLOSURE":
                ok, witness = self.op_derivation_role_closure()
            elif operation == "PROCEDURE_OPERATION_SUPPORTED":
                ok, witness = self.op_operation_supported()
            elif operation == "MISSING_BEHAVIOR_SUPPORTED":
                ok, witness = self.op_behavior("missing_behavior")
            elif operation == "AMBIGUITY_BEHAVIOR_SUPPORTED":
                ok, witness = self.op_behavior("ambiguity_behavior")
            elif operation == "REFERENCE_DISCOVERY_SCOPE_VALID":
                ok, witness = self.op_discovery_scope()
            elif operation == "REFERENCE_SHAPE_PREDICATE_APPLIED":
                ok, witness = self.op_shape_predicate()
            elif operation == "UNIQUENESS_KEY_APPLIED":
                ok, witness = self.op_uniqueness_key()
            elif operation == "ROLE_MODEL_APPLIED":
                ok, witness = self.op_role_model()
            elif operation == "SCHEMA_IDENTITY_MATCHES_REGISTRY":
                ok, witness = self.op_schema_identity()
            elif operation == "RULE_COVERAGE_EXACT":
                ok, witness = self.op_rule_coverage()
            elif operation == "INVARIANT_SET_EXACT":
                ok, witness = self.op_invariant_set_exact()
            elif operation == "GOVERNING_AUTHORITY_REFERENCE_VALID":
                ok, witness = self.op_governing_authority()
            elif operation == "GOVERNING_TOKEN_SINGLETON":
                ok, witness = self.op_governing_token_singleton()
            elif operation == "TRUST_ANCHOR_COMPARE":
                result = self.trust_result()
                ok, witness = result["status"] == "PASS", result
            else:
                ok, witness = False, {"error": "UNSUPPORTED_OPERATION", "operation": operation}
        except Exception as exc:
            ok, witness = False, {"exception": type(exc).__name__ + ": " + str(exc)}
        return {"invariant_id": iid, "class": inv["class"], "status": "PASS" if ok else "FAIL",
                "procedure": inv["procedure_id"], "witness": witness,
                "failure_codes": [] if ok else inv["compatible_failure_codes"]}

    def run(self):
        classes, class_errors = self.class_map()
        arity_ok, arity_trace = self.arity()
        results = {iid: self.execute(iid, inv["default_arguments"])
                   for iid, inv in self.inv.items() if inv["status"] == "ACTIVE"}
        package_ids = [i for i, v in self.inv.items() if v["class"] == "PACKAGE_CONFORMANCE"]
        governance_ids = [i for i, v in self.inv.items() if v["class"] == "GOVERNANCE"]
        package_results = {i: results[i] for i in package_ids}
        governance_results = {i: results[i] for i in governance_ids}
        trust = results["TRUSTED_PACKAGE_IDENTITY"]

        bindings, groups, rule_results, internal_results = {}, {}, {}, {}
        for rule in self.rules["rules"]:
            cls = classes[rule["rule_id"]]
            if cls == "EXECUTABLE_CONFORMANCE_RULE":
                binding = rule["invariant_binding"]
                key = binding["invariant_id"] + "|" + rfc8785.dumps(binding["arguments"]).decode()
                if key not in bindings:
                    bindings[key] = self.execute(binding["invariant_id"], binding["arguments"])
                groups.setdefault(key, []).append(rule["rule_id"])
                rule_results[rule["rule_id"]] = bindings[key]["status"] if not class_errors else "FAIL"
            elif cls == "INTERNAL_DESIGN_INVARIANT":
                check = rule["internal_check"]
                actual = pointer(self.load(check["subject"]), check["pointer"])
                internal_results[rule["rule_id"]] = "PASS" if actual == check["expected"] else "FAIL"
            else:
                rule_results[rule["rule_id"]] = "DEFERRED"

        active_required = set(self.package["required_invariant_ids"])
        internal_conformance = (
            active_required == set(results)
            and arity_ok
            and not class_errors
            and all(r["status"] == "PASS" for r in package_results.values())
            and all(r["status"] == "PASS" for r in bindings.values())
            and all(v == "PASS" for v in internal_results.values()))
        governance_conformance = all(r["status"] == "PASS" for r in governance_results.values())
        conformance_rules = [r for r in self.rules["rules"]
                             if classes[r["rule_id"]] == "EXECUTABLE_CONFORMANCE_RULE"]
        deferred_rules = [r for r in self.rules["rules"]
                          if classes[r["rule_id"]] == "DEFERRED_NO_SUBJECT_ARTIFACT"]
        counts = {
            "TOTAL_RULES": len(self.rules["rules"]),
            "CONFORMANCE_MEMBER_RULES": len(conformance_rules),
            "INDEPENDENT_BINDINGS": len(bindings),
            "INTERNAL_DESIGN_INVARIANTS": len(internal_results),
            "DEFERRED_RULES": len(deferred_rules),
            "PACKAGE_INVARIANTS": len(package_results),
            "GOVERNANCE_INVARIANTS": len(governance_results),
            "PACKAGE_INVARIANTS_PASS": sum(r["status"] == "PASS" for r in package_results.values()),
            "GOVERNANCE_INVARIANTS_PASS": sum(r["status"] == "PASS" for r in governance_results.values()),
        }
        def witness(ident):
            return package_results.get(ident, {}).get("witness", {})

        v013 = witness("NEGATIVE_REQUIREMENT_MAP_CLOSURE")
        return {
            "certificate": "ACCORD-02E4R5R3_PRIMARY",
            "read_only": True,
            "repository_write_count": 0,
            "internal_package_conformance": "PASS" if internal_conformance else "FAIL",
            "governance_conformance": "PASS" if governance_conformance else "FAIL",
            "trusted_package_identity": trust["witness"],
            "active_object_set": sorted((o["kind"], o["id"], o["version"])
                                        for o in self.active_normative()),
            "schema_result_set": witness("STANDARDS_VALIDATION").get("schemas", {}),
            "reference_edge_set": witness("TYPED_REFERENCE_CLOSURE").get("edges", []),
            "package_invariant_map": {i: r["status"] for i, r in package_results.items()},
            "governance_invariant_map": {i: r["status"] for i, r in governance_results.items()},
            "binding_map": {k: v["status"] for k, v in bindings.items()},
            "member_rule_map": {r["rule_id"]: classes[r["rule_id"]] for r in self.rules["rules"]},
            "internal_map": internal_results,
            "rule_set": sorted(r["rule_id"] for r in self.rules["rules"]),
            "class_map": classes,
            "class_errors": class_errors,
            "arity_trace": arity_trace,
            "procedure_role_closure": {i: self.inv[i]["procedure_id"] for i in self.inv},
            "invariant_failure_code_map": {i: r["failure_codes"] for i, r in results.items()},
            "v013_requirement_map_result": v013,
            "v013_result": v013.get("result"),
            "expectation_stability_result": witness("EXPECTATION_STABILITY"),
            "counts": counts,
            "overall_pass": internal_conformance and governance_conformance
                            and trust["status"] == "PASS",
        }


def build_external(args):
    if args.verification_input:
        source = args.verification_input
        if source.lstrip().startswith("{"):
            return json.loads(source)
        return read(source)
    if args.expected_package_digest:
        return {
            "input_type": "EXTERNAL_VERIFICATION_INPUT",
            "package_id": args.expected_package_id,
            "package_version": args.expected_package_version,
            "package_digest": args.expected_package_digest,
            "trust_root": {"root_id": "cli:--expected-package-*",
                           "root_kind": "PINNED_ACCEPTED_TRUST_ROOT"},
        }
    return None


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--expected-package-id")
    parser.add_argument("--expected-package-version")
    parser.add_argument("--expected-package-digest")
    parser.add_argument("--verification-input")
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    try:
        report = Engine(args.root, build_external(args)).run()
    except Exception as exc:
        report = {"certificate": "ACCORD-02E4R5R3_PRIMARY", "overall_pass": False,
                  "fatal": type(exc).__name__ + ": " + str(exc)}
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report.get("overall_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
