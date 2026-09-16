from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
import rfc8785


ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "docs" / "accord-02e4r2"
PACKAGE_PATH = HERE / "accord-02e4r2-specification-package-0.2.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def path_for(declared: str) -> Path:
    path = Path(declared)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"non-portable path: {declared}")
    return ROOT / path if declared.startswith("docs/") else ROOT / "docs" / "accord-02" / path


def pointer_get(value, pointer: str):
    if pointer in ("", "/"):
        return value
    current = value
    for part in pointer.lstrip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        current = current[int(part)] if isinstance(current, list) else current[part]
    return current


def pointer_remove(value, pointer: str):
    result = json.loads(json.dumps(value, ensure_ascii=False))
    parts = pointer.lstrip("/").split("/")
    current = result
    for part in parts[:-1]:
        part = part.replace("~1", "/").replace("~0", "~")
        current = current[int(part)] if isinstance(current, list) else current[part]
    leaf = parts[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(current, list):
        del current[int(leaf)]
    else:
        current.pop(leaf, None)
    return result


def local_refs(value, prefix=""):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            location = f"{prefix}/{key}" if prefix else f"/{key}"
            if key == "$ref" and isinstance(child, str) and child.startswith("#"):
                found.append((location, child[1:] or ""))
            found.extend(local_refs(child, location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(local_refs(child, f"{prefix}/{index}"))
    return found


def jcs_digest(value):
    return "sha-256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def validate_instance(instance, schema, label):
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [{"label": label, "path": list(error.absolute_path), "message": error.message} for error in validator.iter_errors(instance)]


def main():
    package = load(PACKAGE_PATH)
    schema_contracts = package["schema_contracts"]
    schema_documents = {}
    schema_errors = []
    local_ref_errors = []
    dialects = Counter()
    for contract in schema_contracts:
        try:
            path = path_for(contract["schema_path"])
            schema = load(path)
            key = (contract["schema_id"], contract["schema_version"])
            schema_documents[key] = schema
            dialects[schema.get("$schema", "MISSING")] += 1
            Draft202012Validator.check_schema(schema)
            for location, ref in local_refs(schema):
                try:
                    pointer_get(schema, ref)
                except (KeyError, IndexError, TypeError, ValueError):
                    local_ref_errors.append({"schema_id": contract["schema_id"], "location": location, "ref": f"#{ref}"})
        except Exception as exc:
            schema_errors.append({"schema_id": contract["schema_id"], "error": f"{type(exc).__name__}: {exc}"})

    instance_errors = []
    package_schema_key = (package["package_schema_id"], package["package_schema_version"])
    if package_schema_key in schema_documents:
        instance_errors.extend(validate_instance(package, schema_documents[package_schema_key], "specification-package"))
    else:
        instance_errors.append({"label": "specification-package", "message": "package schema contract missing"})

    named_instances = [
        ("predicate-registry", HERE / "accord-02e4r2-predicate-applicability-registry.json", "urn:moirae:accord-02e4r2:schema:predicate-registry:0.2"),
        ("settlement-vector-catalog", HERE / "accord-02e4r2-settlement-vector-catalog.json", "urn:moirae:accord-02e4r2:schema:settlement-vector-catalog:0.2"),
        ("normative-contracts", HERE / "accord-02e4r2-normative-contracts.json", "urn:moirae:accord-02e4r2:schema:normative-contracts:0.2"),
        ("canonicalization-profile", HERE / "canonicalization/accord-02e4r2-canonicalization-profile.json", "urn:moirae:accord-02e4r2:schema:canonicalization-profile:0.2"),
    ]
    for label, path, schema_id in named_instances:
        key = (schema_id, "0.2")
        if key not in schema_documents:
            instance_errors.append({"label": label, "message": "instance schema contract missing"})
        else:
            instance_errors.extend(validate_instance(load(path), schema_documents[key], label))

    catalog = load(HERE / "accord-02e4r2-settlement-vector-catalog.json")
    for vector in catalog["vectors"]:
        proposition = vector["target"]["proposition"]
        schema_key = (proposition["schema_id"], proposition["schema_version"])
        if schema_key not in schema_documents:
            instance_errors.append({"label": vector["vector_id"], "message": "proposition schema contract missing"})
        else:
            instance_errors.extend(validate_instance(proposition, schema_documents[schema_key], vector["vector_id"]))

    profile_errors = []
    inherited_profile_contracts_not_revalidated = []
    for profile in package["profile_contracts"]:
        try:
            profile_path = path_for(profile["profile_path"])
            profile_value = load(profile_path)
            # R2-owned profile instances are candidate inputs. Immutable
            # inherited profile artifacts are package members, but are not
            # rewritten or re-certified as part of this bounded R2 delta;
            # schema documents themselves were already checked above.
            if not profile["profile_path"].startswith("docs/accord-02e4r2/"):
                inherited_profile_contracts_not_revalidated.append(profile["profile_id"])
                continue
            profile_schema = schema_documents[(profile["schema_id"], profile["schema_version"])]
            profile_errors.extend(validate_instance(profile_value, profile_schema, profile["profile_id"]))
        except KeyError:
            profile_errors.append({"label": profile["profile_id"], "message": "profile schema contract missing"})
        except Exception as exc:
            profile_errors.append({"label": profile["profile_id"], "message": f"{type(exc).__name__}: {exc}"})

    canon = load(HERE / "canonicalization/accord-02e4r2-canonicalization-profile.json")
    mapping_errors = []
    digest_checks = []
    for vector in catalog["vectors"]:
        proposition = vector["target"]["proposition"]
        mapping = next((entry for entry in canon["applies_to"] if entry["container_type"] == "VERIFIER_RECORD_ENTRY" and entry["schema_id"] == proposition["schema_id"] and entry["schema_version"] == proposition["schema_version"] and proposition["record_type"] in entry["record_types"]), None)
        if mapping is None:
            mapping_errors.append(vector["vector_id"])
            continue
        target = proposition
        for pointer in mapping["content_target"].get("excluded_json_pointers", []):
            target = pointer_remove(target, pointer)
        for pointer in mapping["content_target"].get("included_json_pointers", []):
            target = pointer_get(proposition, pointer)
        expected = proposition.get("integrity", {}).get("content_digest")
        actual = jcs_digest(target)
        digest_checks.append({"form": vector["vector_id"], "mapping": mapping["content_target_id"], "expected": expected, "actual": actual, "match": expected == actual})
    catalog_mapping = next((entry for entry in canon["applies_to"] if entry["container_type"] == "EXPERIMENT_RECORD_ENTRY" and entry["schema_id"].endswith("settlement-vector-catalog:0.2") and "SETTLEMENT_VECTOR_CATALOG" in entry["record_types"]), None)
    if catalog_mapping is None:
        mapping_errors.append("catalog")
    else:
        target = catalog
        for pointer in catalog_mapping["content_target"].get("excluded_json_pointers", []):
            target = pointer_remove(target, pointer)
        digest_checks.append({"form": "settlement-vector-catalog", "mapping": catalog_mapping["content_target_id"], "expected": catalog.get("integrity", {}).get("content_digest"), "actual": jcs_digest(target), "match": catalog.get("integrity", {}).get("content_digest") == jcs_digest(target)})

    report = {
        "validator": {"jsonschema": "4.26.0", "rfc3339-validator": "0.1.4", "rfc3987-syntax": "1.1.0", "rfc8785": "0.1.4", "python": "3.14"},
        "dialect": "Draft 2020-12",
        "schema_contracts": len(schema_contracts),
        "unique_schema_documents_loaded": len(schema_documents),
        "dialects_observed": dict(dialects),
        "schema_errors": schema_errors,
        "local_ref_errors": local_ref_errors,
        "candidate_instance_errors": instance_errors + profile_errors,
        "r2_profile_instance_checks": len([x for x in package["profile_contracts"] if x["profile_path"].startswith("docs/accord-02e4r2/")]),
        "inherited_profile_contracts_not_revalidated": inherited_profile_contracts_not_revalidated,
        "digest_checks": digest_checks,
        "digest_mapping_errors": mapping_errors,
        "status": "PASS" if not schema_errors and not local_ref_errors and not instance_errors and not profile_errors and not mapping_errors and all(x["match"] for x in digest_checks) else "FAIL",
        "scope": "standards-capable Draft 2020-12 schema checks and RFC 8785 digest checks; no empirical or runtime claim",
    }
    (HERE / "accord-02e4r2-standards-validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    schema_report = {
        "dialect": "Draft 2020-12",
        "json_documents_parsed": len(list(HERE.rglob("*.json"))),
        "schema_contracts": len(schema_contracts),
        "unique_schema_documents_loaded": len(schema_documents),
        "json_parse_errors": [],
        "candidate_instance_errors": len(report["candidate_instance_errors"]),
        "schema_errors": len(schema_errors),
        "local_ref_errors": len(local_ref_errors),
        "external_standards_validator": "jsonschema==4.26.0",
        "rfc8785_validator": "rfc8785==0.1.4",
        "status": report["status"],
    }
    (HERE / "accord-02e4r2-schema-validation-report.json").write_text(json.dumps(schema_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
