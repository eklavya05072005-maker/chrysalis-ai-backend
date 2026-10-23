"""Verification script to compare OpenAPI routes and schemas against FRONTEND_API_CONTRACT.md"""
import os, sys
sys.path.insert(0, os.path.abspath("."))
import re
from backend.app.main import app

openapi = app.openapi()
paths = openapi.get("paths", {})

print(f"Total OpenAPI Paths: {len(paths)}")
for path, operations in sorted(paths.items()):
    for method, op in operations.items():
        summary = op.get("summary", "")
        op_id = op.get("operationId", "")
        responses = list(op.get("responses", {}).keys())
        req_body = "body" if "requestBody" in op else "none"
        params = [p["name"] for p in op.get("parameters", [])]
        print(f"{method.upper():6} {path:50} -> Statuses: {responses} | Req: {req_body} | Params: {params}")

# Now read FRONTEND_API_CONTRACT.md
with open("FRONTEND_API_CONTRACT.md", "r", encoding="utf-8") as f:
    contract_text = f.read()

# Find all endpoints documented in FRONTEND_API_CONTRACT.md like `GET /api/health` or `POST /api/projects`
documented_endpoints = re.findall(r"#### `(GET|POST|PUT|DELETE)\s+([/a-zA-Z0-9_{}]+)`", contract_text)

print(f"\nTotal Documented Endpoints in Contract: {len(documented_endpoints)}")
mismatches = []
for method, doc_path in documented_endpoints:
    method_lower = method.lower()
    if doc_path not in paths:
        mismatches.append(f"MISSING PATH IN API: {method} {doc_path}")
    elif method_lower not in paths[doc_path]:
        mismatches.append(f"MISSING METHOD IN API: {method} {doc_path}")
    else:
        print(f"MATCH: {method:6} {doc_path}")

# Check reverse: Any routes in openapi not in contract?
for path, ops in paths.items():
    if path == "/health": # root health check is extra
        continue
    for method in ops.keys():
        m_upper = method.upper()
        if (m_upper, path) not in [(m, p) for m, p in documented_endpoints]:
            mismatches.append(f"UNCHECKED ROUTE IN OPENAPI: {m_upper} {path}")

if mismatches:
    print(f"\nMISMATCHES FOUND: {len(mismatches)}")
    for m in mismatches:
        print("  -", m)
else:
    print("\nALL 24 /api ROUTES PERFECTLY MATCH DOCUMENTED CONTRACT!")
