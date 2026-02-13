---
name: kubernetes-debugging
description: "Comprehensive Kubernetes debugging guide for diagnosing and resolving cluster issues. Use when troubleshooting pod failures (CrashLoopBackOff, OOMKilled, ImagePullBackOff), service connectivity, networking, DNS, storage/PVC issues, RBAC permissions, node problems, deployment rollouts, and resource constraints. Covers kubectl debugging commands, ephemeral debug containers, log analysis, and modern CLI tools (k9s, stern, kubectx)."
---

# Kubernetes Debugging

Quick-reference guide for diagnosing and resolving Kubernetes cluster issues via CLI.

## Debugging Workflow

1. **Identify**: What resource is failing? (`kubectl get pods,svc,deploy -o wide`)
2. **Describe**: Get events and status (`kubectl describe <resource>`)
3. **Logs**: Check container logs (`kubectl logs <pod> [-c container] [--previous]`)
4. **Events**: Check cluster events (`kubectl get events --sort-by=.lastTimestamp`)
5. **Exec/Debug**: Get shell access (`kubectl exec` or `kubectl debug`)

## Quick Diagnostic Commands

| What | Command |
|------|---------|
| Pod status overview | `kubectl get pods -o wide --all-namespaces` |
| Pod details + events | `kubectl describe pod <name>` |
| Current logs | `kubectl logs <pod> [-c container]` |
| Previous crash logs | `kubectl logs <pod> --previous` |
| Multi-container logs | `kubectl logs <pod> --all-containers` |
| Follow logs | `kubectl logs -f <pod>` |
| Logs by label | `kubectl logs -l app=myapp --all-containers` |
| Recent events | `kubectl get events --sort-by=.lastTimestamp` |
| Events for a pod | `kubectl get events --field-selector involvedObject.name=<pod>` |
| Resource usage | `kubectl top pods` / `kubectl top nodes` |
| Exec into pod | `kubectl exec -it <pod> -- /bin/sh` |
| Debug with ephemeral container | `kubectl debug -it <pod> --image=busybox --target=<container>` |
| Debug by copying pod | `kubectl debug <pod> -it --copy-to=debug-pod --share-processes --image=busybox` |
| Debug node | `kubectl debug node/<node> -it --image=ubuntu` |
| Port forward | `kubectl port-forward <pod> 8080:80` |
| Check RBAC | `kubectl auth can-i <verb> <resource> --as=<user>` |

## Pod Failure Decision Tree

| Pod Status | Check | Common Causes | Resolution |
|---|---|---|---|
| **Pending** | `kubectl describe pod` -> Events | No nodes with enough resources, unbound PVCs, node affinity/taints | Scale nodes, fix PVC, adjust affinity/tolerations |
| **CrashLoopBackOff** | `kubectl logs --previous` | App crash, missing config/secrets, wrong command, OOM | Fix app code, add ConfigMap/Secret, adjust memory limits |
| **ImagePullBackOff** | `kubectl describe pod` -> Events | Wrong image name/tag, private registry auth, network issues | Fix image reference, create imagePullSecret |
| **OOMKilled** | `kubectl describe pod` -> Last State | Memory limit too low, memory leak | Increase memory limit or fix leak |
| **CreateContainerConfigError** | `kubectl describe pod` -> Events | Missing ConfigMap/Secret referenced in env/volume | Create missing ConfigMap/Secret |
| **Evicted** | `kubectl describe pod` -> Status | Node disk/memory pressure | Free node resources, adjust pod resource requests |
| **Terminating** (stuck) | `kubectl describe pod` -> check finalizers | Finalizers not removed, PVC deletion stuck | Remove finalizers: `kubectl patch pod <name> -p '{"metadata":{"finalizers":null}}'` |

## Domain-Specific Guides

| Topic | Reference | When to Use |
|-------|-----------|-------------|
| **Pod Debugging** | [pod_debugging.md](references/pod_debugging.md) | Pod failures, crashes, container issues, init containers |
| **Networking & Services** | [networking_debugging.md](references/networking_debugging.md) | Service connectivity, DNS, NetworkPolicy, Ingress, Gateway API |
| **Storage & PVC** | [storage_debugging.md](references/storage_debugging.md) | PVC binding, mount errors, StorageClass issues |
| **Node & Cluster** | [node_debugging.md](references/node_debugging.md) | Node NotReady, resource pressure, kubelet issues |
| **RBAC & Security** | [rbac_debugging.md](references/rbac_debugging.md) | Permission errors, ServiceAccount, PSA, policy violations |
| **Deployments & Workloads** | [workload_debugging.md](references/workload_debugging.md) | Rollout failures, HPA issues, CronJob/Job debugging |
| **Tools & Cheat Sheet** | [tools_and_cheatsheet.md](references/tools_and_cheatsheet.md) | k9s, stern, kubectx, comprehensive kubectl reference |

## Key Principles

- **Start broad, narrow down**: `get` -> `describe` -> `logs` -> `exec/debug`
- **Check events first**: Most scheduling/config issues surface in events
- **Use `--previous` for crashes**: Gets logs from the last terminated container
- **Ephemeral containers for distroless**: Use `kubectl debug` when the container has no shell
- **Isolate network layers**: Use `port-forward` to bypass Service/Ingress and test pods directly
- **Compare working vs broken**: `kubectl diff` and comparing describe output between working and failing resources
