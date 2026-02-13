# Pod Debugging Reference

## Pod Lifecycle States

### Pending
Pod accepted but not running yet.

**Diagnostic steps:**
```bash
kubectl describe pod <name> -n <namespace>
# Look at Events section for scheduling failures
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name>
```

**Common causes:**
- **Insufficient resources**: "0/3 nodes are available: insufficient cpu/memory"
  - Fix: Reduce requests, scale cluster, or remove resource hogs
  - Check: `kubectl describe nodes | grep -A5 "Allocated resources"`
- **Unbound PVC**: "persistentvolumeclaim is not bound"
  - Fix: Create matching PV or fix StorageClass
  - Check: `kubectl get pvc -n <namespace>`
- **Node selector/affinity mismatch**: "0/3 nodes match selector"
  - Fix: Adjust nodeSelector/affinity or label nodes
  - Check: `kubectl get nodes --show-labels`
- **Taints not tolerated**: "node had taint that the pod didn't tolerate"
  - Fix: Add tolerations to pod spec or remove taint from node
  - Check: `kubectl describe node <name> | grep Taints`
- **Unschedulable node**: Node is cordoned
  - Check: `kubectl get nodes` (look for SchedulingDisabled)

### CrashLoopBackOff
Container starts, crashes, Kubernetes restarts it with exponential backoff.

**Diagnostic steps:**
```bash
# Get logs from the crashed container
kubectl logs <pod> --previous -n <namespace>

# Check exit code
kubectl describe pod <pod> -n <namespace>
# Look at: Last State -> Terminated -> Exit Code
# Exit Code 1: Application error
# Exit Code 137: OOMKilled (128+9=SIGKILL) or killed by system
# Exit Code 139: Segmentation fault (128+11)
# Exit Code 143: Graceful termination (128+15=SIGTERM)

# If no useful logs, debug with ephemeral container
kubectl debug -it <pod> --image=busybox --target=<container> -n <namespace>
```

**Common causes:**
- Application error at startup (missing env vars, bad config)
- Missing dependencies (config files, secrets, services)
- Wrong `command` or `args` in pod spec
- Insufficient memory (OOMKilled)
- Readiness/liveness probe misconfiguration causing premature restarts

### ImagePullBackOff / ErrImagePull
Cannot pull the container image.

**Diagnostic steps:**
```bash
kubectl describe pod <pod> -n <namespace>
# Look at Events for the exact pull error message
```

**Common causes:**
- Wrong image name or tag: Verify image exists in registry
- Private registry without imagePullSecret:
  ```bash
  kubectl create secret docker-registry regcred \
    --docker-server=<registry> \
    --docker-username=<user> \
    --docker-password=<pass> \
    -n <namespace>
  # Then add imagePullSecrets to pod spec
  ```
- Network issues reaching registry
- Image architecture mismatch (amd64 vs arm64)

### OOMKilled
Container exceeded its memory limit.

**Diagnostic steps:**
```bash
kubectl describe pod <pod> -n <namespace>
# Last State: Terminated - Reason: OOMKilled

# Check current memory usage of running pods
kubectl top pods -n <namespace>

# Check memory limits
kubectl get pod <pod> -o jsonpath='{.spec.containers[*].resources}' -n <namespace>
```

**Resolution:**
- Increase `resources.limits.memory`
- Profile application memory usage and fix memory leaks
- For JVM apps: Set `-Xmx` to ~75% of container memory limit

### CreateContainerConfigError
Container cannot be created due to config issues.

**Common causes:**
- Referenced ConfigMap doesn't exist
- Referenced Secret doesn't exist
- Invalid environment variable references

```bash
# Check what configmaps/secrets the pod references
kubectl get pod <pod> -o yaml | grep -A2 'configMapKeyRef\|secretKeyRef'
# Verify they exist
kubectl get configmap -n <namespace>
kubectl get secrets -n <namespace>
```

### Init Container Failures

```bash
# Check init container status
kubectl describe pod <pod> -n <namespace>
# Look at "Init Containers" section

# Get init container logs
kubectl logs <pod> -c <init-container-name> -n <namespace>
```

Init containers run sequentially. If one fails, the pod stays in Init state.

## Ephemeral Debug Containers (kubectl debug)

Available stable since Kubernetes v1.28+.

```bash
# Add debug container to running pod (shares PID namespace by default since 1.28)
kubectl debug -it <pod> --image=busybox --target=<container-name> -n <namespace>

# Copy pod and add debug container (useful for crashed pods)
kubectl debug <pod> -it --copy-to=debug-pod --share-processes --image=ubuntu -n <namespace>

# Copy pod with different command (override entrypoint)
kubectl debug <pod> -it --copy-to=debug-pod --container=<container> -- sh

# Useful debug images:
# busybox - minimal, has basic unix tools
# nicolaka/netshoot - networking tools (dig, curl, tcpdump, nmap)
# ubuntu - full OS for complex debugging
```

## Probes Debugging

If pods keep restarting due to probe failures:

```bash
# Check probe configuration
kubectl get pod <pod> -o yaml | grep -A10 'livenessProbe\|readinessProbe\|startupProbe'

# Common issues:
# - initialDelaySeconds too short (app hasn't started yet)
# - timeoutSeconds too short
# - Wrong port or path
# - Startup probe missing (slow-starting apps need it)

# Test probe endpoint manually
kubectl exec <pod> -- wget -qO- http://localhost:<port>/<path>
kubectl exec <pod> -- curl -s http://localhost:<port>/<path>
```
