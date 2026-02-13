# Node & Cluster Debugging Reference

## Node NotReady

```bash
# Check node status
kubectl get nodes
kubectl describe node <node-name>
# Look at Conditions section:
# - Ready: kubelet is healthy
# - MemoryPressure: node running out of memory
# - DiskPressure: node running out of disk
# - PIDPressure: too many processes
# - NetworkUnavailable: network not configured

# Check kubelet logs (SSH to node)
journalctl -u kubelet -f --lines=100
systemctl status kubelet
```

**Common causes:**
- kubelet stopped or crashed -> restart: `systemctl restart kubelet`
- Container runtime issues -> check: `systemctl status containerd`
- Certificate expired -> check kubelet logs for TLS errors
- Network partition -> check node can reach API server

## Resource Pressure and Evictions

```bash
# Check node resource usage
kubectl top nodes
kubectl describe node <name> | grep -A20 "Allocated resources"

# Check for eviction events
kubectl get events --field-selector reason=Evicted -A

# Check eviction thresholds
kubectl get node <name> -o yaml | grep -A10 eviction
```

**Eviction signals:**
- `memory.available` < 100Mi (default)
- `nodefs.available` < 10%
- `imagefs.available` < 15%

## Node Debugging with kubectl debug

```bash
# Create a privileged debugging pod on a specific node
kubectl debug node/<node-name> -it --image=ubuntu
# This creates a pod with hostPID, hostNetwork and mounts host root at /host

# Inside the debug pod:
chroot /host  # Get full access to host filesystem
journalctl -u kubelet --lines=50
crictl ps  # List containers via container runtime
crictl logs <container-id>
df -h  # Check disk usage
free -m  # Check memory
```

## Checking Node Capacity and Allocatable Resources

```bash
# Node capacity vs allocatable (allocatable = capacity - system reserved)
kubectl describe node <name> | grep -A6 "Capacity\|Allocatable"

# Compare allocated vs allocatable
kubectl describe node <name> | grep -A10 "Allocated resources"

# Quick overview of all nodes
kubectl get nodes -o custom-columns=\
NAME:.metadata.name,\
STATUS:.status.conditions[-1].type,\
CPU:.status.capacity.cpu,\
MEMORY:.status.capacity.memory
```

## Taints and Tolerations

```bash
# View node taints
kubectl describe node <name> | grep Taints

# Add a taint
kubectl taint nodes <name> key=value:NoSchedule

# Remove a taint
kubectl taint nodes <name> key-

# Common built-in taints:
# node.kubernetes.io/not-ready          - Node not ready
# node.kubernetes.io/unreachable        - Node unreachable from controller
# node.kubernetes.io/memory-pressure    - Node has memory pressure
# node.kubernetes.io/disk-pressure      - Node has disk pressure
# node.kubernetes.io/pid-pressure       - Node has PID pressure
# node.kubernetes.io/unschedulable      - Node is cordoned
```

## Cordon, Drain, and Maintenance

```bash
# Prevent new pods from being scheduled (mark unschedulable)
kubectl cordon <node-name>

# Safely evict all pods (respects PDBs)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data

# Re-enable scheduling
kubectl uncordon <node-name>

# If drain is stuck, check PodDisruptionBudgets:
kubectl get pdb -A
kubectl describe pdb <name> -n <namespace>
```
