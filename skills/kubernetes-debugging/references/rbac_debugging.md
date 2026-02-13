# RBAC & Security Debugging Reference

## RBAC Permission Errors

When you see `Error from server (Forbidden)`:

```bash
# Test if a specific action is allowed
kubectl auth can-i create pods -n <namespace>
kubectl auth can-i get secrets -n <namespace> --as=system:serviceaccount:<namespace>:<sa-name>
kubectl auth can-i '*' '*'  # Check for cluster-admin

# Check current identity (Kubernetes v1.29+)
kubectl auth whoami

# List all permissions for a service account
kubectl auth can-i --list --as=system:serviceaccount:<namespace>:<sa-name> -n <namespace>
```

## Finding Roles and Bindings

```bash
# Find ClusterRoles/Roles
kubectl get clusterroles | grep -v system:
kubectl get roles -n <namespace>

# Find bindings for a specific ServiceAccount
kubectl get clusterrolebindings -o json | jq '.items[] | select(.subjects[]? | .name=="<sa-name>" and .namespace=="<namespace>") | .metadata.name'
kubectl get rolebindings -n <namespace> -o json | jq '.items[] | select(.subjects[]? | .name=="<sa-name>") | .metadata.name'

# Describe a specific role to see its permissions
kubectl describe clusterrole <name>
kubectl describe role <name> -n <namespace>
```

## ServiceAccount Token Issues

```bash
# Check ServiceAccount exists
kubectl get serviceaccount <name> -n <namespace>

# Projected tokens (default since v1.24) are auto-rotated
# Check token volume mount in pod
kubectl get pod <pod> -o yaml | grep -A10 serviceAccountToken

# Create a manual token for testing
kubectl create token <sa-name> -n <namespace> --duration=1h
```

## Pod Security Standards (PSA)

Since Kubernetes v1.25+, PodSecurityPolicy is removed. Pod Security Admission (PSA) uses namespace labels:

```bash
# Check namespace enforcement level
kubectl get namespace <name> -o yaml | grep pod-security

# Levels: privileged, baseline, restricted
# Modes: enforce, audit, warn

# Test if a pod would be admitted
kubectl label --dry-run=server namespace <ns> pod-security.kubernetes.io/enforce=restricted

# Common PSA violations:
# - Running as root: set runAsNonRoot: true
# - Privileged container: remove privileged: true
# - Host namespaces: remove hostNetwork/hostPID/hostIPC
# - Capabilities: drop ALL, add only needed
```

## SecurityContext Debugging

```bash
# Check what security context a pod is running with
kubectl get pod <pod> -o yaml | grep -A15 securityContext

# Common issues:
# - Container needs to write to filesystem but readOnlyRootFilesystem: true
#   -> Add emptyDir volume for writable paths
# - Container can't bind to low port
#   -> Add NET_BIND_SERVICE capability or use port > 1024
# - Container runs as wrong user
#   -> Set runAsUser/runAsGroup in securityContext
```

## Policy Engine Violations (Gatekeeper/Kyverno)

### Gatekeeper (OPA)

```bash
# List all constraint templates
kubectl get constrainttemplates

# List all constraints
kubectl get constraints

# Check specific constraint and its violations
kubectl describe <constraint-kind> <name>

# Check audit results
kubectl get <constraint-kind> <name> -o yaml | grep -A20 violations

# Check Gatekeeper logs
kubectl logs -n gatekeeper-system -l control-plane=controller-manager
```

### Kyverno

```bash
# List all policies
kubectl get clusterpolicy
kubectl get policy -n <namespace>

# Check policy reports for violations
kubectl get policyreport -A
kubectl get clusterpolicyreport

# Describe a policy to see its rules
kubectl describe clusterpolicy <name>

# Check Kyverno logs
kubectl logs -n kyverno -l app.kubernetes.io/component=kyverno
```
