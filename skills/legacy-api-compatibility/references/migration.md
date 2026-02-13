# Migration Techniques

Step-by-step processes for migrating API consumers, implementing compatibility shims, and managing deprecation lifecycles.

## Deprecation Lifecycle

### Step 1: Announce Deprecation

Add the `Deprecation` header to responses and update documentation.

```python
from flask import Flask, request, jsonify, make_response
from datetime import datetime

app = Flask(__name__)

DEPRECATED_ENDPOINTS = {
    "/api/v1/users": {
        "sunset": "2026-03-01",
        "successor": "/api/v2/users",
        "reason": "v1 uses flat name field; v2 splits first/last name",
    },
}

@app.after_request
def add_deprecation_headers(response):
    rule = request.url_rule
    if rule and rule.rule in DEPRECATED_ENDPOINTS:
        info = DEPRECATED_ENDPOINTS[rule.rule]
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = datetime.fromisoformat(
            info["sunset"]
        ).strftime("%a, %d %b %Y %H:%M:%S GMT")
        response.headers["Link"] = f'<{info["successor"]}>; rel="successor-version"'
    return response
```

### Step 2: Monitor Usage

Track which consumers are still using deprecated endpoints.

```python
import logging
from collections import defaultdict

deprecated_usage = defaultdict(int)

@app.before_request
def track_deprecated_usage():
    rule = request.url_rule
    if rule and rule.rule in DEPRECATED_ENDPOINTS:
        api_key = request.headers.get("X-Api-Key", "anonymous")
        deprecated_usage[f"{api_key}:{rule.rule}"] += 1
        logging.warning(
            "Deprecated endpoint hit: %s by %s", rule.rule, api_key
        )
```

### Step 3: Communicate with Consumers

Send targeted notifications to consumers still using deprecated endpoints:

```python
def generate_migration_report():
    """Generate report of consumers needing migration."""
    report = []
    for key, count in deprecated_usage.items():
        api_key, endpoint = key.split(":", 1)
        info = DEPRECATED_ENDPOINTS.get(endpoint, {})
        report.append({
            "consumer": api_key,
            "deprecated_endpoint": endpoint,
            "call_count": count,
            "successor": info.get("successor"),
            "sunset_date": info.get("sunset"),
        })
    return sorted(report, key=lambda r: r["call_count"], reverse=True)
```

### Step 4: Return 410 Gone After Sunset

```python
from datetime import date

@app.before_request
def enforce_sunset():
    rule = request.url_rule
    if rule and rule.rule in DEPRECATED_ENDPOINTS:
        info = DEPRECATED_ENDPOINTS[rule.rule]
        if date.today() >= date.fromisoformat(info["sunset"]):
            return jsonify({
                "error": "gone",
                "message": f"This endpoint was removed on {info['sunset']}. "
                           f"Use {info['successor']} instead.",
                "successor": info["successor"],
                "documentation": f"https://api.example.com/docs/migration/{info['successor']}",
            }), 410
```

## Compatibility Shim Implementation

A translation layer that maps old API requests to new API internals.

### Full Request/Response Translation

```python
class V1CompatibilityShim:
    """Translate v1 requests to v2 format and v2 responses back to v1 format."""

    def translate_request(self, v1_request: dict) -> dict:
        """Convert v1 request body to v2 format."""
        v2_body = {}

        # Field renaming
        field_map = {
            "userName": "username",
            "emailAddress": "email",
            "phoneNum": "phone_number",
        }
        for old_key, new_key in field_map.items():
            if old_key in v1_request:
                v2_body[new_key] = v1_request[old_key]

        # Field splitting: v1 "name" → v2 "first_name"/"last_name"
        if "name" in v1_request:
            parts = v1_request["name"].split(" ", 1)
            v2_body["first_name"] = parts[0]
            v2_body["last_name"] = parts[1] if len(parts) > 1 else ""

        # Nested object restructuring: v1 flat → v2 nested
        if "street" in v1_request:
            v2_body["address"] = {
                "street": v1_request["street"],
                "city": v1_request.get("city", ""),
                "state": v1_request.get("state", ""),
                "postal_code": v1_request.get("zip", ""),
                "country": v1_request.get("country", "US"),
            }

        # Default value injection for new required fields
        v2_body.setdefault("locale", "en-US")
        v2_body.setdefault("timezone", "UTC")

        return v2_body

    def translate_response(self, v2_response: dict) -> dict:
        """Convert v2 response back to v1 format."""
        v1_body = {
            "id": v2_response["id"],
            "name": f"{v2_response['first_name']} {v2_response['last_name']}".strip(),
            "emailAddress": v2_response["email"],
            "phoneNum": v2_response.get("phone_number", ""),
        }

        if "address" in v2_response:
            addr = v2_response["address"]
            v1_body["street"] = addr.get("street", "")
            v1_body["city"] = addr.get("city", "")
            v1_body["state"] = addr.get("state", "")
            v1_body["zip"] = addr.get("postal_code", "")

        return v1_body

    def translate_error(self, v2_error: dict) -> dict:
        """Map v2 error format to v1 error format."""
        error_code_map = {
            "VALIDATION_ERROR": "INVALID_INPUT",
            "NOT_FOUND": "RESOURCE_NOT_FOUND",
            "CONFLICT": "DUPLICATE_ENTRY",
            "RATE_LIMITED": "TOO_MANY_REQUESTS",
        }
        return {
            "error": error_code_map.get(v2_error.get("code", ""), "UNKNOWN_ERROR"),
            "message": v2_error.get("detail", v2_error.get("message", "")),
        }
```

### Express.js Shim Middleware

```typescript
import { Request, Response, NextFunction } from "express";
import axios from "axios";

const V2_BASE = "http://api-v2:8080";

// Middleware that intercepts v1 requests and proxies to v2
function v1Shim(req: Request, res: Response, next: NextFunction) {
  const v1Path = req.path;
  const v2Path = v1Path.replace("/api/v1/", "/api/v2/");

  // Transform request body from v1 → v2 format
  const v2Body = transformRequestV1toV2(req.body, v1Path);

  axios({
    method: req.method,
    url: `${V2_BASE}${v2Path}`,
    data: v2Body,
    headers: {
      "Content-Type": "application/json",
      Authorization: req.headers.authorization,
    },
  })
    .then((v2Res) => {
      // Transform response from v2 → v1 format
      const v1Body = transformResponseV2toV1(v2Res.data, v1Path);
      res.status(v2Res.status).json(v1Body);
    })
    .catch((err) => {
      const status = err.response?.status || 502;
      const v1Error = transformErrorV2toV1(err.response?.data);
      res.status(status).json(v1Error);
    });
}

app.use("/api/v1/*", v1Shim);
```

## Codemods for Client Migration

Automated code transformations to update consumer code from old API to new API.

### jscodeshift — JavaScript/TypeScript

```javascript
// Transform: api.getUser(id) → api.users.get(id)
// File: transforms/migrate-api-v2.js

module.exports = function(fileInfo, api) {
  const j = api.jscodeshift;
  const root = j(fileInfo.source);

  // Replace api.getUser(id) with api.users.get(id)
  root
    .find(j.CallExpression, {
      callee: {
        type: "MemberExpression",
        object: { name: "api" },
        property: { name: "getUser" },
      },
    })
    .forEach((path) => {
      path.value.callee = j.memberExpression(
        j.memberExpression(j.identifier("api"), j.identifier("users")),
        j.identifier("get")
      );
    });

  // Replace api.createUser(data) with api.users.create(data)
  root
    .find(j.CallExpression, {
      callee: {
        type: "MemberExpression",
        object: { name: "api" },
        property: { name: "createUser" },
      },
    })
    .forEach((path) => {
      path.value.callee = j.memberExpression(
        j.memberExpression(j.identifier("api"), j.identifier("users")),
        j.identifier("create")
      );
    });

  return root.toSource();
};

// Run: npx jscodeshift -t transforms/migrate-api-v2.js src/
```

### libcst — Python

```python
# Transform: client.get_user(id) → client.users.get(id)
import libcst as cst
from libcst import matchers as m

class MigrateApiV2(cst.CSTTransformer):
    METHOD_MAP = {
        "get_user": ("users", "get"),
        "create_user": ("users", "create"),
        "list_users": ("users", "list"),
        "get_order": ("orders", "get"),
        "create_order": ("orders", "create"),
    }

    def leave_Call(self, original_node, updated_node):
        if not m.matches(updated_node.func, m.Attribute(value=m.Name("client"))):
            return updated_node

        attr = updated_node.func
        method_name = attr.attr.value

        if method_name in self.METHOD_MAP:
            resource, action = self.METHOD_MAP[method_name]
            new_func = cst.Attribute(
                value=cst.Attribute(
                    value=cst.Name("client"),
                    attr=cst.Name(resource),
                ),
                attr=cst.Name(action),
            )
            return updated_node.with_changes(func=new_func)

        return updated_node

# Usage:
# source_tree = cst.parse_module(open("myfile.py").read())
# modified = source_tree.visit(MigrateApiV2())
# open("myfile.py", "w").write(modified.code)
```

## Feature Flags for Gradual Migration

Use feature flags to control which API version is active, enabling gradual rollout and instant rollback.

### Implementation

```python
class FeatureFlagRouter:
    """Route API calls between legacy and new implementations using feature flags."""

    def __init__(self, flag_service, legacy_service, new_service):
        self._flags = flag_service
        self._legacy = legacy_service
        self._new = new_service

    def get_user(self, user_id: str, context: dict) -> dict:
        if self._flags.is_enabled("new_user_api", context=context):
            try:
                return self._new.get_user(user_id)
            except Exception as e:
                # Fallback to legacy on error during rollout
                logging.error("New API failed, falling back: %s", e)
                if self._flags.is_enabled("new_user_api_fallback", context=context):
                    return self._legacy.get_user(user_id)
                raise
        return self._legacy.get_user(user_id)
```

### Rollout Stages

```python
ROLLOUT_PLAN = {
    "stage_1": {
        "description": "Internal testing",
        "criteria": {"user_group": "employees"},
        "percentage": 100,
        "duration": "1 week",
    },
    "stage_2": {
        "description": "Beta users",
        "criteria": {"user_group": "beta"},
        "percentage": 100,
        "duration": "2 weeks",
    },
    "stage_3": {
        "description": "Gradual public rollout",
        "criteria": {},
        "percentage": 10,  # Start at 10%, increase to 25%, 50%, 100%
        "duration": "4 weeks",
    },
    "stage_4": {
        "description": "Full rollout + legacy removal",
        "criteria": {},
        "percentage": 100,
        "duration": "Permanent",
    },
}
```

## Database Schema Migration for API Compatibility

When API changes require database schema changes, maintain dual-write and dual-read capability during the transition.

### Expand-Contract Pattern

```sql
-- Phase 1: EXPAND — Add new columns alongside old ones
ALTER TABLE users ADD COLUMN first_name VARCHAR(100);
ALTER TABLE users ADD COLUMN last_name VARCHAR(100);

-- Backfill new columns from old data
UPDATE users SET
  first_name = SPLIT_PART(name, ' ', 1),
  last_name = SUBSTRING(name FROM POSITION(' ' IN name) + 1);

-- Phase 2: MIGRATE — Application writes to both old and new columns
-- (handled in application code with dual-write)

-- Phase 3: CONTRACT — Remove old column after all consumers migrated
ALTER TABLE users DROP COLUMN name;
```

### Application-Level Dual Write

```python
class UserRepository:
    def create_user(self, first_name: str, last_name: str, email: str):
        """Write to both old and new schema during migration."""
        self.db.execute(
            """
            INSERT INTO users (name, first_name, last_name, email)
            VALUES (%s, %s, %s, %s)
            """,
            (f"{first_name} {last_name}", first_name, last_name, email),
        )

    def get_user(self, user_id: int) -> dict:
        """Read from new columns, fall back to old if null."""
        row = self.db.fetchone(
            "SELECT * FROM users WHERE id = %s", (user_id,)
        )
        if row["first_name"]:
            return {
                "first_name": row["first_name"],
                "last_name": row["last_name"],
            }
        # Fallback for rows not yet backfilled
        parts = row["name"].split(" ", 1)
        return {
            "first_name": parts[0],
            "last_name": parts[1] if len(parts) > 1 else "",
        }
```

## Migration Checklist

Use this checklist when planning an API version migration:

- [ ] Document all breaking changes between versions
- [ ] Implement compatibility shim or translation layer
- [ ] Add `Deprecation` and `Sunset` headers to old endpoints
- [ ] Set up usage monitoring for deprecated endpoints
- [ ] Create migration guide for consumers
- [ ] Build codemods for automated client updates (if applicable)
- [ ] Set up contract tests covering both old and new versions
- [ ] Configure feature flags for gradual rollout
- [ ] Notify consumers with timeline and migration resources
- [ ] Monitor error rates during migration window
- [ ] Remove deprecated endpoints after sunset date
- [ ] Clean up compatibility shim code
- [ ] Archive old API documentation (keep accessible but mark as deprecated)
