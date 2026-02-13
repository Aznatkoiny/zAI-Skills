# Storage & PVC Debugging Reference

## PVC Not Binding

```bash
kubectl get pvc -n <namespace>
kubectl describe pvc <name> -n <namespace>
# Check Events section for binding errors
```

**Common causes:**
- **No matching PV**: StorageClass doesn't have a provisioner or no PV matches access mode/size
  ```bash
  kubectl get pv
  kubectl get storageclass
  ```
- **StorageClass doesn't exist**: PVC references a non-existent StorageClass
  ```bash
  kubectl get storageclass
  # Check default: kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'
  ```
- **Access mode mismatch**: PVC requests ReadWriteMany but PV only supports ReadWriteOnce
- **Capacity mismatch**: PV is smaller than PVC request
- **Volume already bound**: PV is bound to another PVC

## Volume Mount Errors

```bash
kubectl describe pod <pod> -n <namespace>
# Look for: "Unable to attach or mount volumes"
```

**Multi-Attach Error**: Volume already attached to another node (common with EBS/Azure Disk)
```bash
# Find which node has the volume
kubectl get volumeattachment
# Force detach if needed (may cause data corruption!)
kubectl delete volumeattachment <name>
```

**Permission Denied on Mount**:
```bash
# Check SecurityContext fsGroup
# Pod spec should include:
# securityContext:
#   fsGroup: <gid>
# This changes ownership of volume files to the specified group
```

**Stale Volume Attachment** (pod deleted but volume stuck):
```bash
kubectl get volumeattachment
# Delete stale attachment
kubectl delete volumeattachment <name>
```

## StorageClass Issues

```bash
# List StorageClasses and their provisioners
kubectl get storageclass -o wide

# Check provisioner pod is running
kubectl get pods -n kube-system | grep provisioner
kubectl logs -n kube-system <provisioner-pod>

# Common issues:
# - Provisioner not running: check provisioner pods in kube-system
# - Wrong parameters: check StorageClass parameters match cloud provider requirements
# - Quota exceeded: check cloud provider volume quotas
```

## Debugging PV/PVC Lifecycle

```bash
# PVC lifecycle: Pending -> Bound -> Released -> (Available | Failed)
kubectl get pv
# STATUS column shows current phase

# Reclaim policy determines what happens when PVC is deleted:
# - Retain: PV keeps data, must be manually cleaned
# - Delete: PV and underlying storage are deleted
# - Recycle: (deprecated) basic rm -rf on volume

# To reuse a Released PV, remove the claimRef:
kubectl patch pv <pv-name> -p '{"spec":{"claimRef": null}}'
```

## Common Volume Types Debugging

### emptyDir Issues
- Lives only as long as the pod; lost on pod restart
- Check if `sizeLimit` is set and being exceeded

### ConfigMap/Secret Volume Issues
```bash
# Verify the ConfigMap/Secret exists and has expected keys
kubectl get configmap <name> -n <namespace> -o yaml
kubectl get secret <name> -n <namespace> -o yaml

# Check mount path doesn't conflict with existing directories
# ConfigMap/Secret volumes overlay the entire directory by default
# Use subPath to mount individual keys without replacing directory contents
```

### hostPath Issues
- Requires node access; won't work across nodes
- Check permissions on the host path
- PodSecurityStandards may block hostPath mounts
