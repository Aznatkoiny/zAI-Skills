# Design Patterns for Legacy API Compatibility

Full implementations of adapter, facade, anti-corruption layer, strangler fig, and BFF patterns.

## Adapter Pattern

Wrap a legacy interface to match the expected modern interface. Use when integrating with a third-party or legacy API that cannot be modified.

### Python — REST Client Adapter

```python
from dataclasses import dataclass
from typing import Protocol

# Modern interface your code expects
class PaymentProvider(Protocol):
    def charge(self, amount: float, currency: str, token: str) -> "PaymentResult": ...
    def refund(self, transaction_id: str, amount: float) -> "RefundResult": ...

@dataclass
class PaymentResult:
    transaction_id: str
    status: str
    amount: float

@dataclass
class RefundResult:
    refund_id: str
    status: str

# Legacy API client (cannot be modified)
class LegacyBillingSystem:
    def create_charge(self, amt_cents: int, cc_token: str, curr: str = "USD"):
        # Returns: {"code": 0, "ref": "CHG-xxx", "msg": "approved"}
        ...

    def reverse_charge(self, ref: str, amt_cents: int):
        # Returns: {"code": 0, "reversal_ref": "REV-xxx"}
        ...

# Adapter bridges the gap
class LegacyBillingAdapter:
    STATUS_MAP = {0: "succeeded", 1: "declined", 2: "error"}

    def __init__(self, legacy: LegacyBillingSystem):
        self._legacy = legacy

    def charge(self, amount: float, currency: str, token: str) -> PaymentResult:
        result = self._legacy.create_charge(
            amt_cents=int(amount * 100),
            cc_token=token,
            curr=currency.upper(),
        )
        return PaymentResult(
            transaction_id=result["ref"],
            status=self.STATUS_MAP.get(result["code"], "unknown"),
            amount=amount,
        )

    def refund(self, transaction_id: str, amount: float) -> RefundResult:
        result = self._legacy.reverse_charge(
            ref=transaction_id,
            amt_cents=int(amount * 100),
        )
        return RefundResult(
            refund_id=result["reversal_ref"],
            status=self.STATUS_MAP.get(result["code"], "unknown"),
        )
```

### TypeScript — API Response Adapter

```typescript
// Legacy API response shape
interface LegacyUserResponse {
  usr_id: number;
  usr_nm: string;
  usr_email: string;
  created_ts: number; // Unix timestamp
  addr_line1: string;
  addr_city: string;
  addr_zip: string;
}

// Modern model your app uses
interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
  address: {
    street: string;
    city: string;
    postalCode: string;
  };
}

// Adapter function
function adaptLegacyUser(legacy: LegacyUserResponse): User {
  return {
    id: String(legacy.usr_id),
    name: legacy.usr_nm,
    email: legacy.usr_email,
    createdAt: new Date(legacy.created_ts * 1000),
    address: {
      street: legacy.addr_line1,
      city: legacy.addr_city,
      postalCode: legacy.addr_zip,
    },
  };
}

// Adapter class wrapping legacy API client
class UserApiAdapter {
  constructor(private legacyClient: LegacyUserApi) {}

  async getUser(id: string): Promise<User> {
    const raw = await this.legacyClient.fetchUser(Number(id));
    return adaptLegacyUser(raw);
  }

  async listUsers(page: number, limit: number): Promise<User[]> {
    const raw = await this.legacyClient.getUsers(page, limit);
    return raw.map(adaptLegacyUser);
  }
}
```

### Java — Interface Adapter

```java
// Modern interface
public interface NotificationService {
    CompletableFuture<NotificationResult> send(Notification notification);
}

// Legacy system
public class LegacySMSGateway {
    public int sendSMS(String phone, String body, String sender) {
        // Returns status code: 0=sent, 1=failed, 2=queued
        return 0;
    }
}

// Adapter
public class SMSGatewayAdapter implements NotificationService {
    private final LegacySMSGateway legacy;
    private final String defaultSender;

    public SMSGatewayAdapter(LegacySMSGateway legacy, String defaultSender) {
        this.legacy = legacy;
        this.defaultSender = defaultSender;
    }

    @Override
    public CompletableFuture<NotificationResult> send(Notification notification) {
        return CompletableFuture.supplyAsync(() -> {
            int code = legacy.sendSMS(
                notification.getRecipient(),
                notification.getBody(),
                defaultSender
            );
            return new NotificationResult(
                code == 0 ? Status.SENT : code == 2 ? Status.PENDING : Status.FAILED,
                notification.getId()
            );
        });
    }
}
```

## Facade Pattern

Provide a simplified, unified interface over multiple legacy subsystems. Use when legacy code has scattered or complex APIs that consumers should not depend on directly.

### Python — Unified Order Facade

```python
class OrderFacade:
    """Unified interface over legacy inventory, billing, and shipping systems."""

    def __init__(
        self,
        inventory: LegacyInventoryService,
        billing: LegacyBillingService,
        shipping: LegacyShippingService,
    ):
        self._inventory = inventory
        self._billing = billing
        self._shipping = shipping

    def place_order(self, items: list[dict], payment: dict, address: dict) -> dict:
        # Step 1: Reserve inventory (legacy uses SKU codes)
        reservations = []
        for item in items:
            res = self._inventory.hold_stock(
                sku=item["product_id"],
                qty=item["quantity"],
                warehouse="AUTO",
            )
            reservations.append(res["hold_id"])

        # Step 2: Process payment (legacy uses cents)
        total_cents = sum(
            item["quantity"] * int(item["unit_price"] * 100) for item in items
        )
        charge = self._billing.charge_card(
            amount=total_cents,
            token=payment["token"],
            currency_code="USD",
        )

        # Step 3: Create shipment (legacy uses separate address fields)
        shipment = self._shipping.create_shipment(
            line1=address["street"],
            city=address["city"],
            state=address["state"],
            zip_code=address["postal_code"],
            items=[{"sku": i["product_id"], "qty": i["quantity"]} for i in items],
        )

        return {
            "order_id": f"ORD-{charge['ref']}",
            "status": "confirmed",
            "shipment_tracking": shipment["tracking_number"],
            "total": total_cents / 100,
        }
```

### TypeScript — Service Aggregation Facade

```typescript
class AnalyticsFacade {
  constructor(
    private legacyMetrics: LegacyMetricsDB,
    private legacyEvents: LegacyEventLog,
    private legacyReports: LegacyReportEngine,
  ) {}

  async getDashboardData(userId: string, dateRange: DateRange): Promise<Dashboard> {
    const [metrics, events, report] = await Promise.all([
      this.legacyMetrics.queryMetrics(userId, dateRange.start, dateRange.end),
      this.legacyEvents.getEvents({ user: userId, from: dateRange.start }),
      this.legacyReports.generate("user_summary", { uid: userId }),
    ]);

    return {
      activeUsers: metrics.active_count,
      revenue: metrics.total_rev / 100,
      recentEvents: events.map(e => ({
        type: e.evt_type,
        timestamp: new Date(e.ts),
        details: JSON.parse(e.payload),
      })),
      summary: report.body,
    };
  }
}
```

## Anti-Corruption Layer (ACL)

A boundary layer from Domain-Driven Design that translates between a legacy/external system's model and your internal domain model. Use when integrating with systems whose data model would "corrupt" your clean domain.

### Project Structure

```
src/
├── domain/
│   ├── models/
│   │   └── order.py          # Clean domain model
│   └── ports/
│       └── order_repository.py  # Interface (port)
├── infrastructure/
│   └── legacy/
│       ├── client.py          # Raw legacy API client
│       ├── models.py          # Legacy response DTOs
│       └── acl.py             # Anti-corruption layer
└── application/
    └── order_service.py       # Uses domain models only
```

### Python — Full ACL Implementation

```python
# domain/models/order.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

@dataclass
class OrderItem:
    product_id: str
    name: str
    quantity: int
    unit_price: float

@dataclass
class Order:
    id: str
    customer_id: str
    status: OrderStatus
    items: list[OrderItem]
    total: float
    created_at: datetime

# domain/ports/order_repository.py
from typing import Protocol

class OrderRepository(Protocol):
    def get_by_id(self, order_id: str) -> Order: ...
    def list_by_customer(self, customer_id: str) -> list[Order]: ...

# infrastructure/legacy/models.py — legacy data shapes
@dataclass
class LegacyOrderRecord:
    ORD_NUM: str
    CUST_CODE: str
    STATUS_CD: int
    LINE_ITEMS: list[dict]  # [{"SKU": "X", "DESC": "Y", "QTY": 1, "PRICE": "9.99"}]
    TOTAL_AMT: str          # "99.99"
    CREATE_DT: str          # "20250115"

# infrastructure/legacy/acl.py — the anti-corruption layer
class OrderACL:
    """Translates between legacy order system and domain model."""

    STATUS_MAP = {
        0: OrderStatus.PENDING,
        1: OrderStatus.CONFIRMED,
        2: OrderStatus.SHIPPED,
        3: OrderStatus.DELIVERED,
        9: OrderStatus.CANCELLED,
    }

    def __init__(self, legacy_client: LegacyOrderClient):
        self._client = legacy_client

    def get_by_id(self, order_id: str) -> Order:
        record = self._client.fetch_order(order_id)
        return self._translate(record)

    def list_by_customer(self, customer_id: str) -> list[Order]:
        records = self._client.query_orders(cust_code=customer_id)
        return [self._translate(r) for r in records]

    def _translate(self, record: LegacyOrderRecord) -> Order:
        return Order(
            id=record.ORD_NUM,
            customer_id=record.CUST_CODE,
            status=self.STATUS_MAP.get(record.STATUS_CD, OrderStatus.PENDING),
            items=[
                OrderItem(
                    product_id=li["SKU"],
                    name=li["DESC"],
                    quantity=int(li["QTY"]),
                    unit_price=float(li["PRICE"]),
                )
                for li in record.LINE_ITEMS
            ],
            total=float(record.TOTAL_AMT),
            created_at=datetime.strptime(record.CREATE_DT, "%Y%m%d"),
        )
```

## Strangler Fig Pattern

Incrementally replace a legacy system by routing traffic to the new implementation piece by piece. The legacy system is gradually "strangled" as more functionality moves to the new system.

### Implementation Approaches

#### 1. Router-Based (API Gateway)

```python
# Route configuration — gradually move endpoints to new service
ROUTES = {
    # Migrated to new service
    "/api/users": {"backend": "new-service", "port": 8081},
    "/api/products": {"backend": "new-service", "port": 8081},

    # Still on legacy
    "/api/orders": {"backend": "legacy-service", "port": 8080},
    "/api/invoices": {"backend": "legacy-service", "port": 8080},
}
```

#### 2. Feature-Flag Based

```python
from feature_flags import is_enabled

class OrderService:
    def __init__(self, legacy: LegacyOrderService, modern: ModernOrderService):
        self._legacy = legacy
        self._modern = modern

    def get_order(self, order_id: str) -> Order:
        if is_enabled("use_modern_orders", default=False):
            return self._modern.get_order(order_id)
        return self._legacy.get_order(order_id)

    def create_order(self, request: CreateOrderRequest) -> Order:
        if is_enabled("use_modern_orders", default=False):
            return self._modern.create_order(request)
        return self._legacy.create_order(request)
```

#### 3. Percentage-Based Rollout

```python
import hashlib

def route_to_backend(user_id: str, rollout_pct: int = 0) -> str:
    """Deterministic routing based on user ID hash."""
    hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 100
    if hash_val < rollout_pct:
        return "new-service"
    return "legacy-service"
```

### Migration Tracking

Track which endpoints have been migrated:

```python
MIGRATION_STATUS = {
    "GET /api/users":        {"status": "migrated",    "date": "2025-03-15"},
    "POST /api/users":       {"status": "migrated",    "date": "2025-04-01"},
    "GET /api/products":     {"status": "migrated",    "date": "2025-04-15"},
    "GET /api/orders":       {"status": "in_progress", "date": None},
    "POST /api/orders":      {"status": "planned",     "date": None},
    "GET /api/invoices":     {"status": "planned",     "date": None},
}
```

## Backend-for-Frontend (BFF) as Compatibility Layer

A BFF acts as an aggregation and translation layer between frontend clients and backend APIs. Use when different clients (web, mobile, legacy) need different API shapes from the same backend.

### TypeScript — BFF for Multiple Client Versions

```typescript
import express from "express";

const app = express();

// BFF for legacy mobile app (v1 format)
app.get("/bff/mobile/v1/dashboard", async (req, res) => {
  const [user, orders, notifications] = await Promise.all([
    backendApi.get(`/users/${req.userId}`),
    backendApi.get(`/orders?user=${req.userId}&limit=5`),
    backendApi.get(`/notifications?user=${req.userId}&unread=true`),
  ]);

  // Legacy mobile app expects flat structure
  res.json({
    user_name: user.name,
    user_email: user.email,
    recent_orders: orders.map(o => ({
      id: o.id,
      total: o.total,
      status: o.status,
    })),
    unread_count: notifications.length,
  });
});

// BFF for modern web app (v2 format)
app.get("/bff/web/v2/dashboard", async (req, res) => {
  const [user, orders, notifications, analytics] = await Promise.all([
    backendApi.get(`/users/${req.userId}`),
    backendApi.get(`/orders?user=${req.userId}&limit=10`),
    backendApi.get(`/notifications?user=${req.userId}`),
    backendApi.get(`/analytics/user/${req.userId}`),
  ]);

  // Modern web app expects rich nested structure
  res.json({
    user: { ...user, analytics },
    orders: {
      items: orders,
      hasMore: orders.length === 10,
    },
    notifications: {
      items: notifications,
      unreadCount: notifications.filter(n => !n.read).length,
    },
  });
});
```

## Choosing the Right Pattern

| Scenario | Pattern | Rationale |
|---|---|---|
| Wrapping a single legacy service | **Adapter** | Simple interface translation |
| Simplifying multiple legacy services | **Facade** | Unified entry point |
| Protecting domain from legacy models | **ACL** | Clean domain boundaries |
| Replacing legacy system incrementally | **Strangler Fig** | Gradual, low-risk migration |
| Multiple clients needing different shapes | **BFF** | Client-specific aggregation |
| Combining patterns | **ACL + Strangler Fig** | Common: ACL isolates while migrating |
