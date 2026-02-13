# Networking & Services Debugging Reference

## Service Connectivity Debugging Path

Debug in this order to isolate the failing layer:

### 1. Verify Pod is Running and Ready
```bash
kubectl get pods -l app=<app-label> -o wide -n <namespace>
# All pods should be Running and Ready (e.g., 1/1)
```

### 2. Check Service Exists and Has Endpoints
```bash
kubectl get svc <service-name> -n <namespace>
kubectl get endpoints <service-name> -n <namespace>
# Endpoints should list pod IPs. Empty = no matching pods

# If endpoints are empty:
# - Check that pod labels match Service selector
kubectl get svc <service-name> -o yaml -n <namespace> | grep -A5 selector
kubectl get pods --show-labels -n <namespace>
```

### 3. Test Direct Pod Connectivity
```bash
# Bypass the service - connect directly to pod IP
kubectl run test-pod --rm -it --image=busybox --restart=Never -- wget -qO- http://<pod-ip>:<container-port>
```

### 4. Test Service Connectivity
```bash
# From within the cluster
kubectl run test-pod --rm -it --image=busybox --restart=Never -- wget -qO- http://<service-name>.<namespace>.svc.cluster.local:<port>
```

### 5. Test DNS Resolution
```bash
kubectl run test-dns --rm -it --image=busybox --restart=Never -- nslookup <service-name>.<namespace>.svc.cluster.local

# For more detailed DNS debugging
kubectl run test-dns --rm -it --image=nicolaka/netshoot --restart=Never -- dig <service-name>.<namespace>.svc.cluster.local
```

### 6. Use Port-Forward to Isolate Layers
```bash
# Bypass everything - connect directly to pod
kubectl port-forward pod/<pod-name> 8080:80 -n <namespace>
# Test: curl localhost:8080

# Bypass Ingress - connect through Service
kubectl port-forward svc/<service-name> 8080:80 -n <namespace>
# Test: curl localhost:8080
```

## DNS Debugging

### CoreDNS Issues
```bash
# Check CoreDNS pods are running
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns

# Test DNS from a pod
kubectl run dnstest --rm -it --image=busybox --restart=Never -- nslookup kubernetes.default
```

### ndots and Search Domain Issues
Pods use `/etc/resolv.conf` with `ndots:5` by default. Names with fewer than 5 dots are searched across multiple domains before external resolution.

```bash
# Check resolv.conf in a pod
kubectl exec <pod> -- cat /etc/resolv.conf

# If external DNS is slow, consider setting dnsConfig in pod spec:
# spec:
#   dnsConfig:
#     options:
#     - name: ndots
#       value: "2"
```

## NetworkPolicy Debugging

NetworkPolicies silently drop traffic. If connectivity works without policies but fails with them:

```bash
# List all NetworkPolicies
kubectl get networkpolicy -n <namespace>
kubectl describe networkpolicy -n <namespace>

# Check if any policy applies to your pod
kubectl get networkpolicy -n <namespace> -o yaml | grep -B5 -A10 'podSelector'

# Test connectivity with a debug pod
kubectl run nettest --rm -it --image=nicolaka/netshoot --restart=Never -n <namespace> -- \
  curl -v --connect-timeout 5 http://<service>:<port>
```

**Key rules:**
- If ANY NetworkPolicy selects a pod, only explicitly allowed traffic is permitted
- Default deny = create NetworkPolicy with podSelector matching pod but empty ingress/egress
- Ingress and egress are independent; both must allow the traffic

## Ingress Debugging

```bash
# Check Ingress resource
kubectl get ingress -n <namespace>
kubectl describe ingress <name> -n <namespace>

# Check Ingress controller logs
kubectl logs -n <ingress-namespace> -l app.kubernetes.io/name=ingress-nginx

# Common 502/503/504 errors:
# 502: Backend pod not responding (check pod health and readiness)
# 503: No endpoints (service has no ready pods)
# 504: Backend timeout (pod is too slow, increase timeout annotations)

# Verify backend service
kubectl get endpoints <backend-service> -n <namespace>
```

## Gateway API Debugging (v1.0+)

```bash
# Check Gateway status
kubectl get gateway -n <namespace>
kubectl describe gateway <name> -n <namespace>

# Check HTTPRoute
kubectl get httproute -n <namespace>
kubectl describe httproute <name> -n <namespace>
# Look at status.parents for route acceptance status

# Common issues:
# - HTTPRoute not accepted: parentRef doesn't match Gateway listener
# - BackendRef not found: service doesn't exist or wrong port
# - Cross-namespace routing requires ReferenceGrant
```
