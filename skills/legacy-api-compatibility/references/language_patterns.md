# Language-Specific Compatibility Patterns

Idiomatic deprecation and backward compatibility techniques for Java, Python, TypeScript/JavaScript, Go, Rust, and C#.

## Python

### Deprecation Warnings

```python
import warnings
import functools

def deprecated(reason: str, removal_version: str = ""):
    """Decorator to mark functions as deprecated."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            msg = f"{func.__qualname__} is deprecated: {reason}"
            if removal_version:
                msg += f" Will be removed in {removal_version}."
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@deprecated("Use get_user_by_id() instead", removal_version="3.0")
def get_user(user_id):
    return get_user_by_id(user_id)
```

### Module-Level Deprecation with `__getattr__`

```python
# mypackage/__init__.py
import warnings

_DEPRECATED_NAMES = {
    "OldClient": ("NewClient", "2.0"),
    "old_function": ("new_function", "2.0"),
}

def __getattr__(name):
    if name in _DEPRECATED_NAMES:
        new_name, version = _DEPRECATED_NAMES[name]
        warnings.warn(
            f"{name} is deprecated, use {new_name} instead. "
            f"Will be removed in {version}.",
            DeprecationWarning,
            stacklevel=2,
        )
        return globals()[new_name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

### Backward-Compatible Signature Changes

```python
def create_user(
    name: str | None = None,  # Deprecated
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str,
) -> User:
    """Create a user. Use first_name/last_name instead of name."""
    if name is not None:
        warnings.warn(
            "The 'name' parameter is deprecated. Use 'first_name' and 'last_name'.",
            DeprecationWarning,
            stacklevel=2,
        )
        parts = name.split(" ", 1)
        first_name = first_name or parts[0]
        last_name = last_name or (parts[1] if len(parts) > 1 else "")

    if not first_name:
        raise ValueError("first_name is required")

    return User(first_name=first_name, last_name=last_name or "", email=email)
```

### Class Renaming with Backward Compatibility

```python
class UserService:
    """Modern user service implementation."""
    def get(self, user_id: str) -> User:
        ...

# Keep old name working but warn
class UserManager(UserService):
    def __init_subclass__(cls, **kwargs):
        warnings.warn(
            "UserManager is deprecated, use UserService instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init_subclass__(**kwargs)

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "UserManager is deprecated, use UserService instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
```

## TypeScript / JavaScript

### Deprecation with JSDoc + Runtime Warning

```typescript
/** @deprecated Use `getUserById` instead. Will be removed in v3.0. */
function getUser(id: string): Promise<User> {
  if (process.env.NODE_ENV !== "production") {
    console.warn("getUser() is deprecated. Use getUserById() instead.");
  }
  return getUserById(id);
}
```

### Proxy-Based Deprecation Tracking

```typescript
function createDeprecatedProxy<T extends object>(
  target: T,
  deprecations: Record<string, string>,
): T {
  return new Proxy(target, {
    get(obj, prop: string) {
      if (prop in deprecations) {
        console.warn(
          `Property "${prop}" is deprecated: ${deprecations[prop]}`
        );
      }
      return Reflect.get(obj, prop);
    },
  });
}

// Usage
const api = createDeprecatedProxy(realApi, {
  getUser: "Use api.users.get() instead",
  createUser: "Use api.users.create() instead",
});
```

### Overloaded Function Signatures for Compatibility

```typescript
// Support both old and new calling conventions
interface CreateUserOptionsV1 {
  name: string;
  email: string;
}

interface CreateUserOptionsV2 {
  firstName: string;
  lastName: string;
  email: string;
}

function createUser(options: CreateUserOptionsV1): Promise<User>;
function createUser(options: CreateUserOptionsV2): Promise<User>;
function createUser(
  options: CreateUserOptionsV1 | CreateUserOptionsV2,
): Promise<User> {
  let firstName: string;
  let lastName: string;

  if ("name" in options) {
    // V1 format — emit deprecation warning
    console.warn("createUser({ name }) is deprecated. Use firstName/lastName.");
    const parts = options.name.split(" ");
    firstName = parts[0];
    lastName = parts.slice(1).join(" ");
  } else {
    firstName = options.firstName;
    lastName = options.lastName;
  }

  return userService.create({ firstName, lastName, email: options.email });
}
```

### Conditional Exports in package.json

```json
{
  "name": "my-sdk",
  "exports": {
    ".": {
      "import": "./dist/esm/index.js",
      "require": "./dist/cjs/index.js"
    },
    "./v1": {
      "import": "./dist/esm/v1/index.js",
      "require": "./dist/cjs/v1/index.js"
    },
    "./v2": {
      "import": "./dist/esm/v2/index.js",
      "require": "./dist/cjs/v2/index.js"
    }
  }
}
```

## Java

### @Deprecated Annotation with Javadoc

```java
public class UserService {

    /**
     * @deprecated Use {@link #getUserById(String)} instead.
     *             Will be removed in version 3.0.
     */
    @Deprecated(since = "2.0", forRemoval = true)
    public User getUser(int userId) {
        return getUserById(String.valueOf(userId));
    }

    public User getUserById(String userId) {
        // Modern implementation
        return userRepository.findById(userId);
    }
}
```

### Interface Default Methods for Backward Compatibility

```java
// Original interface
public interface PaymentProcessor {
    PaymentResult process(String cardNumber, int amountCents);
}

// Extended with new method + backward-compatible default
public interface PaymentProcessor {
    @Deprecated(since = "2.0", forRemoval = true)
    PaymentResult process(String cardNumber, int amountCents);

    // New method with richer type
    default PaymentResult process(PaymentRequest request) {
        // Default delegates to old method for backward compatibility
        return process(request.getCardNumber(), request.getAmountCents());
    }
}
```

### Builder Pattern for Evolving APIs

```java
public class UserRequest {
    private final String firstName;
    private final String lastName;
    private final String email;
    private final String locale;      // Added in v2
    private final String timezone;    // Added in v2

    private UserRequest(Builder builder) {
        this.firstName = builder.firstName;
        this.lastName = builder.lastName;
        this.email = builder.email;
        this.locale = builder.locale;
        this.timezone = builder.timezone;
    }

    public static class Builder {
        private String firstName;
        private String lastName;
        private String email;
        private String locale = "en-US";      // Defaults for backward compat
        private String timezone = "UTC";

        /** @deprecated Use firstName() and lastName() instead. */
        @Deprecated(since = "2.0")
        public Builder name(String fullName) {
            String[] parts = fullName.split(" ", 2);
            this.firstName = parts[0];
            this.lastName = parts.length > 1 ? parts[1] : "";
            return this;
        }

        public Builder firstName(String firstName) { this.firstName = firstName; return this; }
        public Builder lastName(String lastName) { this.lastName = lastName; return this; }
        public Builder email(String email) { this.email = email; return this; }
        public Builder locale(String locale) { this.locale = locale; return this; }
        public Builder timezone(String timezone) { this.timezone = timezone; return this; }

        public UserRequest build() { return new UserRequest(this); }
    }
}

// Both old and new callers work:
// Old: new UserRequest.Builder().name("John Doe").email("j@x.com").build()
// New: new UserRequest.Builder().firstName("John").lastName("Doe").email("j@x.com").build()
```

## Go

### Module Major Version Paths

```
mymodule/             # v0.x, v1.x
mymodule/v2/          # v2.x (separate module path per semver)
mymodule/v3/          # v3.x
```

```go
// go.mod for v2
module github.com/example/mymodule/v2

go 1.21
```

```go
// Consumer imports:
import "github.com/example/mymodule/v2/client"
```

### Type Aliases for Migration

```go
// v2/compat.go — provide aliases for renamed types
package v2

import v1 "github.com/example/mymodule"

// Deprecated: Use UserRequest instead.
type CreateUserRequest = v1.CreateUserRequest

// Deprecated: Use UserService instead.
type UserManager = UserService
```

### Interface Embedding for Extension

```go
// v1 interface
type UserStore interface {
    GetUser(id string) (*User, error)
    CreateUser(u *User) error
}

// v2 extends v1 — all v1 implementations still satisfy v2
// if they also implement the new method
type UserStoreV2 interface {
    UserStore  // Embeds all v1 methods
    UpdateUser(id string, updates map[string]any) error
    DeleteUser(id string) error
}

// Adapter to make v1 impl work with v2 interface
type V1Adapter struct {
    UserStore
}

func (a *V1Adapter) UpdateUser(id string, updates map[string]any) error {
    user, err := a.GetUser(id)
    if err != nil {
        return err
    }
    applyUpdates(user, updates)
    return a.CreateUser(user) // Upsert via create
}

func (a *V1Adapter) DeleteUser(id string) error {
    return fmt.Errorf("delete not supported in v1 backend")
}
```

### Functional Options for Backward-Compatible Configuration

```go
type ClientOption func(*clientConfig)

type clientConfig struct {
    baseURL    string
    timeout    time.Duration
    apiVersion string     // Added in v2
    retries    int        // Added in v2
}

func WithBaseURL(url string) ClientOption {
    return func(c *clientConfig) { c.baseURL = url }
}

func WithTimeout(d time.Duration) ClientOption {
    return func(c *clientConfig) { c.timeout = d }
}

// New options — old code continues to work without them
func WithAPIVersion(v string) ClientOption {
    return func(c *clientConfig) { c.apiVersion = v }
}

func WithRetries(n int) ClientOption {
    return func(c *clientConfig) { c.retries = n }
}

func NewClient(opts ...ClientOption) *Client {
    cfg := &clientConfig{
        baseURL:    "https://api.example.com",
        timeout:    30 * time.Second,
        apiVersion: "v1",  // Default for backward compat
        retries:    0,
    }
    for _, opt := range opts {
        opt(cfg)
    }
    return &Client{config: cfg}
}
```

## Rust

### #[deprecated] Attribute

```rust
#[deprecated(since = "2.0.0", note = "Use `get_user_by_id` instead")]
pub fn get_user(id: u64) -> User {
    get_user_by_id(&id.to_string())
}

pub fn get_user_by_id(id: &str) -> User {
    // New implementation
    todo!()
}
```

### Feature Flags for API Transitions

```toml
# Cargo.toml
[features]
default = ["v2-api"]
v1-api = []          # Enable legacy v1 API
v2-api = []          # Enable modern v2 API
```

```rust
#[cfg(feature = "v1-api")]
pub mod v1 {
    pub fn create_user(name: &str, email: &str) -> User {
        let parts: Vec<&str> = name.splitn(2, ' ').collect();
        super::v2::create_user(parts[0], parts.get(1).unwrap_or(&""), email)
    }
}

#[cfg(feature = "v2-api")]
pub mod v2 {
    pub fn create_user(first_name: &str, last_name: &str, email: &str) -> User {
        User { first_name: first_name.into(), last_name: last_name.into(), email: email.into() }
    }
}
```

### cargo-semver-checks

```bash
# Install
cargo install cargo-semver-checks

# Check for semver violations before publishing
cargo semver-checks check-release

# Compare against specific baseline
cargo semver-checks check-release --baseline-version 1.5.0
```

## C#

### [Obsolete] Attribute

```csharp
public class UserService
{
    [Obsolete("Use GetUserByIdAsync instead. Will be removed in v3.0.", error: false)]
    public User GetUser(int userId)
    {
        return GetUserByIdAsync(userId.ToString()).GetAwaiter().GetResult();
    }

    public async Task<User> GetUserByIdAsync(string userId)
    {
        // Modern async implementation
        return await _repository.FindByIdAsync(userId);
    }
}
```

### Default Interface Methods (C# 8+)

```csharp
public interface IPaymentProcessor
{
    // Original method
    [Obsolete("Use ProcessAsync(PaymentRequest) instead.")]
    PaymentResult Process(string cardNumber, int amountCents);

    // New method with default implementation for backward compatibility
    async Task<PaymentResult> ProcessAsync(PaymentRequest request)
    {
        // Default: delegate to old synchronous method
        return await Task.FromResult(
            Process(request.CardNumber, request.AmountCents)
        );
    }
}
```

### Extension Methods for Non-Breaking Additions

```csharp
// Original class (cannot modify)
public class LegacyApiClient
{
    public string GetUserJson(int id) { ... }
}

// Extension: add modern typed method without modifying original
public static class LegacyApiClientExtensions
{
    public static async Task<User> GetUserAsync(this LegacyApiClient client, string id)
    {
        var json = client.GetUserJson(int.Parse(id));
        return JsonSerializer.Deserialize<User>(json);
    }
}
```

## Common Cross-Language Patterns

### Optional Parameters with Defaults

Add new parameters with sensible defaults so existing callers don't break:

| Language | Pattern |
|---|---|
| Python | `def func(old_param, *, new_param="default")` |
| TypeScript | `function func(oldParam: string, newParam = "default")` |
| Java | Overloaded methods or Builder pattern |
| Go | Functional options (`WithXxx()` pattern) |
| Rust | Builder pattern or `Default` trait |
| C# | Optional parameters `void Func(string old, string newP = "default")` |

### Wrapper/Shim for Renamed APIs

When renaming a function, keep the old name as a thin wrapper:

```python
# Python
def old_name(*args, **kwargs):
    warnings.warn("old_name is deprecated, use new_name", DeprecationWarning)
    return new_name(*args, **kwargs)
```

```typescript
// TypeScript
/** @deprecated Use newName instead */
export const oldName = (...args: Parameters<typeof newName>) => {
  console.warn("oldName is deprecated, use newName");
  return newName(...args);
};
```

```java
// Java
@Deprecated(since = "2.0", forRemoval = true)
public Result oldName(String arg) {
    return newName(arg);
}
```
