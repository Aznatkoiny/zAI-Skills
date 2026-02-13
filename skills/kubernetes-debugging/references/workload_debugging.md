# Deployments & Workload Debugging Reference

## Deployment Rollout Issues

```bash
# Check rollout status
kubectl rollout status deployment/<name> -n <namespace>

# View rollout history
kubectl rollout history deployment/<name> -n <namespace>

# Check specific revision
kubectl rollout history deployment/<name> --revision=2 -n <namespace>

# Compare current vs previous
kubectl get deployment <name> -o yaml -n <namespace>
```

**Stuck rollout causes:**
- **Failed readiness probes**: New pods never become Ready
  ```bash
  kubectl get pods -l app=<label> -n <namespace>
  kubectl describe pod <new-pod> -n <namespace>
  # Look for readiness probe failures in Events
  ```
- **Insufficient resources**: New pods can't be scheduled
- **Image pull failures**: New image doesn't exist
- **maxUnavailable/maxSurge misconfiguration**: Not enough room to roll new pods
- **PodDisruptionBudget blocking**: PDB preventing old pod termination

## Rollback

```bash
# Rollback to previous revision
kubectl rollout undo deployment/<name> -n <namespace>

# Rollback to specific revision
kubectl rollout undo deployment/<name> --to-revision=2 -n <namespace>

# Pause/resume rollout (for canary-style debugging)
kubectl rollout pause deployment/<name> -n <namespace>
kubectl rollout resume deployment/<name> -n <namespace>
```

## HorizontalPodAutoscaler (HPA) Issues

```bash
# Check HPA status
kubectl get hpa -n <namespace>
kubectl describe hpa <name> -n <namespace>

# Common issues:
# "unable to fetch metrics" -> metrics-server not installed or not reporting
kubectl top pods -n <namespace>  # If this fails, metrics-server is broken

# "current replicas equals desired replicas" but load is high
# -> Check if resource requests are set (HPA needs requests to calculate utilization)

# HPA flapping (scaling up and down rapidly)
# -> Increase stabilizationWindowSeconds in HPA spec behavior
```

## Job and CronJob Debugging

```bash
# Check Job status
kubectl get jobs -n <namespace>
kubectl describe job <name> -n <namespace>

# Check pods created by Job
kubectl get pods -l job-name=<job-name> -n <namespace>
kubectl logs job/<job-name> -n <namespace>

# CronJob not firing
kubectl get cronjobs -n <namespace>
kubectl describe cronjob <name> -n <namespace>
# Check: schedule syntax, suspend flag, concurrencyPolicy
# Check: LAST SCHEDULE and ACTIVE fields

# Common Job issues:
# - backoffLimit reached: pods keep failing
# - activeDeadlineSeconds exceeded: job takes too long
# - concurrencyPolicy=Forbid: previous job still running
```

## StatefulSet Debugging

```bash
# StatefulSets create pods with stable identities (pod-0, pod-1, ...)
kubectl get statefulset -n <namespace>
kubectl describe statefulset <name> -n <namespace>

# Pods are created/deleted sequentially by default
# If pod-1 is stuck, check pod-0 is running first
kubectl get pods -l app=<label> -n <namespace>

# Common issues:
# - PVC not binding: each pod gets its own PVC from volumeClaimTemplates
#   kubectl get pvc -l app=<label> -n <namespace>
# - Pod stuck in Pending: previous pod not Ready yet (ordered startup)
# - Partition rollout: check partition value in updateStrategy
```

## DaemonSet Debugging

```bash
kubectl get daemonset -n <namespace>
kubectl describe daemonset <name> -n <namespace>

# Check DESIRED vs CURRENT vs READY
# If DESIRED != CURRENT, some nodes aren't getting pods:
# - Node taints not tolerated by DaemonSet
# - Node selector doesn't match all nodes
# - Node is cordoned

# Find which nodes are missing the DaemonSet pod
kubectl get pods -l <ds-label> -o wide -n <namespace>
kubectl get nodes  # Compare node list
```

## ReplicaSet Issues

```bash
# Check ReplicaSets for a deployment
kubectl get rs -l app=<label> -n <namespace>

# Old ReplicaSets not scaling down = stuck rollout
# New ReplicaSet not scaling up = scheduling/image issues

# Check events for ReplicaSet
kubectl describe rs <name> -n <namespace>
```
