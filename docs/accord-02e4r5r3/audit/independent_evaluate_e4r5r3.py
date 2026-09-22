#!/usr/bin/env python3
"""Independent evaluator for the ACCORD-02E4R5R3 specification package.

Deliberately written from the same normative artifacts with its own pointer
walker, its own dispatch table and its own V013 requirement engine.  It shares
no semantic helper with the primary evaluator.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import rfc8785

REL = "docs/accord-02e4r5r3"
CATALOG = {"kind": "SOURCE_VECTOR_CATALOG",
           "id": "urn:moirae:accord-02r5:source-vector-catalog", "version": "0.1"}
ROLE_TOKEN = re.compile(r"^([a-z0-9_]+):/")


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def canon(value):
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def navigate(value, path):
    if path in ("", "/"):
        return value
    for raw in path.split("/")[1:]:
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            value = value[int(token)]
        else:
            value = value[token]
    return value


def clock(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def roles_in(node, acc):
    if isinstance(node, dict):
        for value in node.values():
            roles_in(value, acc)
    elif isinstance(node, list):
        for value in node:
            roles_in(value, acc)
    elif isinstance(node, str):
        hit = ROLE_TOKEN.match(node)
        if hit:
            acc.add(hit.group(1))


def key_sites(node, name, acc, prefix=""):
    if isinstance(node, dict):
        for label, value in node.items():
            if label == name:
                acc.append(prefix + "/" + label)
            key_sites(value, name, acc, prefix + "/" + label)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            key_sites(value, name, acc, prefix + "/" + str(index))


class IndependentEvaluator:
    def __init__(self, root, external=None):
        self.base = Path(root).resolve()
        self.pkgdir = self.base / REL
        self.external = external
        self.registry = load_json(self.pkgdir / "object-registry.json")
        self.package = load_json(self.pkgdir / "specification-package-0.2.json")
        self.rule_registry = load_json(self.pkgdir / "rule-registry.json")
        self.invariant_registry = load_json(self.pkgdir / "invariant-registry.json")
        self.procedure_registry = load_json(self.pkgdir / "procedure-registry.json")
        self.reference_model = load_json(self.pkgdir / "reference-model.json")
        self.authority = load_json(self.pkgdir / "authority-requirements.json")
        self.governance = load_json(self.pkgdir / "governance-requirements.json")
        self.modes = load_json(self.pkgdir / "integrity-modes.json")
        self.semantic_keys = load_json(self.pkgdir / "semantic-key-authority.json")
        self.inputs = load_json(self.pkgdir / "normative-inputs.json")
        self.bindings = load_json(self.pkgdir / "accepted-source-bindings.json")
        self.canon_profile = load_json(self.pkgdir / "canonicalization-profile.json")
        self.partial = load_json(self.pkgdir / "partial-effect-policy.json")
        self.target = load_json(self.pkgdir / "v013-target.json")
        self.evidence = load_json(self.pkgdir / "v013-evidence.json")
        self.v013 = load_json(self.pkgdir / "v013-governance.json")
        self.propositions = load_json(self.pkgdir / "proposition-inventory.json")
        self.source_binding = load_json(self.pkgdir / "source-catalog-binding.json")
        self.objects = self.registry["objects"]
        self.by_key = {}
        for item in self.objects:
            self.by_key.setdefault((item["kind"], item["id"], item["version"]), []).append(item)
        self.invariants = {row["invariant_id"]: row for row in self.invariant_registry["invariants"]}
        self.procedures = {row["procedure_id"]: row for row in self.procedure_registry["procedures"]}
        self.mode_table = {row["mode"]: row for row in self.modes["modes"]}

    # ------------------------------------------------------- package plumbing
    def resolve(self, ref):
        if not isinstance(ref, dict) or "kind" not in ref:
            raise ValueError("malformed reference")
        candidates = self.by_key.get((ref["kind"], ref["id"], ref["version"]), [])
        if len(candidates) != 1:
            raise ValueError("expected exactly one target")
        if ref.get("member_id") and ref["member_id"] not in candidates[0].get("members", []):
            raise ValueError("member not present")
        return candidates[0]

    def document(self, ref):
        return load_json(self.base / self.resolve(ref)["path"])

    def package_universe(self):
        return [item for item in self.objects
                if item["status"] == "ACTIVE" and item["classification"] == "NORMATIVE"]

    # ------------------------------------------------------------ checks
    def check_integrity_modes(self):
        outcome = {}
        okay = True
        for item in self.package_universe():
            mode = item["integrity"].get("mode")
            spec = self.mode_table.get(mode)
            if spec is None:
                outcome[item["id"]] = {"status": "FAIL", "failure_code":
                                       self.modes["dispatch"]["unknown_mode_failure_code"]}
                okay = False
                continue
            try:
                verdict = self._integrity_verdict(item, mode)
            except Exception as exc:
                verdict = False
                spec = {**spec, "detail": type(exc).__name__ + ": " + str(exc)}
            outcome[item["id"]] = {"status": "PASS" if verdict else "FAIL",
                                   "failure_code": spec["failure_code"]}
            okay = okay and verdict
        return okay, outcome

    def _integrity_verdict(self, item, mode):
        where = self.base / item["path"]
        payload = item["integrity"]
        if mode == "SEMANTIC_JSON_CONTENT":
            return canon(load_json(where)) == payload.get("digest")
        if mode == "RAW_FILE_BYTES":
            return hashlib.sha256(where.read_bytes()).hexdigest() == payload.get("digest")
        if mode == "PACKAGE_PINNED_BOOTSTRAP":
            return canon(load_json(where)) == self.package.get("registry_semantic_sha256")
        if mode == "SELF_DIGEST":
            document = load_json(where)
            want = document["current_candidate_integrity"]["digest"]
            clone = json.loads(json.dumps(document))
            del clone["current_candidate_integrity"]["digest"]
            return canon(clone) == want
        if mode == "DUAL_ACCEPTED_SOURCE":
            bound = self.document(payload["binding_ref"])
            record = [row for row in bound["sources"] if row["path"] == item["path"]]
            if len(record) != 1:
                raise ValueError("source not uniquely bound")
            raw = where.read_bytes()
            claim = record[0]["integrity"]
            return (hashlib.sha256(raw).hexdigest() == claim["raw_file_bytes_sha256"]
                    and canon(json.loads(raw)) == claim["semantic_json_content_sha256"])
        raise ValueError("unhandled mode " + str(mode))

    def check_schema_universe(self):
        compiled = {}
        outcome = {}
        for item in self.objects:
            if item["kind"] == "SCHEMA" and item["status"] == "ACTIVE":
                document = load_json(self.base / item["path"])
                jsonschema.Draft202012Validator.check_schema(document)
                compiled[item["id"]] = document
                outcome[item["id"]] = "PASS"
        for item in self.package_universe():
            if item["kind"] == "SCHEMA":
                continue
            ref = item["schema_ref"]
            jsonschema.validate(load_json(self.base / item["path"]), compiled[ref["id"]])
            outcome[item["id"]] = "PASS"
        return True, {"schemas": outcome}

    def derive_edges(self):
        shape = self.reference_model["shape_predicate"]
        signature = set(shape["required_keys"])
        extras = set(shape["optional_keys"])
        permissive = shape["additional_keys"] == "ALLOW"
        bucket = set()

        def visit(node, owner, trail=""):
            if isinstance(node, dict):
                labels = set(node)
                if signature <= labels and (permissive or labels <= signature | extras) \
                        and all(isinstance(v, str) for v in node.values()):
                    bucket.add((owner["kind"], owner["id"], owner["version"], trail,
                                node["kind"], node["id"], node["version"], node.get("member_id", "")))
                for label, child in node.items():
                    visit(child, owner, trail + "/" + label.replace("~", "~0").replace("/", "~1"))
            elif isinstance(node, list):
                for index, child in enumerate(node):
                    visit(child, owner, trail + "/" + str(index))

        for owner in self.package_universe():
            visit(load_json(self.base / owner["path"]), owner)
        return sorted(bucket)

    def check_references(self):
        edges = self.derive_edges()
        broken = []
        for edge in edges:
            ref = {"kind": edge[4], "id": edge[5], "version": edge[6]}
            if edge[7]:
                ref["member_id"] = edge[7]
            try:
                self.resolve(ref)
            except Exception as exc:
                broken.append({"edge": list(edge), "error": str(exc)})
        return not broken, {"edges": [list(e) for e in edges], "unresolved_or_ambiguous": broken}

    def class_partition(self):
        classes = {}
        invalid = set()
        for row in self.rule_registry["rules"]:
            rid = row["rule_id"]
            if "invariant_binding" in row:
                label = "EXECUTABLE_CONFORMANCE_RULE"
                binding = row["invariant_binding"]
                target = self.invariants.get(binding["invariant_id"])
                good = target is not None and target["status"] == "ACTIVE" \
                    and set(binding["arguments"]) == {r["role"] for r in target["input_roles"] if r["required"]} \
                    and binding["arguments"] == target["default_arguments"] \
                    and row["inherited_failure_code"] in target["compatible_failure_codes"] \
                    and "subjects" not in row
                if good:
                    for spec in target["input_roles"]:
                        argument = binding["arguments"].get(spec["role"])
                        good = good and argument is not None and argument.get("kind") == spec["kind"]
                        try:
                            self.resolve(argument)
                        except Exception:
                            good = False
                if not good:
                    invalid.add(rid)
            elif "internal_check" in row and "invariant_binding" not in row:
                label = "INTERNAL_DESIGN_INVARIANT"
            elif row.get("missing_subject_roles") and row.get("later_lifecycle_stage") \
                    and "internal_check" not in row and "invariant_binding" not in row:
                label = "DEFERRED_NO_SUBJECT_ARTIFACT"
            else:
                label = "INVALID"
                invalid.add(rid)
            classes[rid] = label
            if label != row["declared_class"]:
                invalid.add(rid)
        return classes, invalid

    # ------------------------------------------------------- V013 evaluation
    POLICIES = {
        "EXACT_EQUAL": "pair",
        "TUPLE_EQUAL": "scope",
        "RFC3339_ORDER_INCLUSIVE": "interval_valid",
        "INTERVAL_COVERAGE_INCLUSIVE_BOTH_ENDS": "coverage",
        "RETENTION_GTE_MAX_SPAN_AND_PROFILE_MIN": "retention",
        "MEMBERSHIP": "membership",
        "AGE_WITHIN_PROFILE_MAX": "freshness",
        "COMPLETE_READ_REQUIRED": "complete_read",
        "ADMISSIBLE_POSITIVE_SAME_TARGET_COUNT_ZERO": "contradiction",
        "OBSERVATION_NOT_IN_FUTURE": "future",
        "OBSERVATION_NOT_STALE": "stale",
        "UNIVERSE_ITEMS_TYPED_CLOSED": "universe",
        "CALLER_SUPPLIED_COUNT_FORBIDDEN": "caller_count",
    }

    def run_requirement(self, requirement, policy):
        kind = self.POLICIES[requirement["procedure"]]
        target, evidence = self.target, self.evidence
        if kind == "pair":
            fields = requirement["source_fields"]
            bag = {"target": target, "evidence": evidence}
            return navigate(bag, "/" + fields[0].replace(".", "/")) == \
                navigate(bag, "/" + fields[1].replace(".", "/"))
        if kind == "scope":
            return target["scope"] == evidence["scope"]
        if kind == "interval_valid":
            span = evidence["observed_interval"]
            return clock(span["not_before"]) <= clock(span["as_of"])
        if kind == "coverage":
            need, have = target["required_interval"], evidence["observed_interval"]
            return clock(have["not_before"]) <= clock(need["not_before"]) \
                and clock(need["as_of"]) <= clock(have["as_of"])
        if kind == "retention":
            need = target["required_interval"]
            duration = (clock(need["as_of"]) - clock(need["not_before"])).total_seconds()
            return evidence["retention_window_seconds"] >= max(duration, policy["minimum_retention_seconds"])
        if kind == "membership":
            if requirement["requirement_id"] == "CONSISTENCY_ALLOWED":
                return evidence["consistency_level"] in policy["allowed_consistency_levels"]
            return evidence["evidence_class"] in policy["allowed_source_classes"]
        if kind == "freshness":
            age = (clock(evidence["verification_time"]) - clock(evidence["observed_at"])).total_seconds()
            return 0 <= age <= policy["freshness_max_age_seconds"]
        if kind == "complete_read":
            return policy["complete_read_requirement"] == "COMPLETE_LEDGER_QUERY_REQUIRED" \
                and evidence["read_scope_complete"] is True \
                and evidence["read_semantics"] == "COMPLETE_LEDGER_QUERY"
        if kind == "contradiction":
            if policy["contradiction_rule"] != "FORBID_ADMISSIBLE_SAME_TARGET_POSITIVE":
                return False
            wanted = (target["effect_id"], target["negated_predicate_id"],
                      target["negated_stage"], target["scope"])
            ids = set()
            for entry in evidence["evidence_universe"]:
                # 'admissible' is mandatory; a missing key is a hard failure.
                if not entry["admissible"] or entry["polarity"] != "POSITIVE":
                    continue
                if (entry["effect_id"], entry["predicate_id"], entry["stage"], entry["scope"]) != wanted:
                    continue
                ids.add(entry["evidence_id"])
            return len(ids) == 0
        if kind == "future":
            declared = policy["future_observation_result"]
            if declared not in self.v013["result_vocabulary"] or declared == self.v013["pass_result"]:
                return False
            return clock(evidence["observed_at"]) <= clock(evidence["verification_time"])
        if kind == "stale":
            declared = policy["stale_result"]
            if declared not in self.v013["result_vocabulary"] or declared == self.v013["pass_result"]:
                return False
            age = (clock(evidence["verification_time"]) - clock(evidence["observed_at"])).total_seconds()
            return age <= policy["freshness_max_age_seconds"]
        if kind == "universe":
            required = {"evidence_id", "effect_id", "predicate_id", "stage", "scope", "polarity",
                        "relationship", "admissible", "observed_interval", "consistency_level",
                        "source_class"}
            return all(set(entry) == required and isinstance(entry["admissible"], bool)
                       for entry in evidence["evidence_universe"])
        if kind == "caller_count":
            return not any(field in target or field in evidence
                           for field in self.v013["requirement_map"]["forbidden_requirements"])
        raise ValueError("unknown requirement kind")

    def v013_result(self):
        requirement_map = self.v013["requirement_map"]
        policy = self.inputs["profile"]["negative_policy"]
        listed = [row["requirement_id"] for row in requirement_map["requirements"]]
        order = requirement_map["evaluation_order"]
        required = requirement_map["required_requirement_ids"]
        structural = (sorted(set(listed)) == sorted(set(required))
                      and len(listed) == len(set(listed))
                      and len(order) == len(set(order)) and set(order) == set(listed)
                      and sorted(self.v013["policy_field_roles"]) == sorted(policy))
        index = {row["requirement_id"]: row for row in requirement_map["requirements"]}
        detail = {}
        verdict = structural
        for rid in order:
            row = index.get(rid)
            if row is None:
                detail[rid] = {"status": "FAIL", "reason": "MISSING_REQUIREMENT"}
                verdict = False
                continue
            try:
                passed = bool(self.run_requirement(row, policy))
                note = "EVALUATED"
            except Exception as exc:
                passed = False
                note = type(exc).__name__ + ": " + str(exc)
            detail[rid] = {"status": "PASS" if passed else "FAIL", "failure_code": row["failure_code"],
                           "note": note}
            verdict = verdict and passed
        return verdict, {"structural": structural, "requirements": detail,
                         "result": self.v013["pass_result"] if verdict else self.v013["fail_result"]}

    # ---------------------------------------------------- invariant handlers
    def handler_table(self):
        return {
            "STANDARDS_VALIDATION": lambda args: self.check_schema_universe(),
            "PACKAGE_LINEAGE": lambda args: self.check_lineage(),
            "PROFILE_REFERENCE_PINNING": lambda args: self.check_profile_pin(),
            "ACCEPTED_BASE_DUAL_INTEGRITY": lambda args: self.check_accepted_integrity(),
            "ACCEPTED_SOURCE_DUAL_INTEGRITY": lambda args: self.check_accepted_integrity(),
            "OBJECT_IDENTITY_UNIQUE": lambda args: self.check_identity_unique(),
            "TYPED_REFERENCE_CLOSURE": lambda args: self.check_references(),
            "SEMANTIC_DIGEST_VERIFY": lambda args: self.check_integrity_modes(),
            "INTEGRITY_MODE_DISPATCH": lambda args: self.check_integrity_modes(),
            "DEPENDENCY_GRAPH_EQUAL": lambda args: self.check_graph_equality(),
            "EXPECTATION_STABILITY": lambda args: self.check_expectation_stability(),
            "PREDICATE_AUTHORITY_CLOSURE": lambda args: self.check_predicate_agreement(),
            "CANONICALIZATION_AUTHORITY_CLOSURE": lambda args: self.check_canon_agreement(),
            "SOURCE_CATALOG_BINDING": lambda args: self.check_source_binding(),
            "PARTIAL_EFFECT_POLICY_CLOSURE": lambda args: self.check_partial_closure(),
            "NEGATIVE_REQUIREMENT_MAP_CLOSURE": lambda args: self.v013_result(),
            "RULE_EXPECTATION_AUTHORITY_COMPLETE": lambda args: self.check_authority_closure(),
            "PROPOSITION_INVENTORY_BOUND": lambda args: self.check_propositions(),
            "INVARIANT_PROCEDURE_ARITY_AGREEMENT": lambda args: self.check_arity(),
            "SCHEMA_NON_VACUITY": lambda args: self.check_non_vacuity(),
            "CURRENT_PACKAGE_IDENTITY": lambda args: self.check_current_identity(args),
            "PACKAGE_SELF_DIGEST": lambda args: self.check_self_digest(),
            "V013_BASIS_VALID": lambda args: self.check_v013_basis(),
            "FAIL_CLOSED_ENFORCED": lambda args: self.check_fail_closed(),
            "SUBJECT_ROLE_COVERAGE": lambda args: self.check_subject_roles(),
            "DEFAULT_ARGUMENT_COVERAGE": lambda args: self.check_default_arguments(),
            "DERIVATION_ROLE_CLOSURE": lambda args: self.check_role_closure(),
            "PROCEDURE_OPERATION_SUPPORTED": lambda args: self.check_operations(),
            "MISSING_BEHAVIOR_SUPPORTED": lambda args: self.check_behavior("missing_behavior"),
            "AMBIGUITY_BEHAVIOR_SUPPORTED": lambda args: self.check_behavior("ambiguity_behavior"),
            "REFERENCE_DISCOVERY_SCOPE_VALID": lambda args: self.check_discovery_scope(),
            "REFERENCE_SHAPE_PREDICATE_APPLIED": lambda args: self.check_shape_predicate(),
            "UNIQUENESS_KEY_APPLIED": lambda args: self.check_uniqueness_key(),
            "ROLE_MODEL_APPLIED": lambda args: self.check_role_model(),
            "SCHEMA_IDENTITY_MATCHES_REGISTRY": lambda args: self.check_schema_identity(),
            "RULE_COVERAGE_EXACT": lambda args: self.check_rule_coverage(),
            "INVARIANT_SET_EXACT": lambda args: self.check_invariant_set(),
            "GOVERNING_AUTHORITY_REFERENCE_VALID": lambda args: self.check_governing_authority(),
            "GOVERNING_TOKEN_SINGLETON": lambda args: self.check_token_singleton(),
            "TRUSTED_PACKAGE_IDENTITY": lambda args: self.check_trust(),
        }

    def check_lineage(self):
        required = self.authority["package_requirements"]
        wanted = required["required_rejected_revision"]
        rows = [{k: r[k] for k in ("revision", "commit") if k in r}
                for r in self.package["rejected_candidate_lineage"]]
        ok = (self.package["package_id"] == required["family"]
              and self.package["package_version"] == required["version"]
              and self.package["status"] == required["status"] and wanted in rows)
        return ok, {"required": wanted}

    def check_profile_pin(self):
        return (self.inputs["profile"]["object_version"]
                == self.authority["package_requirements"]["version"]), {}

    def check_accepted_integrity(self):
        verdict = True
        note = {}
        for row in self.bindings["sources"]:
            raw = (self.base / row["path"]).read_bytes()
            claim = row["integrity"]
            ok = (hashlib.sha256(raw).hexdigest() == claim["raw_file_bytes_sha256"]
                  and canon(json.loads(raw)) == claim["semantic_json_content_sha256"])
            note[row["path"]] = "PASS" if ok else "FAIL"
            verdict = verdict and ok
        return verdict, note

    def check_identity_unique(self):
        keys = [(o["kind"], o["id"], o["version"]) for o in self.objects]
        return len(keys) == len(set(keys)), {"count": len(keys)}

    def check_graph_equality(self):
        left = {(r["rule_id"], dep) for r in self.inputs["rule_dependencies"] for dep in r["depends_on"]}
        right = {(e["from"], e["to"]) for e in self.inputs["dependency_edges"]}
        return left == right, {"edges": len(left)}

    def check_expectation_stability(self):
        mine = {r["vector_id"]: r["expected"] for r in self.inputs["vector_expectations"]}
        theirs = {r["vector_id"]: r["expected"] for r in self.document(CATALOG)["vectors"]}
        return mine == theirs, {"vector_ids": len(mine),
                                "changed": sorted(k for k in set(mine) | set(theirs)
                                                  if mine.get(k) != theirs.get(k))}

    def check_predicate_agreement(self):
        req = self.authority["stage_policy_requirements"]
        allowed = self.authority["stage_policy_authorization"]
        return (self.inputs["predicate_policy"] == req
                and all(req[k] in allowed[k] for k in req)), {"required": req}

    def check_canon_agreement(self):
        req = self.authority["canonicalization_requirements"]
        return {k: self.canon_profile[k] for k in req} == req, {}

    def check_source_binding(self):
        cand = self.source_binding["candidate_binding"]
        mapping = self.source_binding["field_vocabulary_mapping"]
        catalog_objects = [o for o in self.objects if o["kind"] == "SOURCE_VECTOR_CATALOG"]
        accepted = [s for s in self.bindings["sources"]
                    if s["ref"]["kind"] == "SOURCE_VECTOR_CATALOG"]
        conditions = []
        conditions.append(len(catalog_objects) == 1)
        if len(catalog_objects) != 1 or len(accepted) != 1:
            return False, {"reason": "catalog binding cardinality"}
        target, bound = catalog_objects[0], accepted[0]
        conditions.append(cand["assigned_kind"] == target["kind"]
                          and cand["assigned_id"] == target["id"]
                          and cand["assigned_version"] == target["version"])
        conditions.append(cand["repository_root_path"] == bound["path"])
        by_path = [o for o in self.objects if o["path"] == cand["repository_root_path"]]
        conditions.append(len(by_path) == 1 and by_path[0]["kind"] == "SOURCE_VECTOR_CATALOG")
        raw = (self.base / cand["repository_root_path"]).read_bytes()
        semantic = canon(json.loads(raw))
        raw_digest = hashlib.sha256(raw).hexdigest()
        conditions.append(cand["semantic_json_content_sha256"] == semantic
                          == bound["integrity"]["semantic_json_content_sha256"])
        conditions.append(cand["raw_file_bytes_sha256"] == raw_digest
                          == bound["integrity"]["raw_file_bytes_sha256"])
        mode = self.mode_table.get(cand["declared_integrity_class"])
        conditions.append(mode is not None)
        if mode is not None:
            conditions.append(cand["declared_canonicalization"]
                              == mode[mapping["declared_canonicalization"]])
            conditions.append(cand["declared_algorithm"] == mode[mapping["declared_algorithm"]])
        return all(conditions), {"satisfied": len(conditions)}

    def check_partial_closure(self):
        req = self.authority["partial_effect_requirements"]
        ok = (self.partial["same_effect_required"] == req["same_effect_required"]
              and self.partial["direct_predecessor_required"] == req["direct_predecessor_required"]
              and self.partial["decisions"][req["merged_decision_key"]] == req["merged_decision_value"])
        return ok, {}

    def check_authority_closure(self):
        classes, invalid = self.class_partition()
        active = {k for k, v in self.invariants.items() if v["status"] == "ACTIVE"}
        required = set(self.package["required_invariant_ids"])
        bound = {r["invariant_binding"]["invariant_id"]
                 for r in self.rule_registry["rules"] if "invariant_binding" in r}
        loose = {k for k, v in self.invariants.items() if v["usage"] != "CONFORMANCE_BOUND"}
        ok = not invalid and active == required == (bound | loose)
        return ok, {"invalid": sorted(invalid)}

    def check_propositions(self):
        collections = self.propositions["collection_propositions"]
        members = self.propositions["member_propositions"]
        projections = self.propositions["projection_propositions"]
        extras = self.propositions["informational"]
        all_ids = [p["proposition_id"]
                   for p in collections + members + projections + extras]
        vectors = [r["vector_id"] for r in self.inputs["vector_expectations"]]
        collection_ids = {c["proposition_id"] for c in collections if c["normative"]}
        member_ids = {m["proposition_id"] for m in members if m["normative"]}
        projection_ids = {p["proposition_id"] for p in projections if p["normative"]}
        ok = (len(all_ids) == len(set(all_ids)) and len(vectors) == len(set(vectors))
              and member_ids == set(vectors)
              and (collection_ids | member_ids | projection_ids)
              == (set(vectors) | collection_ids | projection_ids)
              and all(m["member_of"] in collection_ids for m in members)
              and all(p["collection_proposition_id"] in collection_ids for p in projections))
        return ok, {"declared": len(all_ids)}

    def check_arity(self):
        for ident, inv in self.invariants.items():
            proc = self.procedures.get(inv["procedure_id"])
            if proc is None:
                return False, {"invariant": ident, "reason": "no procedure"}
            need = {r["role"] for r in inv["input_roles"] if r["required"]}
            have = {a["name"] for a in proc["arguments"] if a["required"]}
            if need != have or set(inv["default_arguments"]) != need or inv["fail_closed"] is not True:
                return False, {"invariant": ident}
        return True, {}

    def check_non_vacuity(self):
        for item in self.objects:
            if item["kind"] == "SCHEMA" and item["status"] == "ACTIVE":
                errors = list(jsonschema.Draft202012Validator(
                    load_json(self.base / item["path"])).iter_errors({"zzz": 1}))
                if not errors:
                    return False, {"schema": item["id"]}
        return True, {}

    def check_current_identity(self, args):
        required = self.authority["package_requirements"]
        hits = self.by_key.get(("PACKAGE", required["family"], required["version"]), [])
        return (len(hits) == 1 and hits[0]["path"] == self.resolve(args["package"])["path"]), \
            {"hits": [h["path"] for h in hits]}

    def check_self_digest(self):
        want = self.package["current_candidate_integrity"]["digest"]
        clone = json.loads(json.dumps(self.package))
        del clone["current_candidate_integrity"]["digest"]
        return canon(clone) == want, {}

    def check_v013_basis(self):
        basis = self.target["relationship_basis"]
        locator = self.v013["accepted_v013_locator"]
        accepted = self.document(locator["source_ref"])
        member = [v for v in accepted["vectors"]
                  if v["vector_id"] == locator["accepted_member_id"]]
        if len(member) != 1:
            return False, {"reason": "accepted member not uniquely resolvable"}
        member = member[0]
        checks = [self.target["relationship"] in self.v013["relationship_vocabulary"]]
        for row in basis["accepted"]:
            if row["accepted_pointer"].endswith("/*"):
                checks.append(row["must_contain"] in navigate(member, row["accepted_pointer"][:-2]))
            else:
                checks.append(navigate(member, row["accepted_pointer"]) == row["must_equal"])
        accepted_ids = {r["field_id"] for r in basis["accepted"]}
        candidate_ids = {r["field_id"] for r in basis["candidate_supplied"]}
        checks.append(not (accepted_ids & candidate_ids))
        for row in basis["candidate_supplied"]:
            checks.append(row["provenance"] == "CANDIDATE_LOCAL_NOT_HISTORY"
                          and navigate(self.target, row["candidate_pointer"]) is not None
                          and row["candidate_pointer"].startswith(
                              self.v013["relationship_basis_schema"]["candidate_pointer_prefix"]))
        return all(checks), {"checks": len(checks)}

    def check_fail_closed(self):
        bad = [i["invariant_id"] for i in self.invariant_registry["invariants"]
               if i["acceptance_critical"] and i["fail_closed"] is not True]
        return not bad, {"not_fail_closed": bad}

    def check_subject_roles(self):
        bad = {}
        for inv in self.invariant_registry["invariants"]:
            allowed = {r["role"] for r in inv["input_roles"] if r["required"]}
            missing = [s for s in inv["subject_roles"] if s not in allowed]
            if missing or not inv["subject_roles"]:
                bad[inv["invariant_id"]] = missing
        return not bad, {"uncovered": bad}

    def check_default_arguments(self):
        bad = {}
        for inv in self.invariant_registry["invariants"]:
            proc = self.procedures.get(inv["procedure_id"])
            need = {r["role"] for r in inv["input_roles"] if r["required"]}
            args = {a["name"] for a in proc["arguments"]} if proc else set()
            issues = []
            if set(inv["default_arguments"]) != need:
                issues.append("role_set")
            for role, ref in inv["default_arguments"].items():
                spec = [r for r in inv["input_roles"] if r["role"] == role]
                if len(spec) != 1 or spec[0]["kind"] != ref.get("kind"):
                    issues.append("kind:" + role)
                    continue
                try:
                    self.resolve(ref)
                except Exception:
                    issues.append("resolve:" + role)
            if issues or args != need:
                bad[inv["invariant_id"]] = issues
        return not bad, {"violations": bad}

    def check_role_closure(self):
        bad = {}
        for inv in self.invariant_registry["invariants"]:
            proc = self.procedures.get(inv["procedure_id"])
            used = set()
            roles_in(proc["derivation"], used)
            need = {r["role"] for r in inv["input_roles"] if r["required"]}
            args = {a["name"] for a in proc["arguments"] if a["required"]}
            if not (need == args == used):
                bad[inv["invariant_id"]] = {"need": sorted(need), "args": sorted(args),
                                            "used": sorted(used)}
        return not bad, {"violations": bad}

    def check_operations(self):
        supported = set(self.governance["supported_operations"])
        bad = [p["procedure_id"] for p in self.procedure_registry["procedures"]
               if p["derivation"]["operation"] not in supported]
        return not bad, {"unsupported": bad}

    def check_behavior(self, field):
        vocabulary = set(self.governance["behavior_vocabulary"][field])
        bad = [p["procedure_id"] for p in self.procedure_registry["procedures"]
               if p[field] not in vocabulary]
        return not bad, {"field": field, "unsupported": bad}

    def check_discovery_scope(self):
        scope = self.reference_model["discovery_scope"]
        found = [o for o in self.objects if o["status"] == scope["registry_status"]
                 and o["classification"] == scope["classification"]]
        return len(found) > 0, {"size": len(found)}

    def check_shape_predicate(self):
        shape = self.reference_model["shape_predicate"]
        rule = self.governance["shape_predicate_requirement"]
        return shape["additional_keys"] in rule["allowed_additional_keys"], \
            {"additional_keys": shape["additional_keys"]}

    def check_uniqueness_key(self):
        want = self.governance["uniqueness_key_requirement"]["identity_fields"]
        if self.registry["uniqueness_key"] != want or self.registry["identity_fields"] != want:
            return False, {"key": self.registry["uniqueness_key"]}
        keys = [tuple(o[f] for f in self.registry["uniqueness_key"]) for o in self.objects]
        return len(keys) == len(set(keys)), {"key": want}

    def check_role_model(self):
        vocab = set(self.registry["role_vocabulary"])
        unknown = [o["id"] for o in self.objects if any(r not in vocab for r in o["roles"])]
        ok = self.registry["role_model"] == self.governance["role_model_requirement"]["required_role_model"] \
            and not unknown
        return ok, {"unknown": unknown}

    def check_schema_identity(self):
        schemas = {o["id"]: o for o in self.objects if o["kind"] == "SCHEMA"}
        bad = {}
        for item in self.objects:
            ref = item.get("schema_ref")
            if not ref:
                continue
            target = schemas.get(ref["id"])
            if target is None:
                bad[item["id"]] = "missing"
                continue
            expected = "urn:moirae:accord-02r5r3:schema:" + \
                Path(target["path"]).name[:-len(".schema.json")]
            if target["id"] != expected or load_json(self.base / target["path"]).get("$id") != expected + ":0.2":
                bad[item["id"]] = expected
        return not bad, {"mismatches": bad}

    def check_rule_coverage(self):
        required = self.rule_registry["provenance"]["required_rule_ids"]
        actual = [r["rule_id"] for r in self.rule_registry["rules"]]
        return (len(actual) == len(set(actual)) and set(actual) == set(required)
                and len(actual) == len(required)), \
            {"required": len(required), "actual": len(actual)}

    def check_invariant_set(self):
        required = self.package["required_invariant_ids"]
        active = [i["invariant_id"] for i in self.invariant_registry["invariants"]
                  if i["status"] == "ACTIVE"]
        return (len(required) == len(set(required)) and set(required) == set(active)), \
            {"required": len(required), "active": len(active)}

    def check_governing_authority(self):
        roots = set(self.v013["authority_roots"])
        bad = [r["requirement_id"] for r in self.v013["requirement_map"]["requirements"]
               if r["governing_authority"] not in roots]
        ids = {r["requirement_id"] for r in self.v013["requirement_map"]["requirements"]}
        for field, role in self.v013["policy_field_roles"].items():
            if not role.startswith("COMPUTED:") or role.split(":", 1)[1] not in ids:
                bad.append("POLICY_FIELD:" + field)
        return not bad, {"unresolved": bad}

    def check_token_singleton(self):
        policy = self.semantic_keys["governing_token_singleton"]
        skip_kinds = set(policy["scan_excludes_kinds"])
        skip_prefixes = tuple(policy["scan_excluded_pointer_prefixes"])
        exempt = set(policy["permitted_exception_roles"])
        duplicates = []
        kind_for_role = {"authority": "AUTHORITY", "inputs": "NORMATIVE_INPUTS",
                         "canonicalization": "CANONICALIZATION", "references": "CONTRACT",
                         "registry": "REGISTRY", "partial": "POLICY"}
        for key in self.semantic_keys["semantic_keys"]:
            allowed = set()
            for declared in [key["authority_path"], *key["governed_mirror_paths"]]:
                if ":/" in declared:
                    role, path = declared.split(":/", 1)
                    allowed.add((kind_for_role.get(role), "/" + path))
            for item in self.package_universe():
                if item["kind"] in skip_kinds or (exempt & set(item.get("roles", []))):
                    continue
                found = []
                key_sites(load_json(self.base / item["path"]), key["key"], found)
                for site in found:
                    if site.startswith(skip_prefixes) or (item["kind"], site) in allowed:
                        continue
                    duplicates.append(key["key"] + "@" + item["id"] + site)
        return not duplicates, {"duplicates": duplicates}

    def check_trust(self):
        identity = {"package_id": self.package["package_id"],
                    "package_version": self.package["package_version"]}
        clone = json.loads(json.dumps(self.package))
        del clone["current_candidate_integrity"]["digest"]
        identity["package_digest"] = canon(clone)
        if self.external is None:
            return False, {"status": "FAIL", "code": "MISSING_EXTERNAL_TRUST_INPUT",
                           "recomputed_identity": identity}
        root = self.external.get("trust_root") or {}
        if root.get("root_kind") == "REPLACED_TRUST_ROOT":
            return False, {"status": "DIFFERENT_PACKAGE_VERIFIED",
                           "sub_status": "OUT_OF_SCOPE_TRUST_ROOT_REPLACEMENT",
                           "recomputed_identity": identity}
        if root.get("root_kind") != "PINNED_ACCEPTED_TRUST_ROOT":
            return False, {"status": "FAIL", "code": "EXTERNAL_INPUT_INVALID",
                           "recomputed_identity": identity}
        if (self.external.get("package_id") != identity["package_id"]
                or self.external.get("package_version") != identity["package_version"]):
            return False, {"status": "FAIL", "code": "FOREIGN_PACKAGE_IDENTITY",
                           "recomputed_identity": identity}
        if self.external.get("package_digest") != identity["package_digest"]:
            return False, {"status": "FAIL", "code": "TRUSTED_IDENTITY_MISMATCH",
                           "recomputed_identity": identity}
        return True, {"status": "PASS", "recomputed_identity": identity}

    # --------------------------------------------------------------- driver
    def run(self):
        table = self.handler_table()
        classes, invalid = self.class_partition()
        package_ids = [k for k, v in self.invariants.items()
                       if v["class"] == "PACKAGE_CONFORMANCE" and v["status"] == "ACTIVE"]
        governance_ids = [k for k, v in self.invariants.items()
                          if v["class"] == "GOVERNANCE" and v["status"] == "ACTIVE"]
        all_ids = [k for k, v in self.invariants.items() if v["status"] == "ACTIVE"]
        produced = {}
        for ident in all_ids:
            inv = self.invariants[ident]
            try:
                for role, ref in inv["default_arguments"].items():
                    self.resolve(ref)
                ok, note = table[ident](inv["default_arguments"])
            except Exception as exc:
                ok, note = False, {"exception": type(exc).__name__ + ": " + str(exc)}
            produced[ident] = {"status": "PASS" if ok else "FAIL",
                               "failure_codes": [] if ok else inv["compatible_failure_codes"],
                               "note": note}

        bindings, groups, rules, internal = {}, {}, {}, {}
        for row in self.rule_registry["rules"]:
            label = classes[row["rule_id"]]
            if label == "EXECUTABLE_CONFORMANCE_RULE":
                binding = row["invariant_binding"]
                token = binding["invariant_id"] + "|" + rfc8785.dumps(binding["arguments"]).decode()
                if token not in bindings:
                    inv = self.invariants.get(binding["invariant_id"])
                    if inv is None or binding["invariant_id"] not in table:
                        bindings[token] = {"status": "FAIL",
                                           "failure_codes": [binding["invariant_id"] + "_FAILURE"]}
                    else:
                        try:
                            ok, note = table[binding["invariant_id"]](binding["arguments"])
                        except Exception as exc:
                            ok, note = False, {"exception": str(exc)}
                        bindings[token] = {"status": "PASS" if ok else "FAIL",
                                           "failure_codes": [] if ok else inv["compatible_failure_codes"]}
                groups.setdefault(token, []).append(row["rule_id"])
                rules[row["rule_id"]] = "FAIL" if invalid else bindings[token]["status"]
            elif label == "INTERNAL_DESIGN_INVARIANT":
                check = row["internal_check"]
                got = navigate(self.document(check["subject"]), check["pointer"])
                internal[row["rule_id"]] = "PASS" if got == check["expected"] else "FAIL"
            else:
                rules[row["rule_id"]] = "DEFERRED"

        arity_ok, _ = self.check_arity()
        internal_ok = (set(self.package["required_invariant_ids"]) == set(all_ids)
                       and arity_ok and not invalid
                       and all(produced[k]["status"] == "PASS" for k in package_ids)
                       and all(v["status"] == "PASS" for v in bindings.values())
                       and all(v == "PASS" for v in internal.values()))
        governance_ok = all(produced[k]["status"] == "PASS" for k in governance_ids)
        def note(ident):
            return produced.get(ident, {}).get("note", {})

        trust = produced["TRUSTED_PACKAGE_IDENTITY"] if "TRUSTED_PACKAGE_IDENTITY" in produced \
            else {"status": "FAIL", "note": {"status": "FAIL", "code": "MISSING_INVARIANT"}}
        conf = [r for r in self.rule_registry["rules"]
                if classes[r["rule_id"]] == "EXECUTABLE_CONFORMANCE_RULE"]
        deferred = [r for r in self.rule_registry["rules"]
                    if classes[r["rule_id"]] == "DEFERRED_NO_SUBJECT_ARTIFACT"]
        return {
            "certificate": "ACCORD-02E4R5R3_INDEPENDENT",
            "read_only": True,
            "repository_write_count": 0,
            "internal_package_conformance": "PASS" if internal_ok else "FAIL",
            "governance_conformance": "PASS" if governance_ok else "FAIL",
            "trusted_package_identity": trust["note"],
            "active_object_set": sorted((o["kind"], o["id"], o["version"])
                                        for o in self.package_universe()),
            "schema_result_set": note("STANDARDS_VALIDATION").get("schemas", {}),
            "reference_edge_set": note("TYPED_REFERENCE_CLOSURE").get("edges", []),
            "package_invariant_map": {k: produced[k]["status"] for k in package_ids},
            "governance_invariant_map": {k: produced[k]["status"] for k in governance_ids},
            "binding_map": {k: v["status"] for k, v in bindings.items()},
            "member_rule_map": classes,
            "internal_map": internal,
            "rule_set": sorted(r["rule_id"] for r in self.rule_registry["rules"]),
            "class_map": classes,
            "procedure_role_closure": {k: self.invariants[k]["procedure_id"] for k in all_ids},
            "invariant_failure_code_map": {k: v["failure_codes"] for k, v in produced.items()},
            "v013_requirement_map_result": note("NEGATIVE_REQUIREMENT_MAP_CLOSURE"),
            "v013_result": note("NEGATIVE_REQUIREMENT_MAP_CLOSURE").get("result"),
            "expectation_stability_result": note("EXPECTATION_STABILITY"),
            "counts": {
                "TOTAL_RULES": len(self.rule_registry["rules"]),
                "CONFORMANCE_MEMBER_RULES": len(conf),
                "INDEPENDENT_BINDINGS": len(bindings),
                "INTERNAL_DESIGN_INVARIANTS": len(internal),
                "DEFERRED_RULES": len(deferred),
                "PACKAGE_INVARIANTS": len(package_ids),
                "GOVERNANCE_INVARIANTS": len(governance_ids),
                "PACKAGE_INVARIANTS_PASS": sum(produced[k]["status"] == "PASS" for k in package_ids),
                "GOVERNANCE_INVARIANTS_PASS": sum(produced[k]["status"] == "PASS"
                                                  for k in governance_ids),
            },
            "overall_pass": internal_ok and governance_ok and trust["status"] == "PASS",
        }


def external_from_args(args):
    if args.verification_input:
        if args.verification_input.lstrip().startswith("{"):
            return json.loads(args.verification_input)
        return load_json(args.verification_input)
    if args.expected_package_digest:
        return {"input_type": "EXTERNAL_VERIFICATION_INPUT",
                "package_id": args.expected_package_id,
                "package_version": args.expected_package_version,
                "package_digest": args.expected_package_digest,
                "trust_root": {"root_id": "cli", "root_kind": "PINNED_ACCEPTED_TRUST_ROOT"}}
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
        report = IndependentEvaluator(args.root, external_from_args(args)).run()
    except Exception as exc:
        report = {"certificate": "ACCORD-02E4R5R3_INDEPENDENT", "overall_pass": False,
                  "fatal": type(exc).__name__ + ": " + str(exc)}
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                     encoding="utf-8", newline="\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report.get("overall_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
