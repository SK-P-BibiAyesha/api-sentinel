"""
API Comparison Engine (Member 1: API Comparison Engine)
======================================================
Project: API Sentinel — Automated Microservice API Drift Detector and
         Backward-Compatibility Breaking Change Linter

Purpose:
--------
This module compares two OpenAPI 3.x specifications (in YAML or JSON format)
and generates a structured, deterministic JSON report detailing all API differences.

Downstream Consumers:
- Member 2 (Breaking Change Linter & Risk Engine):
  Consumes the output `changes` list to detect backward-incompatibilities and assign risk levels.
- Member 3 (FastAPI Backend Integration):
  Imports `compare_specs`, `compare_openapi`, and `compare_files` to expose REST endpoints.
"""

from __future__ import annotations

import copy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_OPENAPI_PREFIXES = ("3.0", "3.1")
HTTP_METHODS = ["get", "post", "put", "patch", "delete", "options", "head", "trace"]


# ---------------------------------------------------------------------------
# Custom Exception
# ---------------------------------------------------------------------------

class OpenAPIValidationError(ValueError):
    """Raised when an OpenAPI document is invalid, malformed, or unsupported."""
    pass


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_openapi_dict(spec: Any, label: str = "Specification") -> List[str]:
    """
    Validates that a parsed OpenAPI object satisfies core structural constraints:
    - Must be a dictionary.
    - Must define a valid 'openapi' version string starting with 3.0 or 3.1.
    - Must define a 'paths' dictionary.

    Returns a list of error messages (empty if valid).
    """
    errors: List[str] = []

    if not isinstance(spec, dict):
        return [f"{label} must be a valid JSON/YAML object/dictionary."]

    if "openapi" not in spec:
        errors.append(f"{label} is missing required 'openapi' version field.")
    else:
        version = str(spec["openapi"]).strip()
        if not any(version.startswith(prefix) for prefix in SUPPORTED_OPENAPI_PREFIXES):
            errors.append(
                f"Unsupported OpenAPI version '{version}' in {label.lower()}. "
                f"Supported versions are OpenAPI 3.0.x and 3.1.x."
            )

    if "paths" not in spec:
        errors.append(f"{label} is missing required 'paths' object.")
    elif not isinstance(spec["paths"], dict):
        errors.append(f"'paths' field in {label.lower()} must be an object/dictionary.")

    return errors


# ---------------------------------------------------------------------------
# File Loading Helper
# ---------------------------------------------------------------------------

def load_spec_from_file(
    file_path: Union[str, Path],
    label: str = "Specification",
) -> Tuple[Optional[dict], List[str]]:
    """
    Safely reads and parses an OpenAPI file from disk.
    Supports both JSON and YAML.
    Returns: (parsed_dict, list_of_error_strings)
    """
    path_obj = Path(file_path)

    if not path_obj.exists():
        return None, [f"{label} file not found: '{file_path}'"]

    try:
        file_size = path_obj.stat().st_size
    except OSError as err:
        return None, [f"Could not access {label.lower()} file '{file_path}': {err}"]

    if file_size == 0:
        return None, [f"{label} file is empty: '{file_path}'"]

    ext = path_obj.suffix.lower()

    try:
        content = path_obj.read_text(encoding="utf-8")

        if not content.strip():
            return None, [f"{label} file is empty: '{file_path}'"]

        if ext == ".json":
            data = json.loads(content)
        elif ext in (".yaml", ".yml"):
            data = yaml.safe_load(content)
        else:
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                data = yaml.safe_load(content)

    except json.JSONDecodeError as json_err:
        return None, [f"Malformed JSON in {label.lower()} file '{file_path}': {json_err}"]
    except yaml.YAMLError as yaml_err:
        return None, [f"Malformed YAML in {label.lower()} file '{file_path}': {yaml_err}"]
    except Exception as err:
        return None, [f"Error reading {label.lower()} file '{file_path}': {err}"]

    val_errors = validate_openapi_dict(data, label=f"{label} ('{file_path}')")
    if val_errors:
        return None, val_errors

    return data, []


# ---------------------------------------------------------------------------
# Pointer and $ref Resolution
# ---------------------------------------------------------------------------

def resolve_pointer(root: dict, pointer: str) -> Any:
    """
    Resolve a local JSON Pointer string against the root dictionary.
    Example: '#/components/schemas/Product' -> root['components']['schemas']['Product']

    Handles RFC 6901 escaped characters:
      ~1 -> /
      ~0 -> ~
    """
    if not isinstance(pointer, str) or not pointer.startswith("#"):
        raise ValueError(f"Only local references starting with '#' are supported. Got: '{pointer}'")

    path_str = pointer[1:].lstrip("/")
    if not path_str:
        return root

    segments = path_str.split("/")
    current = root

    for raw_seg in segments:
        seg = raw_seg.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and seg in current:
            current = current[seg]
        elif isinstance(current, list) and seg.isdigit() and int(seg) < len(current):
            current = current[int(seg)]
        else:
            raise KeyError(f"Pointer segment '{seg}' in '{pointer}' does not exist.")

    return current


def resolve_ref_if_needed(
    root: dict,
    obj: Any,
    visited_refs: Optional[Set[str]] = None,
) -> Any:
    """
    If `obj` is a dictionary containing a '$ref' string, resolve it within `root`.
    
    Protects against infinite recursion in self-referencing and mutually recursive schemas.
    Identifies unsupported external references safely.
    """
    if not isinstance(obj, dict) or "$ref" not in obj:
        return obj

    ref = obj["$ref"]
    if not isinstance(ref, str):
        return obj

    # External references (URLs or external files)
    if ref.startswith("http://") or ref.startswith("https://") or not ref.startswith("#"):
        return {
            **obj,
            "_is_external_ref": True,
            "_error": f"External reference '{ref}' is unsupported; local references only.",
        }

    if visited_refs is None:
        visited_refs = set()

    # Detect recursive loops
    if ref in visited_refs:
        return {**obj, "_is_circular": True}

    try:
        resolved = resolve_pointer(root, ref)
    except (KeyError, ValueError, TypeError) as exc:
        return {
            **obj,
            "_is_unresolved_ref": True,
            "_error": f"Unresolved reference '{ref}': {exc}",
        }

    new_visited = visited_refs | {ref}

    if isinstance(resolved, dict):
        if "$ref" in resolved:
            return resolve_ref_if_needed(root, resolved, new_visited)

        # Merge any sibling fields from the reference object (allowed in OpenAPI 3.1)
        merged = dict(resolved)
        for key, val in obj.items():
            if key != "$ref" and key not in merged:
                merged[key] = val
        return merged

    return resolved


# ---------------------------------------------------------------------------
# Schema Helpers
# ---------------------------------------------------------------------------

def get_schema_type(schema: Any) -> str:
    """
    Extract a normalized data type string from an OpenAPI schema dictionary.
    Handles OpenAPI 3.0 (single string) and 3.1 (string or array of strings).
    Falls back to structural inference ('object' or 'array') if 'type' is missing.
    """
    if not isinstance(schema, dict):
        return "any"

    raw_type = schema.get("type")
    if raw_type is not None:
        if isinstance(raw_type, list):
            return ", ".join(sorted(str(t) for t in raw_type))
        return str(raw_type)

    if "properties" in schema:
        return "object"
    if "items" in schema:
        return "array"
    if "oneOf" in schema:
        return "oneOf"
    if "anyOf" in schema:
        return "anyOf"
    if "allOf" in schema:
        return "allOf"

    return "any"


def flatten_schema_properties(schema: dict, root: dict) -> Tuple[Dict[str, Any], Set[str]]:
    """
    Extract all properties and required fields from a schema, merging any 'allOf' components.
    Returns: (properties_dict, required_set)
    """
    resolved_schema = resolve_ref_if_needed(root, schema)
    if not isinstance(resolved_schema, dict):
        return {}, set()

    properties: Dict[str, Any] = {}
    required: Set[str] = set()

    # Composed schemas using allOf
    if "allOf" in resolved_schema and isinstance(resolved_schema["allOf"], list):
        for sub_schema in resolved_schema["allOf"]:
            sub_props, sub_req = flatten_schema_properties(sub_schema, root)
            properties.update(sub_props)
            required.update(sub_req)

    # Direct properties
    if "properties" in resolved_schema and isinstance(resolved_schema["properties"], dict):
        for prop_name, prop_def in resolved_schema["properties"].items():
            properties[prop_name] = prop_def

    # Direct required fields
    if "required" in resolved_schema and isinstance(resolved_schema["required"], list):
        for req_field in resolved_schema["required"]:
            if isinstance(req_field, str):
                required.add(req_field)

    return properties, required


# ---------------------------------------------------------------------------
# Normalized Change Record Builder
# ---------------------------------------------------------------------------

def make_change(
    type_name: str,
    path: str,
    method: Optional[str] = None,
    location: str = "endpoint",
    field: Optional[str] = None,
    old_type: Optional[str] = None,
    new_type: Optional[str] = None,
    old_value: Any = None,
    new_value: Any = None,
    description: str = "",
    action: Optional[str] = None,
    category: Optional[str] = None,
    change_type: Optional[str] = None,
) -> dict:
    """
    Creates a standardized, dual-contract change dictionary compatible with:
    - Member 1's structured contract ('type', 'endpoint', 'method', 'location', 'field', 'old_type', 'new_type')
    - Member 2's Linter and Risk Engine ('change_type', 'path', 'location', 'old_value', 'new_value')
    """
    norm_method = method.upper() if method else None

    # Determine canonical change_type for Member 2 if not explicitly provided
    resolved_change_type = change_type or type_name

    # Determine coarse action (added/removed/modified)
    if action is None:
        if "removed" in type_name:
            action = "removed"
        elif "added" in type_name:
            action = "added"
        else:
            action = "modified"

    return {
        "type": type_name,
        "change_type": resolved_change_type,
        "action": action,
        "category": category or location,
        "endpoint": path,
        "path": path,
        "method": norm_method,
        "location": location,
        "field": field,
        "old_type": old_type,
        "new_type": new_type,
        "old_value": old_value if old_value is not None else old_type,
        "new_value": new_value if new_value is not None else new_type,
        "description": description,
    }


# ---------------------------------------------------------------------------
# Deep Schema Comparison Engine
# ---------------------------------------------------------------------------

def compare_schemas(
    old_schema_raw: Any,
    new_schema_raw: Any,
    old_root: dict,
    new_root: dict,
    path: str,
    method: str,
    location: str,
    category: str,
    field_prefix: str = "",
    visited_pairs: Optional[Set[Tuple[str, str]]] = None,
) -> List[dict]:
    """
    Recursively compares two schemas (request body schemas or response schemas).
    Identifies:
    - Added properties
    - Removed properties
    - Modified property data types
    - Changed requiredness (optional -> required, required -> optional)
    - Array item type changes
    - Nested object differences
    - Enum constraint changes
    - Numeric/string validation constraint changes
    """
    changes: List[dict] = []
    is_response = "response" in category.lower()
    label = "Response" if is_response else "Request"
    field_cat = "response_field" if is_response else "request_field"

    if visited_pairs is None:
        visited_pairs = set()

    # Track refs to avoid circular recursion
    old_ref = old_schema_raw.get("$ref") if isinstance(old_schema_raw, dict) else None
    new_ref = new_schema_raw.get("$ref") if isinstance(new_schema_raw, dict) else None
    if old_ref and new_ref:
        pair = (old_ref, new_ref)
        if pair in visited_pairs:
            return changes
        visited_pairs.add(pair)

    old_schema = resolve_ref_if_needed(old_root, old_schema_raw)
    new_schema = resolve_ref_if_needed(new_root, new_schema_raw)

    if not isinstance(old_schema, dict) or not isinstance(new_schema, dict):
        return changes

    # Stop recursion if either is marked circular
    if old_schema.get("_is_circular") or new_schema.get("_is_circular"):
        return changes

    # Report unresolvable references
    if old_schema.get("_is_unresolved_ref") or new_schema.get("_is_unresolved_ref"):
        err = old_schema.get("_error") or new_schema.get("_error")
        changes.append(make_change(
            type_name="schema_reference_unresolved",
            change_type="description_changed",
            path=path,
            method=method,
            location=location,
            field=field_prefix or None,
            description=f"{label} schema contains unresolved reference: {err}",
            action="modified",
            category=field_cat,
        ))
        return changes

    old_type = get_schema_type(old_schema)
    new_type = get_schema_type(new_schema)

    # 1. Type change check on nested field
    if field_prefix and old_type != new_type and old_type != "any" and new_type != "any":
        type_name = "response_field_type_changed" if is_response else "request_field_type_changed"
        changes.append(make_change(
            type_name=type_name,
            change_type="field_type_changed",
            path=path,
            method=method,
            location=location,
            field=field_prefix,
            old_type=old_type,
            new_type=new_type,
            old_value=old_type,
            new_value=new_type,
            description=f"{label} field '{field_prefix}' type changed from '{old_type}' to '{new_type}'",
            action="modified",
            category=field_cat,
        ))
        return changes

    # 2. Enum constraints check
    old_enum = old_schema.get("enum")
    new_enum = new_schema.get("enum")
    if isinstance(old_enum, list) and isinstance(new_enum, list):
        old_set = set(str(x) for x in old_enum)
        new_set = set(str(x) for x in new_enum)
        if old_set != new_set:
            if not old_set.issubset(new_set):
                # Allowed values were restricted or eliminated
                changes.append(make_change(
                    type_name="enum_values_restricted",
                    change_type="enum_values_restricted",
                    path=path,
                    method=method,
                    location=location,
                    field=field_prefix or None,
                    old_value=sorted(old_enum, key=str),
                    new_value=sorted(new_enum, key=str),
                    description=f"{label} field '{field_prefix}' enum values were restricted",
                    action="modified",
                    category=field_cat,
                ))
            else:
                changes.append(make_change(
                    type_name="enum_values_expanded",
                    change_type="description_changed",
                    path=path,
                    method=method,
                    location=location,
                    field=field_prefix or None,
                    old_value=sorted(old_enum, key=str),
                    new_value=sorted(new_enum, key=str),
                    description=f"{label} field '{field_prefix}' enum values were expanded",
                    action="modified",
                    category=field_cat,
                ))

    # 3. Numeric & string validation constraint changes
    for constraint in ("minimum", "maximum", "pattern", "minLength", "maxLength", "minItems", "maxItems"):
        old_c = old_schema.get(constraint)
        new_c = new_schema.get(constraint)
        if old_c is not None and new_c is not None and old_c != new_c:
            changes.append(make_change(
                type_name="constraint_changed",
                change_type="description_changed",
                path=path,
                method=method,
                location=location,
                field=f"{field_prefix}.{constraint}" if field_prefix else constraint,
                old_value=old_c,
                new_value=new_c,
                description=f"{label} field '{field_prefix}' constraint '{constraint}' changed from '{old_c}' to '{new_c}'",
                action="modified",
                category=field_cat,
            ))

    # 4. Object properties comparison
    old_props, old_req = flatten_schema_properties(old_schema, old_root)
    new_props, new_req = flatten_schema_properties(new_schema, new_root)

    if old_props or new_props:
        all_props = sorted(set(old_props.keys()) | set(new_props.keys()))
        for prop in all_props:
            prop_field = f"{field_prefix}.{prop}" if field_prefix else prop

            # Property removed
            if prop in old_props and prop not in new_props:
                prop_schema = resolve_ref_if_needed(old_root, old_props[prop])
                prop_type = get_schema_type(prop_schema)
                type_name = "response_field_removed" if is_response else "request_field_removed"
                changes.append(make_change(
                    type_name=type_name,
                    change_type=type_name,
                    path=path,
                    method=method,
                    location=location,
                    field=prop_field,
                    old_type=prop_type,
                    new_type=None,
                    old_value=prop_type,
                    new_value=None,
                    description=f"{label} field '{prop_field}' was removed",
                    action="removed",
                    category=field_cat,
                ))

            # Property added
            elif prop not in old_props and prop in new_props:
                prop_schema = resolve_ref_if_needed(new_root, new_props[prop])
                prop_type = get_schema_type(prop_schema)
                is_req = prop in new_req
                type_name = "response_field_added" if is_response else "request_field_added"

                if is_req and not is_response:
                    desc = f"New required request property '{prop_field}' was added"
                elif is_req:
                    desc = f"New required {label.lower()} field '{prop_field}' was added"
                else:
                    desc = f"{label} field '{prop_field}' was added"

                changes.append(make_change(
                    type_name=type_name,
                    change_type=type_name,
                    path=path,
                    method=method,
                    location=location,
                    field=prop_field,
                    old_type=None,
                    new_type=prop_type,
                    old_value=None,
                    new_value=prop_type,
                    description=desc,
                    action="added",
                    category=field_cat,
                ))

            # Property in both: compare modifications
            else:
                old_is_req = prop in old_req
                new_is_req = prop in new_req

                if not old_is_req and new_is_req:
                    # Optional -> Required
                    type_name = "request_field_became_required" if not is_response else "response_field_became_required"
                    rule_change_type = "request_parameter_became_required" if not is_response else "response_field_became_required"
                    changes.append(make_change(
                        type_name=type_name,
                        change_type=rule_change_type,
                        path=path,
                        method=method,
                        location=location,
                        field=prop_field,
                        old_value=False,
                        new_value=True,
                        description=f"{label} field '{prop_field}' changed from optional to required",
                        action="modified",
                        category=field_cat,
                    ))
                elif old_is_req and not new_is_req:
                    # Required -> Optional
                    type_name = "request_field_became_optional" if not is_response else "response_field_became_optional"
                    changes.append(make_change(
                        type_name=type_name,
                        change_type=type_name,
                        path=path,
                        method=method,
                        location=location,
                        field=prop_field,
                        old_value=True,
                        new_value=False,
                        description=f"{label} field '{prop_field}' changed from required to optional",
                        action="modified",
                        category=field_cat,
                    ))

                # Deeply compare property schemas
                nested_changes = compare_schemas(
                    old_schema_raw=old_props[prop],
                    new_schema_raw=new_props[prop],
                    old_root=old_root,
                    new_root=new_root,
                    path=path,
                    method=method,
                    location=location,
                    category=category,
                    field_prefix=prop_field,
                    visited_pairs=visited_pairs,
                )
                changes.extend(nested_changes)

    # 5. Array items comparison
    old_items = old_schema.get("items")
    new_items = new_schema.get("items")
    if old_items is not None and new_items is not None:
        items_prefix = f"{field_prefix}[]" if field_prefix else "items[]"
        old_item_resolved = resolve_ref_if_needed(old_root, old_items)
        new_item_resolved = resolve_ref_if_needed(new_root, new_items)

        old_it_type = get_schema_type(old_item_resolved)
        new_it_type = get_schema_type(new_item_resolved)

        if old_it_type != new_it_type and old_it_type != "any" and new_it_type != "any":
            type_name = "response_field_type_changed" if is_response else "request_field_type_changed"
            changes.append(make_change(
                type_name=type_name,
                change_type="field_type_changed",
                path=path,
                method=method,
                location=location,
                field=items_prefix,
                old_type=old_it_type,
                new_type=new_it_type,
                old_value=old_it_type,
                new_value=new_it_type,
                description=f"{label} array item '{items_prefix}' type changed from '{old_it_type}' to '{new_it_type}'",
                action="modified",
                category=field_cat,
            ))
        else:
            # Recurse into item schemas (for arrays of objects)
            item_changes = compare_schemas(
                old_schema_raw=old_items,
                new_schema_raw=new_items,
                old_root=old_root,
                new_root=new_root,
                path=path,
                method=method,
                location=location,
                category=category,
                field_prefix=items_prefix,
                visited_pairs=visited_pairs,
            )
            changes.extend(item_changes)

    return changes


# ---------------------------------------------------------------------------
# Parameters Extraction & Comparison
# ---------------------------------------------------------------------------

def get_effective_parameters(path_item: dict, operation: dict, root: dict) -> Dict[str, dict]:
    """
    Extract all parameters applicable to an operation, combining path-level and operation-level parameters.
    Per OpenAPI spec, operation-level parameters override path-level parameters with the same (name, in).
    Returns a dict keyed by 'param_name:location' (e.g. 'limit:query').
    """
    params_map: Dict[str, dict] = {}

    # 1. Path-level parameters
    raw_path_params = path_item.get("parameters", [])
    if isinstance(raw_path_params, list):
        for p in raw_path_params:
            resolved = resolve_ref_if_needed(root, p)
            if isinstance(resolved, dict) and "name" in resolved and "in" in resolved:
                key = f"{resolved['name']}:{resolved['in']}"
                params_map[key] = resolved

    # 2. Operation-level parameters (overrides path-level)
    raw_op_params = operation.get("parameters", [])
    if isinstance(raw_op_params, list):
        for p in raw_op_params:
            resolved = resolve_ref_if_needed(root, p)
            if isinstance(resolved, dict) and "name" in resolved and "in" in resolved:
                key = f"{resolved['name']}:{resolved['in']}"
                params_map[key] = resolved

    return params_map


def compare_parameters(
    old_path_item: dict,
    new_path_item: dict,
    old_op: dict,
    new_op: dict,
    old_root: dict,
    new_root: dict,
    path: str,
    method: str,
) -> List[dict]:
    """
    Compares path, query, header, and cookie parameters for an operation.
    Identifies:
    - Added parameters (required or optional)
    - Removed parameters
    - Changed requiredness
    - Changed parameter data type
    - Changed parameter location
    - Changed enum / constraints
    """
    changes: List[dict] = []

    old_params = get_effective_parameters(old_path_item, old_op, old_root)
    new_params = get_effective_parameters(new_path_item, new_op, new_root)

    # Detect location changes: same parameter name, different location
    old_by_name = {p["name"]: p for p in old_params.values()}
    new_by_name = {p["name"]: p for p in new_params.values()}

    handled_old_keys: Set[str] = set()
    handled_new_keys: Set[str] = set()

    for name, old_p in sorted(old_by_name.items()):
        if name in new_by_name:
            new_p = new_by_name[name]
            old_loc = old_p.get("in")
            new_loc = new_p.get("in")
            if old_loc != new_loc:
                changes.append(make_change(
                    type_name="parameter_location_changed",
                    change_type="request_parameter_became_required" if new_loc == "path" else "parameter_location_changed",
                    path=path,
                    method=method,
                    location="parameter",
                    field=name,
                    old_value=old_loc,
                    new_value=new_loc,
                    description=f"Parameter '{name}' location changed from '{old_loc}' to '{new_loc}' in '{method} {path}'",
                    action="modified",
                    category="parameter",
                ))
                handled_old_keys.add(f"{name}:{old_loc}")
                handled_new_keys.add(f"{name}:{new_loc}")

    all_keys = sorted(set(old_params.keys()) | set(new_params.keys()))

    for key in all_keys:
        if key in handled_old_keys or key in handled_new_keys:
            continue

        # Parameter removed
        if key in old_params and key not in new_params:
            p = old_params[key]
            p_name = p.get("name", "unknown")
            p_in = p.get("in", "query")
            schema = resolve_ref_if_needed(old_root, p.get("schema", {}))
            p_type = get_schema_type(schema)

            changes.append(make_change(
                type_name="parameter_removed",
                change_type="parameter_removed",
                path=path,
                method=method,
                location=p_in,
                field=p_name,
                old_type=p_type,
                new_type=None,
                old_value=p_type,
                new_value=None,
                description=f"Parameter '{p_name}' ({p_in}) was removed from '{method} {path}'",
                action="removed",
                category="parameter",
            ))

        # Parameter added
        elif key not in old_params and key in new_params:
            p = new_params[key]
            p_name = p.get("name", "unknown")
            p_in = p.get("in", "query")
            is_req = bool(p.get("required", p_in == "path"))
            schema = resolve_ref_if_needed(new_root, p.get("schema", {}))
            p_type = get_schema_type(schema)

            desc = (
                f"New required parameter '{p_name}' ({p_in}) was added to '{method} {path}'"
                if is_req
                else f"New optional parameter '{p_name}' ({p_in}) was added to '{method} {path}'"
            )

            changes.append(make_change(
                type_name="parameter_added",
                change_type="request_parameter_became_required" if is_req else "parameter_added",
                path=path,
                method=method,
                location=p_in,
                field=p_name,
                old_type=None,
                new_type=p_type,
                old_value=None,
                new_value=p_type,
                description=desc,
                action="added",
                category="parameter",
            ))

        # Parameter in both: check requiredness and schema
        else:
            old_p = old_params[key]
            new_p = new_params[key]
            p_name = old_p.get("name", "unknown")
            p_in = old_p.get("in", "query")

            old_req = bool(old_p.get("required", p_in == "path"))
            new_req = bool(new_p.get("required", p_in == "path"))

            if not old_req and new_req:
                changes.append(make_change(
                    type_name="request_parameter_became_required",
                    change_type="request_parameter_became_required",
                    path=path,
                    method=method,
                    location=p_in,
                    field=p_name,
                    old_value=False,
                    new_value=True,
                    description=f"Parameter '{p_name}' ({p_in}) changed from optional to required in '{method} {path}'",
                    action="modified",
                    category="parameter",
                ))
            elif old_req and not new_req:
                changes.append(make_change(
                    type_name="parameter_became_optional",
                    change_type="parameter_became_optional",
                    path=path,
                    method=method,
                    location=p_in,
                    field=p_name,
                    old_value=True,
                    new_value=False,
                    description=f"Parameter '{p_name}' ({p_in}) changed from required to optional in '{method} {path}'",
                    action="modified",
                    category="parameter",
                ))

            # Check schema type
            old_schema = resolve_ref_if_needed(old_root, old_p.get("schema", {}))
            new_schema = resolve_ref_if_needed(new_root, new_p.get("schema", {}))
            old_type = get_schema_type(old_schema)
            new_type = get_schema_type(new_schema)

            if old_type != new_type and old_type != "any" and new_type != "any":
                changes.append(make_change(
                    type_name="parameter_type_changed",
                    change_type="field_type_changed",
                    path=path,
                    method=method,
                    location=p_in,
                    field=p_name,
                    old_type=old_type,
                    new_type=new_type,
                    old_value=old_type,
                    new_value=new_type,
                    description=f"Parameter '{p_name}' ({p_in}) type changed from '{old_type}' to '{new_type}' in '{method} {path}'",
                    action="modified",
                    category="parameter",
                ))

            # Check enum constraints on parameter schema
            if isinstance(old_schema, dict) and isinstance(new_schema, dict):
                old_enum = old_schema.get("enum")
                new_enum = new_schema.get("enum")
                if isinstance(old_enum, list) and isinstance(new_enum, list):
                    old_set = set(str(x) for x in old_enum)
                    new_set = set(str(x) for x in new_enum)
                    if old_set != new_set and not old_set.issubset(new_set):
                        changes.append(make_change(
                            type_name="enum_values_restricted",
                            change_type="enum_values_restricted",
                            path=path,
                            method=method,
                            location=p_in,
                            field=p_name,
                            old_value=sorted(old_enum, key=str),
                            new_value=sorted(new_enum, key=str),
                            description=f"Parameter '{p_name}' ({p_in}) enum values were restricted in '{method} {path}'",
                            action="modified",
                            category="parameter",
                        ))

            # Check validation constraints on parameter schema
            if isinstance(old_schema, dict) and isinstance(new_schema, dict):
                for constraint in ("minimum", "maximum", "pattern", "minLength", "maxLength"):
                    old_c = old_schema.get(constraint)
                    new_c = new_schema.get(constraint)
                    if old_c is not None and new_c is not None and old_c != new_c:
                        changes.append(make_change(
                            type_name="constraint_changed",
                            change_type="description_changed",
                            path=path,
                            method=method,
                            location=p_in,
                            field=f"{p_name}.{constraint}",
                            old_value=old_c,
                            new_value=new_c,
                            description=f"Parameter '{p_name}' ({p_in}) constraint '{constraint}' changed from '{old_c}' to '{new_c}' in '{method} {path}'",
                            action="modified",
                            category="parameter",
                        ))

    return changes


# ---------------------------------------------------------------------------
# Request Body Comparison
# ---------------------------------------------------------------------------

def compare_request_bodies(
    old_op: dict,
    new_op: dict,
    old_root: dict,
    new_root: dict,
    path: str,
    method: str,
) -> List[dict]:
    """
    Compares requestBody specifications between two operations.
    Identifies:
    - Request body added / removed
    - Requiredness changes
    - Content types added / removed
    - Schema property additions, removals, and modifications
    """
    changes: List[dict] = []

    old_body_raw = old_op.get("requestBody")
    new_body_raw = new_op.get("requestBody")

    old_body = resolve_ref_if_needed(old_root, old_body_raw) if old_body_raw else None
    new_body = resolve_ref_if_needed(new_root, new_body_raw) if new_body_raw else None

    # Request body removed
    if old_body and not new_body:
        changes.append(make_change(
            type_name="request_body_removed",
            change_type="request_body_removed",
            path=path,
            method=method,
            location="request_body",
            field=None,
            old_value="requestBody",
            new_value=None,
            description=f"Request body was removed from '{method} {path}'",
            action="removed",
            category="request_body",
        ))
        return changes

    # Request body added
    if not old_body and new_body:
        is_req = bool(new_body.get("required", False))
        changes.append(make_change(
            type_name="request_body_added",
            change_type="request_parameter_became_required" if is_req else "request_body_added",
            path=path,
            method=method,
            location="request_body",
            field=None,
            old_value=None,
            new_value="requestBody",
            description=f"Request body was added to '{method} {path}'{' (required)' if is_req else ''}",
            action="added",
            category="request_body",
        ))
        return changes

    if not old_body or not new_body:
        return changes

    # Both have request body: check requiredness
    old_req = bool(old_body.get("required", False))
    new_req = bool(new_body.get("required", False))

    if not old_req and new_req:
        changes.append(make_change(
            type_name="request_body_changed",
            change_type="request_parameter_became_required",
            path=path,
            method=method,
            location="request_body",
            field="required",
            old_value=False,
            new_value=True,
            description=f"Request body for '{method} {path}' changed from optional to required",
            action="modified",
            category="request_body",
        ))
    elif old_req and not new_req:
        changes.append(make_change(
            type_name="request_body_changed",
            change_type="request_body_changed",
            path=path,
            method=method,
            location="request_body",
            field="required",
            old_value=True,
            new_value=False,
            description=f"Request body for '{method} {path}' changed from required to optional",
            action="modified",
            category="request_body",
        ))

    # Compare content media types
    old_content = old_body.get("content", {}) if isinstance(old_body.get("content"), dict) else {}
    new_content = new_body.get("content", {}) if isinstance(new_body.get("content"), dict) else {}

    all_media = sorted(set(old_content.keys()) | set(new_content.keys()))

    for media in all_media:
        if media in old_content and media not in new_content:
            changes.append(make_change(
                type_name="request_body_content_type_removed",
                change_type="request_body_changed",
                path=path,
                method=method,
                location="request_body",
                field=media,
                old_value=media,
                new_value=None,
                description=f"Request body content type '{media}' was removed from '{method} {path}'",
                action="removed",
                category="request_body",
            ))
        elif media not in old_content and media in new_content:
            changes.append(make_change(
                type_name="request_body_content_type_added",
                change_type="request_body_changed",
                path=path,
                method=method,
                location="request_body",
                field=media,
                old_value=None,
                new_value=media,
                description=f"Request body content type '{media}' was added to '{method} {path}'",
                action="added",
                category="request_body",
            ))
        else:
            old_media_obj = old_content[media]
            new_media_obj = new_content[media]
            old_schema = old_media_obj.get("schema", {}) if isinstance(old_media_obj, dict) else {}
            new_schema = new_media_obj.get("schema", {}) if isinstance(new_media_obj, dict) else {}

            schema_changes = compare_schemas(
                old_schema_raw=old_schema,
                new_schema_raw=new_schema,
                old_root=old_root,
                new_root=new_root,
                path=path,
                method=method,
                location="request_body",
                category="request_field",
            )
            changes.extend(schema_changes)

    return changes


# ---------------------------------------------------------------------------
# Responses Comparison
# ---------------------------------------------------------------------------

def compare_responses(
    old_op: dict,
    new_op: dict,
    old_root: dict,
    new_root: dict,
    path: str,
    method: str,
) -> List[dict]:
    """
    Compares response specifications between two operations.
    Identifies:
    - Added / removed HTTP status codes
    - Added / removed response content types
    - Response schema property additions, removals, and modifications
    """
    changes: List[dict] = []

    old_responses = old_op.get("responses", {}) if isinstance(old_op.get("responses"), dict) else {}
    new_responses = new_op.get("responses", {}) if isinstance(new_op.get("responses"), dict) else {}

    all_statuses = sorted(set(str(k) for k in old_responses.keys()) | set(str(k) for k in new_responses.keys()))

    for status_code in all_statuses:
        # Status code removed
        if status_code in old_responses and status_code not in new_responses:
            changes.append(make_change(
                type_name="response_status_removed",
                change_type="response_status_removed",
                path=path,
                method=method,
                location="response",
                field=status_code,
                old_value=status_code,
                new_value=None,
                description=f"Response status code '{status_code}' was removed from '{method} {path}'",
                action="removed",
                category="response",
            ))

        # Status code added
        elif status_code not in old_responses and status_code in new_responses:
            changes.append(make_change(
                type_name="response_status_added",
                change_type="response_status_added",
                path=path,
                method=method,
                location="response",
                field=status_code,
                old_value=None,
                new_value=status_code,
                description=f"Response status code '{status_code}' was added to '{method} {path}'",
                action="added",
                category="response",
            ))

        # Status code in both: compare content and schema
        else:
            old_resp = resolve_ref_if_needed(old_root, old_responses[status_code])
            new_resp = resolve_ref_if_needed(new_root, new_responses[status_code])

            if not isinstance(old_resp, dict) or not isinstance(new_resp, dict):
                continue

            old_content = old_resp.get("content", {}) if isinstance(old_resp.get("content"), dict) else {}
            new_content = new_resp.get("content", {}) if isinstance(new_resp.get("content"), dict) else {}

            all_media = sorted(set(old_content.keys()) | set(new_content.keys()))

            for media in all_media:
                if media in old_content and media not in new_content:
                    changes.append(make_change(
                        type_name="response_content_type_removed",
                        change_type="response_content_type_removed",
                        path=path,
                        method=method,
                        location="response",
                        field=media,
                        old_value=media,
                        new_value=None,
                        description=f"Response content type '{media}' for status '{status_code}' was removed from '{method} {path}'",
                        action="removed",
                        category="response",
                    ))
                elif media not in old_content and media in new_content:
                    changes.append(make_change(
                        type_name="response_content_type_added",
                        change_type="response_content_type_added",
                        path=path,
                        method=method,
                        location="response",
                        field=media,
                        old_value=None,
                        new_value=media,
                        description=f"Response content type '{media}' for status '{status_code}' was added to '{method} {path}'",
                        action="added",
                        category="response",
                    ))
                else:
                    old_media_obj = old_content[media]
                    new_media_obj = new_content[media]
                    old_schema = old_media_obj.get("schema", {}) if isinstance(old_media_obj, dict) else {}
                    new_schema = new_media_obj.get("schema", {}) if isinstance(new_media_obj, dict) else {}

                    schema_changes = compare_schemas(
                        old_schema_raw=old_schema,
                        new_schema_raw=new_schema,
                        old_root=old_root,
                        new_root=new_root,
                        path=path,
                        method=method,
                        location="response",
                        category="response_field",
                    )
                    changes.extend(schema_changes)

    return changes


# ---------------------------------------------------------------------------
# Core Comparison Public APIs
# ---------------------------------------------------------------------------

def compare_specs(
    old_spec: dict,
    new_spec: dict,
    raise_on_error: bool = False,
) -> dict:
    """
    Compare two OpenAPI specification dictionaries and return structured differences.

    :param old_spec: Original OpenAPI specification as a Python dictionary.
    :param new_spec: Updated OpenAPI specification as a Python dictionary.
    :param raise_on_error: If True, raises OpenAPIValidationError on invalid input.
    :return: A dictionary conforming to the comparison engine contract:
             {
               "success": bool,
               "summary": {
                 "total_changes": int,
                 "endpoints_added": int,
                 "endpoints_removed": int,
                 "methods_added": int,
                 "methods_removed": int,
                 "parameters_added": int,
                 "parameters_removed": int,
                 "fields_added": int,
                 "fields_removed": int,
                 "added": int,
                 "removed": int,
                 "modified": int
               },
               "changes": [ ... ],
               "errors": [ ... ]
             }
    """
    errors: List[str] = []
    errors.extend(validate_openapi_dict(old_spec, label="Old specification"))
    errors.extend(validate_openapi_dict(new_spec, label="New specification"))

    if errors:
        if raise_on_error:
            raise OpenAPIValidationError("\n".join(errors))

        return {
            "success": False,
            "summary": {
                "total_changes": 0,
                "endpoints_added": 0,
                "endpoints_removed": 0,
                "methods_added": 0,
                "methods_removed": 0,
                "parameters_added": 0,
                "parameters_removed": 0,
                "fields_added": 0,
                "fields_removed": 0,
                "added": 0,
                "removed": 0,
                "modified": 0,
            },
            "changes": [],
            "errors": errors,
        }

    changes: List[dict] = []

    old_paths: Dict[str, Any] = old_spec.get("paths", {})
    new_paths: Dict[str, Any] = new_spec.get("paths", {})

    all_path_keys = sorted(set(old_paths.keys()) | set(new_paths.keys()))

    for path in all_path_keys:
        # Endpoint removed
        if path in old_paths and path not in new_paths:
            changes.append(make_change(
                type_name="endpoint_removed",
                change_type="endpoint_removed",
                path=path,
                method=None,
                location="endpoint",
                field=None,
                old_value=path,
                new_value=None,
                description=f"Endpoint '{path}' was removed",
                action="removed",
                category="endpoint",
            ))
            continue

        # Endpoint added
        if path not in old_paths and path in new_paths:
            changes.append(make_change(
                type_name="endpoint_added",
                change_type="endpoint_added",
                path=path,
                method=None,
                location="endpoint",
                field=None,
                old_value=None,
                new_value=path,
                description=f"Endpoint '{path}' was added",
                action="added",
                category="endpoint",
            ))
            continue

        # Endpoint present in both: compare HTTP methods
        old_path_item = old_paths[path]
        new_path_item = new_paths[path]

        if not isinstance(old_path_item, dict) or not isinstance(new_path_item, dict):
            continue

        old_methods = {m.lower(): m for m in old_path_item.keys() if m.lower() in HTTP_METHODS}
        new_methods = {m.lower(): m for m in new_path_item.keys() if m.lower() in HTTP_METHODS}

        all_methods = sorted(set(old_methods.keys()) | set(new_methods.keys()))

        for method_key in all_methods:
            method_upper = method_key.upper()

            # Method removed
            if method_key in old_methods and method_key not in new_methods:
                changes.append(make_change(
                    type_name="method_removed",
                    change_type="http_method_removed",
                    path=path,
                    method=method_upper,
                    location="method",
                    field=None,
                    old_value=method_upper,
                    new_value=None,
                    description=f"HTTP method '{method_upper}' was removed from endpoint '{path}'",
                    action="removed",
                    category="http_method",
                ))
                continue

            # Method added
            if method_key not in old_methods and method_key in new_methods:
                changes.append(make_change(
                    type_name="method_added",
                    change_type="method_added",
                    path=path,
                    method=method_upper,
                    location="method",
                    field=None,
                    old_value=None,
                    new_value=method_upper,
                    description=f"HTTP method '{method_upper}' was added to endpoint '{path}'",
                    action="added",
                    category="http_method",
                ))
                continue

            # Method present in both: compare details
            old_op = old_path_item[old_methods[method_key]]
            new_op = new_path_item[new_methods[method_key]]

            if not isinstance(old_op, dict) or not isinstance(new_op, dict):
                continue

            # Check operation description change
            old_desc = (old_op.get("description") or old_op.get("summary") or "").strip()
            new_desc = (new_op.get("description") or new_op.get("summary") or "").strip()
            if old_desc and new_desc and old_desc != new_desc:
                changes.append(make_change(
                    type_name="description_changed",
                    change_type="description_changed",
                    path=path,
                    method=method_upper,
                    location="method",
                    field="description",
                    old_value=old_desc,
                    new_value=new_desc,
                    description=f"Description for '{method_upper} {path}' was updated",
                    action="modified",
                    category="http_method",
                ))

            # 1. Compare parameters (path, query, header, cookie)
            param_changes = compare_parameters(
                old_path_item=old_path_item,
                new_path_item=new_path_item,
                old_op=old_op,
                new_op=new_op,
                old_root=old_spec,
                new_root=new_spec,
                path=path,
                method=method_upper,
            )
            changes.extend(param_changes)

            # 2. Compare request body
            req_changes = compare_request_bodies(
                old_op=old_op,
                new_op=new_op,
                old_root=old_spec,
                new_root=new_spec,
                path=path,
                method=method_upper,
            )
            changes.extend(req_changes)

            # 3. Compare responses
            resp_changes = compare_responses(
                old_op=old_op,
                new_op=new_op,
                old_root=old_spec,
                new_root=new_spec,
                path=path,
                method=method_upper,
            )
            changes.extend(resp_changes)

    # Sort changes deterministically
    def sort_key(c: dict) -> Tuple[str, str, str, str, str]:
        return (
            c.get("path") or "",
            c.get("method") or "",
            c.get("location") or "",
            c.get("field") or "",
            c.get("type") or "",
        )

    changes.sort(key=sort_key)

    # Calculate summary counts deterministically
    endpoints_added = sum(1 for c in changes if c.get("type") == "endpoint_added")
    endpoints_removed = sum(1 for c in changes if c.get("type") == "endpoint_removed")
    methods_added = sum(1 for c in changes if c.get("type") == "method_added")
    methods_removed = sum(1 for c in changes if c.get("type") == "method_removed")
    params_added = sum(1 for c in changes if c.get("type") == "parameter_added")
    params_removed = sum(1 for c in changes if c.get("type") == "parameter_removed")
    fields_added = sum(1 for c in changes if c.get("type") in ("response_field_added", "request_field_added"))
    fields_removed = sum(1 for c in changes if c.get("type") in ("response_field_removed", "request_field_removed"))

    added_count = sum(1 for c in changes if c.get("action") == "added")
    removed_count = sum(1 for c in changes if c.get("action") == "removed")
    modified_count = sum(1 for c in changes if c.get("action") == "modified")

    return {
        "success": True,
        "summary": {
            "total_changes": len(changes),
            "endpoints_added": endpoints_added,
            "endpoints_removed": endpoints_removed,
            "methods_added": methods_added,
            "methods_removed": methods_removed,
            "parameters_added": params_added,
            "parameters_removed": params_removed,
            "fields_added": fields_added,
            "fields_removed": fields_removed,
            "added": added_count,
            "removed": removed_count,
            "modified": modified_count,
        },
        "changes": changes,
        "errors": [],
    }


# Convenient alias matching existing prototype nomenclature
compare_openapi = compare_specs


def compare_files(
    old_file: Union[str, Path],
    new_file: Union[str, Path],
    raise_on_error: bool = False,
) -> dict:
    """
    Compare two OpenAPI specification files (JSON or YAML) and return structured differences.

    :param old_file: Filepath to the original OpenAPI specification (.yaml, .yml, .json).
    :param new_file: Filepath to the updated OpenAPI specification (.yaml, .yml, .json).
    :param raise_on_error: If True, raises OpenAPIValidationError on invalid/missing files.
    :return: A dictionary conforming to the comparison engine contract.
    """
    old_spec, old_errors = load_spec_from_file(old_file, label="Old specification")
    new_spec, new_errors = load_spec_from_file(new_file, label="New specification")

    errors = old_errors + new_errors
    if errors:
        if raise_on_error:
            raise OpenAPIValidationError("\n".join(errors))

        return {
            "success": False,
            "summary": {
                "total_changes": 0,
                "endpoints_added": 0,
                "endpoints_removed": 0,
                "methods_added": 0,
                "methods_removed": 0,
                "parameters_added": 0,
                "parameters_removed": 0,
                "fields_added": 0,
                "fields_removed": 0,
                "added": 0,
                "removed": 0,
                "modified": 0,
            },
            "changes": [],
            "errors": errors,
        }

    return compare_specs(old_spec, new_spec, raise_on_error=raise_on_error)


# ---------------------------------------------------------------------------
# Compatibility Adapter for Legacy Callers
# ---------------------------------------------------------------------------

def compare_apis(old_api: dict, new_api: dict) -> List[dict]:
    """
    Compatibility adapter that converts compare_specs output into the legacy
    'findings' list expected by existing prototype callers in main.py and backend/api.py.

    Each finding contains:
    - severity: 'BREAKING', 'WARNING', or 'INFO'
    - change: Human-readable change title
    - location: Endpoint and method string
    - details: Contextual explanation
    """
    diff_report = compare_specs(old_api, new_api, raise_on_error=False)
    findings: List[dict] = []

    # Map change types to legacy findings
    for c in diff_report.get("changes", []):
        c_type = c.get("type", "")
        method = c.get("method")
        path = c.get("path") or c.get("endpoint") or ""
        loc_str = f"{method} {path}".strip() if method else path

        # Determine severity for legacy consumers
        if c_type in (
            "endpoint_removed",
            "method_removed",
            "response_field_removed",
            "response_status_removed",
            "request_parameter_became_required",
            "request_field_became_required",
            "response_field_type_changed",
            "parameter_type_changed",
            "request_field_type_changed",
            "enum_values_restricted",
        ):
            sev = "BREAKING"
        elif c_type in ("parameter_removed", "request_body_removed"):
            sev = "BREAKING"
        elif c_type in ("parameter_became_optional", "enum_values_expanded", "constraint_changed"):
            sev = "WARNING"
        else:
            sev = "INFO"

        # Format title
        title = c.get("description") or c_type.replace("_", " ").capitalize()

        findings.append({
            "severity": sev,
            "change": title,
            "location": loc_str,
            "details": c.get("description", ""),
            "change_type": c.get("change_type"),
            "type": c_type,
            "field": c.get("field"),
            "old_value": c.get("old_value"),
            "new_value": c.get("new_value"),
        })

    return findings


# ---------------------------------------------------------------------------
# Command-Line Interface (CLI)
# ---------------------------------------------------------------------------

def main() -> int:
    """
    CLI entrypoint:
    Usage: python comparator.py <old_spec_file> <new_spec_file>
    """
    if len(sys.argv) != 3:
        print("Usage: python comparator.py <old_api_file> <new_api_file>", file=sys.stderr)
        return 1

    old_file_path = sys.argv[1]
    new_file_path = sys.argv[2]

    report = compare_files(old_file_path, new_file_path)
    print(json.dumps(report, indent=2))

    if not report.get("success", False):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
