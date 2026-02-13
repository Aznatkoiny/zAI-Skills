# Testing & Verification for API Compatibility

Contract testing, OpenAPI diffing, and multi-version test strategies to prevent breaking changes.

## Contract Testing

Consumer-driven contract testing verifies that API changes don't break existing consumers.

### Pact — Consumer-Driven Contracts

#### Consumer Side (JavaScript)

```javascript
const { PactV3 } = require("@pact-foundation/pact");

const provider = new PactV3({
  consumer: "WebApp",
  provider: "UserService",
});

describe("User API Contract", () => {
  it("returns user by ID", async () => {
    // Define the expected interaction
    provider
      .given("a user with ID 123 exists")
      .uponReceiving("a request for user 123")
      .withRequest({
        method: "GET",
        path: "/api/v2/users/123",
        headers: { Accept: "application/json" },
      })
      .willRespondWith({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: {
          id: "123",
          firstName: like("John"),
          lastName: like("Doe"),
          email: like("john@example.com"),
          createdAt: iso8601DateTime(),
        },
      });

    await provider.executeTest(async (mockserver) => {
      const client = new UserApiClient(mockserver.url);
      const user = await client.getUser("123");
      expect(user.firstName).toBe("John");
    });
  });
});
```

#### Provider Side (Python)

```python
# test_pact_provider.py
import pytest
from pact_verifier import PactVerifier

@pytest.fixture
def verifier():
    return PactVerifier(
        provider="UserService",
        provider_base_url="http://localhost:8080",
    )

def test_verify_pacts(verifier):
    """Verify all consumer pacts against the running provider."""
    verifier.verify(
        pact_urls=[
            "https://pact-broker.example.com/pacts/provider/UserService/consumer/WebApp/latest",
            "https://pact-broker.example.com/pacts/provider/UserService/consumer/MobileApp/latest",
        ],
        provider_states_setup_url="http://localhost:8080/_pact/setup",
    )
```

### Schemathesis — Property-Based API Testing

Test API compliance against OpenAPI spec automatically:

```python
import schemathesis

schema = schemathesis.from_url("http://localhost:8080/openapi.json")

@schema.parametrize()
def test_api(case):
    """Auto-generate test cases from OpenAPI spec."""
    response = case.call()
    case.validate_response(response)
```

```bash
# CLI usage
schemathesis run http://localhost:8080/openapi.json \
  --checks all \
  --hypothesis-max-examples 100
```

### Spring Cloud Contract (Java)

```groovy
// contracts/shouldReturnUser.groovy
Contract.make {
    description "should return user by ID"
    request {
        method GET()
        url "/api/v2/users/123"
        headers {
            accept(applicationJson())
        }
    }
    response {
        status OK()
        headers {
            contentType(applicationJson())
        }
        body([
            id: "123",
            firstName: $(anyNonBlankString()),
            lastName: $(anyNonBlankString()),
            email: $(anyEmail()),
        ])
    }
}
```

## OpenAPI Specification Diffing

Detect breaking changes automatically by comparing OpenAPI specifications.

### oasdiff

```bash
# Install
go install github.com/tufin/oasdiff@latest

# Check for breaking changes
oasdiff breaking api/v1-spec.yaml api/v2-spec.yaml

# Output as JSON for CI/CD
oasdiff breaking api/v1-spec.yaml api/v2-spec.yaml --format json

# Check changelog (all changes, not just breaking)
oasdiff changelog api/v1-spec.yaml api/v2-spec.yaml

# Flatten composed specs before diffing
oasdiff breaking api/v1-spec.yaml api/v2-spec.yaml --flatten
```

#### GitHub Actions Integration

```yaml
name: API Breaking Change Check
on:
  pull_request:
    paths:
      - "api/**"
      - "openapi/**"

jobs:
  check-breaking:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Get base spec
        run: git show origin/main:api/openapi.yaml > /tmp/base-spec.yaml

      - name: Check for breaking changes
        uses: tufin/oasdiff-action/breaking@main
        with:
          base: /tmp/base-spec.yaml
          revision: api/openapi.yaml
          fail-on: ERR  # Fail on breaking changes
```

### Optic

```bash
# Install
npm install -g @useoptic/optic

# Compare two specs
optic diff api/v1-spec.yaml api/v2-spec.yaml

# Watch for changes in development
optic capture openapi.yaml --server-url http://localhost:8080

# CI integration: check captured traffic against spec
optic ci --upload
```

### openapi-diff (Java)

```bash
# Run via Docker
docker run --rm -v $(pwd):/specs openapitools/openapi-diff \
  /specs/old-api.yaml /specs/new-api.yaml \
  --markdown /specs/diff-report.md
```

## Multi-Version Test Suites

Strategies for maintaining tests that cover multiple API versions simultaneously.

### Parameterized Tests

```python
import pytest

API_VERSIONS = ["v1", "v2"]

@pytest.fixture(params=API_VERSIONS)
def api_version(request):
    return request.param

@pytest.fixture
def api_client(api_version):
    return ApiClient(base_url=f"http://localhost:8080/api/{api_version}")

class TestUserEndpoints:
    def test_get_user_returns_200(self, api_client):
        response = api_client.get("/users/123")
        assert response.status_code == 200

    def test_get_user_has_required_fields(self, api_client, api_version):
        response = api_client.get("/users/123")
        data = response.json()

        # Common fields across all versions
        assert "id" in data
        assert "email" in data

        # Version-specific field assertions
        if api_version == "v1":
            assert "name" in data
            assert "first_name" not in data
        elif api_version == "v2":
            assert "first_name" in data
            assert "last_name" in data

    def test_create_user(self, api_client, api_version):
        if api_version == "v1":
            payload = {"name": "John Doe", "email": "john@example.com"}
        else:
            payload = {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
            }
        response = api_client.post("/users", json=payload)
        assert response.status_code == 201
```

### TypeScript — Version-Aware Test Helpers

```typescript
import { describe, it, expect } from "vitest";

const versions = ["v1", "v2"] as const;
type ApiVersion = (typeof versions)[number];

// Version-specific payload factories
const userPayload: Record<ApiVersion, object> = {
  v1: { name: "John Doe", email: "john@example.com" },
  v2: { firstName: "John", lastName: "Doe", email: "john@example.com" },
};

// Version-specific response validators
const validateUserResponse: Record<ApiVersion, (data: any) => void> = {
  v1: (data) => {
    expect(data).toHaveProperty("name");
    expect(data).toHaveProperty("email");
  },
  v2: (data) => {
    expect(data).toHaveProperty("firstName");
    expect(data).toHaveProperty("lastName");
    expect(data).toHaveProperty("email");
    expect(data).toHaveProperty("createdAt");
  },
};

describe.each(versions)("User API %s", (version) => {
  const client = createApiClient(`http://localhost:8080/api/${version}`);

  it("creates a user", async () => {
    const res = await client.post("/users", userPayload[version]);
    expect(res.status).toBe(201);
    validateUserResponse[version](res.data);
  });

  it("retrieves a user", async () => {
    const res = await client.get("/users/123");
    expect(res.status).toBe(200);
    validateUserResponse[version](res.data);
  });
});
```

### Backward Compatibility Test Pattern

Verify that new API versions can handle old request formats gracefully:

```python
class TestBackwardCompatibility:
    """Ensure v2 API gracefully handles v1-style requests."""

    def test_v2_accepts_v1_name_field(self, v2_client):
        """v2 should accept 'name' and split into first/last."""
        response = v2_client.post("/users", json={
            "name": "John Doe",  # v1-style field
            "email": "john@example.com",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"

    def test_v2_returns_deprecation_warning_for_old_fields(self, v2_client):
        """v2 should warn when receiving deprecated fields."""
        response = v2_client.post("/users", json={
            "name": "John Doe",
            "email": "john@example.com",
        })
        assert "Deprecation" in response.headers or "X-Deprecation-Warning" in response.headers
```

## CI/CD Pipeline Integration

### Complete Pipeline Example

```yaml
# .github/workflows/api-compatibility.yml
name: API Compatibility Check

on:
  pull_request:
    paths:
      - "src/api/**"
      - "openapi/**"
      - "tests/api/**"

jobs:
  breaking-change-detection:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check OpenAPI breaking changes
        run: |
          git show origin/main:openapi/spec.yaml > /tmp/base.yaml
          oasdiff breaking /tmp/base.yaml openapi/spec.yaml

  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Start API server
        run: docker compose up -d api

      - name: Run Pact provider verification
        run: |
          npx pact-provider-verifier \
            --provider-base-url http://localhost:8080 \
            --pact-broker-base-url ${{ secrets.PACT_BROKER_URL }} \
            --provider UserService \
            --provider-app-version ${{ github.sha }}

      - name: Run Schemathesis
        run: |
          schemathesis run http://localhost:8080/openapi.json \
            --checks all \
            --report

  multi-version-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        api-version: [v1, v2]
    steps:
      - uses: actions/checkout@v4

      - name: Run version-specific tests
        run: pytest tests/api/ -k "${{ matrix.api-version }}" -v
        env:
          API_VERSION: ${{ matrix.api-version }}
```

## Monitoring During Migration

Track key metrics during version transitions:

```python
# Prometheus metrics for API version monitoring
from prometheus_client import Counter, Histogram

api_requests = Counter(
    "api_requests_total",
    "Total API requests by version",
    ["version", "endpoint", "method", "status"],
)

api_latency = Histogram(
    "api_request_duration_seconds",
    "API request duration by version",
    ["version", "endpoint"],
)

deprecated_hits = Counter(
    "deprecated_endpoint_hits_total",
    "Hits to deprecated endpoints",
    ["endpoint", "consumer"],
)
```
