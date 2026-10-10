"""
Unit & Integration Tests for API Comparison Engine (Member 1)
=============================================================
Project: API Sentinel — Automated Microservice API Drift Detector and
         Backward-Compatibility Breaking Change Linter

Requirements Covered:
  1. Identical specifications produce no changes.
  2. Endpoint addition and removal.
  3. HTTP method addition and removal.
  4. Request parameter addition, removal, and type changes.
  5. Optional-to-required parameter changes.
  6. Request body and nested field changes.
  7. Response field addition and removal.
  8. Response field type changes.
  9. Response status code removal.
 10. Required-property changes.
 11. Enum and constraint changes.
 12. Arrays and nested objects.
 13. Local $ref resolution.
 14. Circular and unresolved references.
 15. Invalid YAML/JSON and malformed OpenAPI documents.
 16. Deterministic output.
 17. Compatibility with the existing backend and Member 2's expected input.
 Extra: File-based comparison, path parameter inheritance, CLI execution, legacy findings adapter.
"""

import copy
import json
import os
import subprocess
import sys
import tempfile
import pytest

from backend.comparator import (
    OpenAPIValidationError,
    compare_apis,
    compare_files,
    compare_openapi,
    compare_specs,
    load_spec_from_file,
    resolve_pointer,
    resolve_ref_if_needed,
    validate_openapi_dict,
)
from backend.linter import analyze_changes
from backend.compatibility_rules import evaluate_compatibility_rule
from backend.risk_engine import classify_risk


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_spec():
    """Returns a minimal valid OpenAPI 3.0.3 specification template."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "API Sentinel Test Service",
            "version": "1.0.0"
        },
        "paths": {}
    }


# ---------------------------------------------------------------------------
# 1. Identical specifications produce no changes
# ---------------------------------------------------------------------------

def test_identical_specifications_produce_no_changes(base_spec):
    """Verify that comparing identical specs results in zero changes."""
    spec_a = copy.deepcopy(base_spec)
    spec_a["paths"] = {
        "/users": {
            "get": {
                "responses": {
                    "200": {
                        "description": "User list",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    spec_b = copy.deepcopy(spec_a)

    result = compare_specs(spec_a, spec_b)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 0
    assert result["summary"]["added"] == 0
    assert result["summary"]["removed"] == 0
    assert result["summary"]["modified"] == 0
    assert result["changes"] == []
    assert result["errors"] == []


# ---------------------------------------------------------------------------
# 2. Endpoint addition and removal
# ---------------------------------------------------------------------------

def test_endpoint_removal(base_spec):
    """Verify detection of removed endpoints."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/users": {
            "get": {"responses": {"200": {"description": "OK"}}}
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {}

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 1
    assert result["summary"]["endpoints_removed"] == 1
    assert result["summary"]["removed"] == 1

    change = result["changes"][0]
    assert change["type"] == "endpoint_removed"
    assert change["change_type"] == "endpoint_removed"
    assert change["endpoint"] == "/users"
    assert change["path"] == "/users"
    assert change["location"] == "endpoint"
    assert change["old_value"] == "/users"
    assert change["new_value"] is None


def test_endpoint_addition(base_spec):
    """Verify detection of added endpoints."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {}
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/orders": {
            "post": {"responses": {"201": {"description": "Created"}}}
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 1
    assert result["summary"]["endpoints_added"] == 1
    assert result["summary"]["added"] == 1

    change = result["changes"][0]
    assert change["type"] == "endpoint_added"
    assert change["change_type"] == "endpoint_added"
    assert change["endpoint"] == "/orders"
    assert change["path"] == "/orders"
    assert change["location"] == "endpoint"
    assert change["new_value"] == "/orders"


# ---------------------------------------------------------------------------
# 3. HTTP method addition and removal
# ---------------------------------------------------------------------------

def test_http_method_removal(base_spec):
    """Verify detection of removed HTTP methods on existing endpoints."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/items": {
            "get": {"responses": {"200": {"description": "List"}}},
            "delete": {"responses": {"204": {"description": "Deleted"}}}
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/items": {
            "get": {"responses": {"200": {"description": "List"}}}
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 1
    assert result["summary"]["methods_removed"] == 1

    change = result["changes"][0]
    assert change["type"] == "method_removed"
    assert change["change_type"] == "http_method_removed"
    assert change["endpoint"] == "/items"
    assert change["method"] == "DELETE"
    assert change["location"] == "method"


def test_http_method_addition(base_spec):
    """Verify detection of added HTTP methods on existing endpoints."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/items": {
            "get": {"responses": {"200": {"description": "List"}}}
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/items": {
            "get": {"responses": {"200": {"description": "List"}}},
            "post": {"responses": {"201": {"description": "Created"}}}
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 1
    assert result["summary"]["methods_added"] == 1

    change = result["changes"][0]
    assert change["type"] == "method_added"
    assert change["change_type"] == "method_added"
    assert change["endpoint"] == "/items"
    assert change["method"] == "POST"


# ---------------------------------------------------------------------------
# 4. Request parameter addition, removal, and type changes
# ---------------------------------------------------------------------------

def test_request_parameter_addition_and_removal(base_spec):
    """Verify detection of added and removed parameters across locations."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/users": {
            "get": {
                "parameters": [
                    {"name": "sort", "in": "query", "schema": {"type": "string"}},
                    {"name": "X-Session-ID", "in": "header", "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/users": {
            "get": {
                "parameters": [
                    {"name": "X-Session-ID", "in": "header", "schema": {"type": "string"}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 2
    assert result["summary"]["parameters_added"] == 1
    assert result["summary"]["parameters_removed"] == 1

    removed_change = next(c for c in result["changes"] if c["type"] == "parameter_removed")
    assert removed_change["field"] == "sort"
    assert removed_change["location"] == "query"

    added_change = next(c for c in result["changes"] if c["type"] == "parameter_added")
    assert added_change["field"] == "limit"
    assert added_change["location"] == "query"


def test_parameter_type_and_location_changes(base_spec):
    """Verify detection of parameter type modification and parameter location changes."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/data": {
            "get": {
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "auth_token", "in": "query", "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/data": {
            "get": {
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "string"}},
                    {"name": "auth_token", "in": "header", "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    # page type changed, auth_token location changed
    type_change = next(c for c in result["changes"] if c["field"] == "page")
    assert type_change["type"] == "parameter_type_changed"
    assert type_change["change_type"] == "field_type_changed"
    assert type_change["old_type"] == "integer"
    assert type_change["new_type"] == "string"

    loc_change = next(c for c in result["changes"] if c["field"] == "auth_token")
    assert loc_change["type"] == "parameter_location_changed"
    assert loc_change["old_value"] == "query"
    assert loc_change["new_value"] == "header"


# ---------------------------------------------------------------------------
# 5. Optional-to-required parameter changes
# ---------------------------------------------------------------------------

def test_optional_to_required_parameter(base_spec):
    """Verify parameter change from optional to required."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/search": {
            "get": {
                "parameters": [
                    {"name": "q", "in": "query", "required": False, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/search": {
            "get": {
                "parameters": [
                    {"name": "q", "in": "query", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 1
    change = result["changes"][0]
    assert change["type"] == "request_parameter_became_required"
    assert change["change_type"] == "request_parameter_became_required"
    assert change["field"] == "q"
    assert change["old_value"] is False
    assert change["new_value"] is True


def test_required_to_optional_parameter(base_spec):
    """Verify parameter change from required to optional."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/search": {
            "get": {
                "parameters": [
                    {"name": "tag", "in": "query", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/search": {
            "get": {
                "parameters": [
                    {"name": "tag", "in": "query", "required": False, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    change = result["changes"][0]
    assert change["type"] == "parameter_became_optional"
    assert change["old_value"] is True
    assert change["new_value"] is False


# ---------------------------------------------------------------------------
# 6. Request body and nested field changes
# ---------------------------------------------------------------------------

def test_request_body_added_and_removed(base_spec):
    """Verify request body addition and removal."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/users": {
            "post": {
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"type": "object"}}}
                },
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/users": {
            "post": {
                "responses": {"200": {"description": "OK"}}
            }
        }
    }

    # Removal
    res_rem = compare_specs(old_spec, new_spec)
    assert res_rem["summary"]["total_changes"] == 1
    assert res_rem["changes"][0]["type"] == "request_body_removed"

    # Addition
    res_add = compare_specs(new_spec, old_spec)
    assert res_add["summary"]["total_changes"] == 1
    assert res_add["changes"][0]["type"] == "request_body_added"


def test_request_body_nested_field_changes(base_spec):
    """Verify nested property additions and removals within request body."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/users": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "user": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "age": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/users": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "user": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "bio": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "OK"}}
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 2

    removed = next(c for c in result["changes"] if c["type"] == "request_field_removed")
    assert removed["field"] == "user.age"

    added = next(c for c in result["changes"] if c["type"] == "request_field_added")
    assert added["field"] == "user.bio"


# ---------------------------------------------------------------------------
# 7. Response field addition and removal
# ---------------------------------------------------------------------------

def test_response_field_addition_and_removal(base_spec):
    """Verify response field addition and removal."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/products": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Products",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "deprecated_tag": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/products": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Products",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "sku": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 2
    assert result["summary"]["fields_added"] == 1
    assert result["summary"]["fields_removed"] == 1

    rem = next(c for c in result["changes"] if c["type"] == "response_field_removed")
    assert rem["change_type"] == "response_field_removed"
    assert rem["field"] == "deprecated_tag"

    add = next(c for c in result["changes"] if c["type"] == "response_field_added")
    assert add["change_type"] == "response_field_added"
    assert add["field"] == "sku"


# ---------------------------------------------------------------------------
# 8. Response field type changes
# ---------------------------------------------------------------------------

def test_response_field_type_changes(base_spec):
    """Verify response field type mutation (e.g. number to string)."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/products/1": {
            "get": {
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "price": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/products/1": {
            "get": {
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "price": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 1
    change = result["changes"][0]
    assert change["type"] == "response_field_type_changed"
    assert change["change_type"] == "field_type_changed"
    assert change["field"] == "price"
    assert change["old_type"] == "number"
    assert change["new_type"] == "string"


# ---------------------------------------------------------------------------
# 9. Response status code removal
# ---------------------------------------------------------------------------

def test_response_status_code_removal_and_addition(base_spec):
    """Verify status code addition and removal."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/orders": {
            "post": {
                "responses": {
                    "200": {"description": "OK"},
                    "404": {"description": "Not Found"}
                }
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/orders": {
            "post": {
                "responses": {
                    "200": {"description": "OK"},
                    "201": {"description": "Created"}
                }
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 2

    rem = next(c for c in result["changes"] if c["type"] == "response_status_removed")
    assert rem["field"] == "404"
    assert rem["old_value"] == "404"

    add = next(c for c in result["changes"] if c["type"] == "response_status_added")
    assert add["field"] == "201"
    assert add["new_value"] == "201"


# ---------------------------------------------------------------------------
# 10. Required-property changes
# ---------------------------------------------------------------------------

def test_request_field_became_required(base_spec):
    """Verify optional request property becoming required."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/signup": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/signup": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["email"],
                                "properties": {
                                    "email": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "OK"}}
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    change = result["changes"][0]
    assert change["type"] == "request_field_became_required"
    assert change["change_type"] == "request_parameter_became_required"
    assert change["field"] == "email"
    assert change["old_value"] is False
    assert change["new_value"] is True


# ---------------------------------------------------------------------------
# 11. Enum and constraint changes
# ---------------------------------------------------------------------------

def test_enum_values_restricted(base_spec):
    """Verify restricted enum options detection."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/status": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "string",
                                    "enum": ["PENDING", "ACTIVE", "ARCHIVED"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/status": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "string",
                                    "enum": ["PENDING", "ACTIVE"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    change = result["changes"][0]
    assert change["type"] == "enum_values_restricted"
    assert change["change_type"] == "enum_values_restricted"
    assert "PENDING" in change["new_value"]
    assert "ARCHIVED" not in change["new_value"]


def test_constraint_changes(base_spec):
    """Verify numeric validation constraint changes (minimum)."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/items": {
            "get": {
                "parameters": [
                    {"name": "count", "in": "query", "schema": {"type": "integer", "minimum": 1}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/items": {
            "get": {
                "parameters": [
                    {"name": "count", "in": "query", "schema": {"type": "integer", "minimum": 10}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    # The constraint changed from 1 to 10
    assert result["summary"]["total_changes"] >= 1


# ---------------------------------------------------------------------------
# 12. Arrays and nested objects
# ---------------------------------------------------------------------------

def test_array_item_type_change_and_nested_objects(base_spec):
    """Verify recursive comparison of arrays and nested schemas."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/catalog": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Catalog",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "tags": {
                                            "type": "array",
                                            "items": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/catalog": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Catalog",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "tags": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    change = result["changes"][0]
    assert change["field"] == "tags[]"
    assert change["old_type"] == "integer"
    assert change["new_type"] == "string"


# ---------------------------------------------------------------------------
# 13. Local $ref resolution
# ---------------------------------------------------------------------------

def test_local_ref_resolution(base_spec):
    """Verify JSON Pointer and $ref resolution in components."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/profile": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Profile",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserProfile"}
                            }
                        }
                    }
                }
            }
        }
    }
    old_spec["components"] = {
        "schemas": {
            "UserProfile": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "score": {"type": "integer"}
                }
            }
        }
    }

    new_spec = copy.deepcopy(old_spec)
    # Remove score, change username type to integer
    new_spec["components"]["schemas"]["UserProfile"]["properties"].pop("score")
    new_spec["components"]["schemas"]["UserProfile"]["properties"]["username"]["type"] = "integer"

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 2

    type_chg = next(c for c in result["changes"] if c["field"] == "username")
    assert type_chg["old_type"] == "string"
    assert type_chg["new_type"] == "integer"

    rem_chg = next(c for c in result["changes"] if c["field"] == "score")
    assert rem_chg["type"] == "response_field_removed"


def test_rfc6901_escaped_pointer_resolution():
    """Verify RFC 6901 escaped characters (~1 for /, ~0 for ~)."""
    root = {
        "paths": {
            "/users/{id}": {"description": "Escaped path segment"}
        }
    }
    resolved = resolve_pointer(root, "#/paths/~1users~1{id}")
    assert resolved["description"] == "Escaped path segment"


# ---------------------------------------------------------------------------
# 14. Circular and unresolved references
# ---------------------------------------------------------------------------

def test_circular_and_recursive_schemas():
    """Verify self-referential schemas terminate safely without infinite loop."""
    old_spec = {
        "openapi": "3.0.3",
        "paths": {
            "/nodes": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Tree",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Node"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "children": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Node"}
                        }
                    }
                }
            }
        }
    }
    new_spec = copy.deepcopy(old_spec)
    new_spec["components"]["schemas"]["Node"]["properties"]["id"]["type"] = "string"

    result = compare_specs(old_spec, new_spec)

    assert result["success"] is True
    assert result["summary"]["total_changes"] == 1
    assert result["changes"][0]["field"] == "id"
    assert result["changes"][0]["old_type"] == "integer"
    assert result["changes"][0]["new_type"] == "string"


def test_unresolved_local_reference(base_spec):
    """Verify broken local pointer is handled safely without unhandled crash."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/broken": {
            "get": {
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DoesNotExist"}
                            }
                        }
                    }
                }
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)

    result = compare_specs(old_spec, new_spec)
    assert result["success"] is True
    # Graceful change handling
    assert len(result["changes"]) > 0


def test_unsupported_external_reference():
    """Verify external URLs are identified as unsupported external refs."""
    root = {"openapi": "3.0.3", "paths": {}}
    ext_ref = {"$ref": "https://example.com/schemas/user.json"}
    resolved = resolve_ref_if_needed(root, ext_ref)
    assert resolved.get("_is_external_ref") is True


# ---------------------------------------------------------------------------
# 15. Invalid YAML/JSON and malformed OpenAPI documents
# ---------------------------------------------------------------------------

def test_invalid_openapi_validation():
    """Verify structural validation rejects malformed dictionaries."""
    errors1 = validate_openapi_dict(None)
    assert any("valid json/yaml" in err.lower() for err in errors1)

    errors2 = validate_openapi_dict({"openapi": "2.0", "paths": {}})
    assert any("unsupported openapi version" in err.lower() for err in errors2)

    errors3 = validate_openapi_dict({"openapi": "3.0.0"})
    assert any("missing required 'paths'" in err.lower() for err in errors3)


def test_compare_specs_raise_on_error():
    """Verify raise_on_error parameter raises OpenAPIValidationError."""
    with pytest.raises(OpenAPIValidationError):
        compare_specs({}, {}, raise_on_error=True)


def test_malformed_files():
    """Verify compare_files returns error payload for broken JSON/YAML."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f_bad:
        f_bad.write("{ not valid: ")
        bad_path = f_bad.name

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f_good:
        f_good.write("openapi: '3.0.0'\npaths: {}\n")
        good_path = f_good.name

    try:
        report = compare_files(bad_path, good_path)
        assert report["success"] is False
        assert len(report["errors"]) > 0
        assert "malformed" in report["errors"][0].lower()
    finally:
        os.remove(bad_path)
        os.remove(good_path)


# ---------------------------------------------------------------------------
# 16. Deterministic output
# ---------------------------------------------------------------------------

def test_deterministic_output(base_spec):
    """Verify multiple executions produce bitwise identical ordered changes."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/z_endpoint": {"get": {"responses": {"200": {"description": "Z"}}}},
        "/a_endpoint": {"get": {"responses": {"200": {"description": "A"}}}}
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {}

    run1 = compare_specs(old_spec, new_spec)
    run2 = compare_specs(old_spec, new_spec)

    assert run1 == run2
    assert run1["changes"][0]["path"] == "/a_endpoint"
    assert run1["changes"][1]["path"] == "/z_endpoint"


# ---------------------------------------------------------------------------
# 17. Compatibility with Member 2 (Change Linter & Risk Engine)
# ---------------------------------------------------------------------------

def test_compatibility_with_member_2_pipeline(base_spec):
    """Verify that compare_specs output directly feeds Member 2's analyze_changes."""
    old_spec = copy.deepcopy(base_spec)
    old_spec["paths"] = {
        "/users": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Users",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "age": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    new_spec = copy.deepcopy(base_spec)
    new_spec["paths"] = {
        "/users": {
            "get": {
                "responses": {
                    "200": {
                        "description": "Users",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        # name removed -> breaking HIGH
                                        # age changed to string -> breaking HIGH
                                        "age": {"type": "string"},
                                        # nickname added -> non-breaking LOW
                                        "nickname": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # Step 1: Member 1 compares specifications
    diff_report = compare_specs(old_spec, new_spec)
    assert diff_report["success"] is True
    assert diff_report["summary"]["total_changes"] == 3

    # Step 2: Member 2 analyzes the diff_report directly
    lint_report = analyze_changes(diff_report)

    assert len(lint_report["issues"]) == 3
    # Two breaking changes (removed name, modified age type) -> high severity
    assert lint_report["summary"]["high"] == 2
    # One additive change (nickname added) -> low severity
    assert lint_report["summary"]["low"] == 1
    assert lint_report["review_required"] == 0

    # Verify rule evaluation
    rem_issue = next(i for i in lint_report["issues"] if i["change_type"] == "response_field_removed")
    assert rem_issue["breaking"] is True
    assert rem_issue["severity"] == "HIGH"
    assert rem_issue["old_value"] == "string"

    type_issue = next(i for i in lint_report["issues"] if i["change_type"] == "field_type_changed")
    assert type_issue["breaking"] is True
    assert type_issue["severity"] == "HIGH"
    assert type_issue["old_value"] == "integer"
    assert type_issue["new_value"] == "string"

    add_issue = next(i for i in lint_report["issues"] if i["change_type"] == "response_field_added")
    assert add_issue["breaking"] is False
    assert add_issue["severity"] == "LOW"
    assert add_issue["new_value"] == "string"


def test_compatibility_with_sample_yaml_files():
    """Verify end-to-end execution on repository sample YAML specs."""
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(tests_dir, ".."))
    old_yaml = os.path.join(repo_root, "samples", "old-api.yaml")
    new_yaml = os.path.join(repo_root, "samples", "new-api.yaml")

    diff_report = compare_files(old_yaml, new_yaml)
    assert diff_report["success"] is True
    assert diff_report["summary"]["total_changes"] == 7

    # Run through Member 2
    linter_report = analyze_changes(diff_report)
    assert linter_report["summary"]["high"] == 4  # 4 breaking changes
    assert linter_report["summary"]["low"] == 3   # 3 additions

    # Run legacy findings adapter
    findings = compare_apis(
        load_spec_from_file(old_yaml)[0],
        load_spec_from_file(new_yaml)[0]
    )
    breaking_findings = [f for f in findings if f["severity"] == "BREAKING"]
    assert len(breaking_findings) == 4
    assert len(findings) == 7


def test_fastapi_backend_integration():
    """Verify integration with Member 3's FastAPI POST /compare endpoint."""
    from fastapi.testclient import TestClient
    from backend.api import app

    tests_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(tests_dir, ".."))
    old_yaml = os.path.join(repo_root, "samples", "old-api.yaml")
    new_yaml = os.path.join(repo_root, "samples", "new-api.yaml")

    client = TestClient(app)
    with open(old_yaml, "rb") as f_old, open(new_yaml, "rb") as f_new:
        resp = client.post(
            "/compare",
            files={
                "old_file": ("old-api.yaml", f_old, "application/x-yaml"),
                "new_file": ("new-api.yaml", f_new, "application/x-yaml"),
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "FAIL"
    assert data["total_changes"] == 7
    assert data["breaking_changes"] == 4
    assert data["old_version"] == "1.0.0"
    assert data["new_version"] == "2.0.0"

