---
name: legacy-api-compatibility
description: |
  Guide for maintaining backward compatibility, migrating deprecated APIs, and bridging legacy and modern API versions.
  Use when: upgrading or deprecating API versions, writing adapter/wrapper layers, implementing versioning strategies,
  migrating consumers between API versions, detecting breaking changes, adding compatibility shims, handling
  third-party API deprecations, or maintaining multiple API versions simultaneously.
---

# Legacy API Compatibility

Patterns, strategies, and techniques for maintaining backward compatibility and migrating between API versions across REST, GraphQL, gRPC, and library APIs.

## Compatibility Decision Workflow

1. **Assess** the change: Is it additive, breaking, or behavioral?
2. **Classify** using the breaking change checklist below
3. **Choose strategy**: versioning, adapter layer, deprecation + migration, or feature flag
4. **Implement** using the appropriate pattern from references
5. **Verify** with contract tests and OpenAPI diffing
6. **Communicate** via sunset headers, changelogs, and deprecation warnings

## Breaking Change Classification

| Change Type | Breaking? | Strategy |
|---|---|---|
| Add optional field to response | No | Ship directly |
| Add required field to request | **Yes** | New version or make optional with default |
| Remove field from response | **Yes** | Deprecate first, remove in next major |
| Rename field | **Yes** | Support both with alias layer |
| Change field type | **Yes** | New version or content negotiation |
| Change error codes/format | **Yes** | Version or compatibility shim |
| Change URL/endpoint path | **Yes** | Redirect + new version |
| Tighten validation rules | **Yes** | Feature flag rollout |
| Loosen validation rules | Usually no | Ship with monitoring |
| Add new endpoint | No | Ship directly |
| Change authentication scheme | **Yes** | Parallel support + migration window |

## API Versioning Strategies

| Strategy | Example | Pros | Cons | Best For |
|---|---|---|---|---|
| **URL path** | `/api/v2/users` | Simple, explicit, cacheable | URL pollution, hard to sunset | Public APIs |
| **Header** | `Api-Version: 2` | Clean URLs, flexible | Hidden, harder to test | Internal APIs |
| **Query param** | `/api/users?version=2` | Easy to test | Caching issues, messy | Quick iteration |
| **Content negotiation** | `Accept: application/vnd.api.v2+json` | RESTful, precise | Complex, tooling gaps | Hypermedia APIs |
| **Date-based** (Stripe-style) | `Stripe-Version: 2025-01-15` | Fine-grained, no version jumps | Complex routing | High-churn APIs |

## Core Design Patterns

### Adapter Pattern — Bridge incompatible interfaces

```python
class LegacyPaymentGateway:
    def process_payment(self, amount_cents, card_number):
        return {"status": "ok", "transaction_id": "TXN-123"}

class ModernPaymentAdapter:
    def __init__(self, legacy: LegacyPaymentGateway):
        self._legacy = legacy

    def charge(self, amount: float, payment_method: dict) -> dict:
        result = self._legacy.process_payment(
            amount_cents=int(amount * 100),
            card_number=payment_method["card"]["number"]
        )
        return {
            "id": result["transaction_id"],
            "status": "succeeded" if result["status"] == "ok" else "failed",
            "amount": amount,
            "currency": "usd"
        }
```

### Strangler Fig — Incremental migration

Route traffic progressively from legacy to new implementation:

```
Client → API Gateway / Router
            ├── /v1/users     → Legacy Service (shrinking)
            ├── /v1/products  → New Service (growing)
            └── /v1/orders    → Legacy Service (next to migrate)
```

### Anti-Corruption Layer — Isolate domain from legacy

```typescript
// Translate between legacy external API and clean internal models
class OrderAntiCorruptionLayer {
  constructor(private legacyClient: LegacyOrderAPI) {}

  async getOrder(id: string): Promise<Order> {
    const raw = await this.legacyClient.fetchOrderXML(id);
    return {
      id: raw.OrderNum,
      status: this.mapStatus(raw.StatusCode),
      items: raw.LineItems.map(li => ({
        productId: li.ItemSKU,
        quantity: li.Qty,
        price: parseFloat(li.UnitPrice),
      })),
      createdAt: new Date(raw.CreateDt),
    };
  }

  private mapStatus(code: number): OrderStatus {
    const statusMap: Record<number, OrderStatus> = {
      0: "pending", 1: "confirmed", 2: "shipped",
      3: "delivered", 9: "cancelled",
    };
    return statusMap[code] ?? "unknown";
  }
}
```

### Compatibility Shim — Map old requests to new API

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/api/v1/users/<user_id>", methods=["GET"])
def get_user_v1(user_id):
    """V1 compatibility shim — translates v2 response to v1 format."""
    v2_response = call_v2_api(f"/api/v2/users/{user_id}")
    return jsonify({
        "id": v2_response["id"],
        "name": f"{v2_response['first_name']} {v2_response['last_name']}",
        "email": v2_response["email"],
        # v1 had flat address, v2 has nested object
        "address": v2_response["address"]["formatted"],
    })
```

## Deprecation Lifecycle

1. **Announce**: Add `Deprecation` header + update docs
2. **Warn**: Emit `Sunset` header with target date (RFC 8594)
3. **Monitor**: Track usage of deprecated endpoints
4. **Migrate**: Provide migration guide + codemods if possible
5. **Remove**: After sunset date, return `410 Gone`

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Mar 2026 00:00:00 GMT
Link: </api/v2/users>; rel="successor-version"
```

## Quick Reference: Tools

| Tool | Purpose | Ecosystem |
|---|---|---|
| **oasdiff** | OpenAPI breaking change detection | Any (CLI) |
| **Optic** | API change review in CI | Any (CLI/CI) |
| **Pact** | Consumer-driven contract testing | Multi-language |
| **Schemathesis** | Property-based API testing from OpenAPI | Python |
| **cargo-semver-checks** | Detect semver violations in Rust crates | Rust |
| **api-extractor** | API surface tracking for TypeScript | TypeScript |
| **jscodeshift** | JavaScript/TypeScript codemods | JS/TS |
| **libcst** | Python concrete syntax tree transforms | Python |
| **Rector** | PHP automated refactoring | PHP |
| **openapi-diff** | OpenAPI spec comparison | Java (CLI) |

## Reference Files

| Topic | Reference | When to Use |
|---|---|---|
| **Versioning Strategies** | [versioning.md](references/versioning.md) | Choosing or implementing API versioning |
| **Design Patterns** | [patterns.md](references/patterns.md) | Adapter, Facade, ACL, Strangler Fig, BFF patterns with full examples |
| **Migration Techniques** | [migration.md](references/migration.md) | Deprecation workflows, shims, codemods, feature flags |
| **Testing & Verification** | [testing.md](references/testing.md) | Contract testing, OpenAPI diffing, multi-version test suites |
| **Language-Specific Patterns** | [language_patterns.md](references/language_patterns.md) | Idiomatic deprecation and compatibility in Java, Python, TS, Go, Rust, C# |
