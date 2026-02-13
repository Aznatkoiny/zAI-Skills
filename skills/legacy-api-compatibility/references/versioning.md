# API Versioning Strategies

Detailed guide for choosing and implementing API versioning approaches.

## URL Path Versioning

The most common approach for public APIs. Version is embedded in the URL path.

### Implementation

```python
# Flask example
from flask import Flask, Blueprint

app = Flask(__name__)

v1 = Blueprint("v1", __name__, url_prefix="/api/v1")
v2 = Blueprint("v2", __name__, url_prefix="/api/v2")

@v1.route("/users/<user_id>")
def get_user_v1(user_id):
    user = fetch_user(user_id)
    return {"id": user.id, "name": user.full_name, "email": user.email}

@v2.route("/users/<user_id>")
def get_user_v2(user_id):
    user = fetch_user(user_id)
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
    }

app.register_blueprint(v1)
app.register_blueprint(v2)
```

```typescript
// Express.js example
import { Router } from "express";

const v1Router = Router();
const v2Router = Router();

v1Router.get("/users/:id", async (req, res) => {
  const user = await getUser(req.params.id);
  res.json({ id: user.id, name: `${user.firstName} ${user.lastName}` });
});

v2Router.get("/users/:id", async (req, res) => {
  const user = await getUser(req.params.id);
  res.json({
    id: user.id,
    firstName: user.firstName,
    lastName: user.lastName,
    createdAt: user.createdAt,
  });
});

app.use("/api/v1", v1Router);
app.use("/api/v2", v2Router);
```

```java
// Spring Boot example
@RestController
@RequestMapping("/api/v1/users")
public class UserControllerV1 {
    @GetMapping("/{id}")
    public UserV1Response getUser(@PathVariable Long id) {
        User user = userService.findById(id);
        return new UserV1Response(user.getId(), user.getFullName());
    }
}

@RestController
@RequestMapping("/api/v2/users")
public class UserControllerV2 {
    @GetMapping("/{id}")
    public UserV2Response getUser(@PathVariable Long id) {
        User user = userService.findById(id);
        return new UserV2Response(
            user.getId(), user.getFirstName(),
            user.getLastName(), user.getCreatedAt()
        );
    }
}
```

**Trade-offs:**
- Explicit and easy to understand for consumers
- Fully cacheable by CDNs and proxies
- Creates URL proliferation over time
- Hard to share code between versions without careful architecture

## Header-Based Versioning

Version specified via custom HTTP header. Keeps URLs clean.

### Implementation

```python
# Flask with header-based versioning
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/api/users/<user_id>")
def get_user(user_id):
    version = request.headers.get("Api-Version", "1")
    user = fetch_user(user_id)

    if version == "2":
        return jsonify({
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        })
    else:
        return jsonify({
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
        })
```

```typescript
// Express middleware for header versioning
function versionRouter(handlers: Record<string, RequestHandler>): RequestHandler {
  return (req, res, next) => {
    const version = req.headers["api-version"] as string || "1";
    const handler = handlers[version] || handlers["1"];
    return handler(req, res, next);
  };
}

app.get("/api/users/:id", versionRouter({
  "1": getUserV1,
  "2": getUserV2,
}));
```

**Trade-offs:**
- Clean URLs with no version pollution
- Easy to add default version fallback
- Version is "hidden" — harder to discover and test in browser
- Some proxies strip custom headers

## Date-Based Versioning (Stripe Pattern)

Use a date-based version string. Each API change is pinned to a date. Clients lock to a version date and receive consistent behavior.

### Implementation

```python
# Stripe-style date versioning
from datetime import date
from flask import Flask, request, jsonify

app = Flask(__name__)

CHANGES = [
    {
        "date": date(2025, 6, 15),
        "description": "Split name into first_name/last_name",
        "transform": "split_name",
    },
    {
        "date": date(2025, 9, 1),
        "description": "Nest address into object",
        "transform": "nest_address",
    },
]

def apply_version_transforms(data: dict, client_version: str) -> dict:
    """Apply backward-compatible transforms for older API versions."""
    client_date = date.fromisoformat(client_version)
    result = data.copy()

    for change in reversed(CHANGES):
        if client_date < change["date"]:
            result = REVERSE_TRANSFORMS[change["transform"]](result)

    return result

REVERSE_TRANSFORMS = {
    "split_name": lambda d: {
        **d,
        "name": f"{d.pop('first_name')} {d.pop('last_name')}",
    },
    "nest_address": lambda d: {
        **d,
        "address": d.pop("address", {}).get("formatted", ""),
    },
}

@app.route("/api/users/<user_id>")
def get_user(user_id):
    version = request.headers.get("Api-Version", "2025-01-01")
    user_data = fetch_user_latest(user_id)
    return jsonify(apply_version_transforms(user_data, version))
```

**Trade-offs:**
- Very fine-grained — each breaking change is independently managed
- No big version jumps, smooth evolution
- Complex version routing logic
- Transform chain can become deep over time — needs periodic cleanup

## Content Negotiation

Use the `Accept` header with vendor media types.

```http
GET /api/users/123
Accept: application/vnd.myapi.v2+json
```

### Implementation

```python
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

def parse_version(accept_header: str) -> int:
    match = re.search(r"application/vnd\.myapi\.v(\d+)\+json", accept_header)
    return int(match.group(1)) if match else 1

@app.route("/api/users/<user_id>")
def get_user(user_id):
    version = parse_version(request.headers.get("Accept", ""))
    user = fetch_user(user_id)
    if version >= 2:
        return jsonify(serialize_user_v2(user))
    return jsonify(serialize_user_v1(user))
```

**Trade-offs:**
- Most RESTful approach per HTTP spec
- Supports fine-grained resource versioning
- Complex to implement and debug
- Tooling and client library support varies

## Query Parameter Versioning

Simple approach using a query parameter.

```
GET /api/users/123?version=2
```

Best used for internal APIs or during rapid prototyping. Avoid for production public APIs due to caching complications.

## API Gateway Version Routing

Use an API gateway to route versions without modifying application code.

### Nginx Example

```nginx
upstream api_v1 { server backend-v1:8080; }
upstream api_v2 { server backend-v2:8080; }

server {
    listen 80;

    location /api/v1/ {
        proxy_pass http://api_v1/;
    }

    location /api/v2/ {
        proxy_pass http://api_v2/;
    }

    # Header-based routing
    location /api/ {
        set $backend api_v2;
        if ($http_api_version = "1") {
            set $backend api_v1;
        }
        proxy_pass http://$backend;
    }
}
```

### AWS API Gateway

```yaml
# SAM template for multi-version API
Resources:
  ApiGateway:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod

  GetUserV1:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/v1.getUser
      Events:
        Api:
          Type: Api
          Properties:
            Path: /v1/users/{id}
            Method: get
            RestApiId: !Ref ApiGateway

  GetUserV2:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handlers/v2.getUser
      Events:
        Api:
          Type: Api
          Properties:
            Path: /v2/users/{id}
            Method: get
            RestApiId: !Ref ApiGateway
```

## Semantic Versioning for Libraries

For library/SDK APIs, use semver to communicate compatibility:

- **MAJOR** (1.x → 2.0): Breaking changes
- **MINOR** (1.1 → 1.2): Additive, backward-compatible features
- **PATCH** (1.1.1 → 1.1.2): Bug fixes only

### Automated Breaking Change Detection

```bash
# Rust: cargo-semver-checks
cargo install cargo-semver-checks
cargo semver-checks check-release

# TypeScript: api-extractor
npx @microsoft/api-extractor run --local

# OpenAPI: oasdiff
oasdiff breaking old-api.yaml new-api.yaml
```

## GraphQL Schema Evolution

GraphQL has built-in deprecation via the `@deprecated` directive:

```graphql
type User {
  id: ID!
  firstName: String!
  lastName: String!
  name: String @deprecated(reason: "Use firstName and lastName instead")
  email: String!
}
```

Detect breaking changes with schema diffing:

```bash
# graphql-inspector
npx graphql-inspector diff old-schema.graphql new-schema.graphql

# Apollo Rover
rover subgraph check my-graph@prod --schema new-schema.graphql
```

## gRPC / Protobuf Compatibility Rules

Protocol Buffers have strict rules for backward/forward compatibility:

### Safe Changes (Non-Breaking)
- Add new fields with new field numbers
- Add new enum values
- Add new RPC methods to a service
- Add new messages

### Breaking Changes (Avoid)
- Change field numbers
- Change field types (int32 → string)
- Remove or rename fields (use `reserved` instead)
- Change field from singular to repeated or vice versa

### Reserved Fields

```protobuf
message User {
  reserved 3, 7;           // reserved field numbers
  reserved "middle_name";   // reserved field names

  int32 id = 1;
  string first_name = 2;
  // field 3 was middle_name, now removed
  string email = 4;
  string last_name = 5;
}
```

## Choosing the Right Strategy

| Scenario | Recommended Approach |
|---|---|
| Public REST API with many consumers | URL path versioning |
| Internal microservice API | Header versioning |
| Rapidly evolving API (SaaS) | Date-based (Stripe pattern) |
| Library/SDK | Semantic versioning |
| GraphQL API | Schema evolution with @deprecated |
| gRPC service | Protobuf field evolution rules |
| Need fine-grained resource versioning | Content negotiation |
