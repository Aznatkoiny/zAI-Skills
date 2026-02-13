# Debugging Tools & kubectl Cheat Sheet

## Modern Debugging Tools

### k9s - Terminal UI for Kubernetes
```bash
# Install
brew install derailed/k9s/k9s  # macOS
# or: curl -sS https://webinstall.dev/k9s | bash

# Usage
k9s                    # Launch with current context
k9s -n <namespace>     # Start in specific namespace
k9s --context <ctx>    # Use specific context

# Key commands inside k9s:
# :pods          - View pods
# :svc           - View services
# :deploy        - View deployments
# :events        - View events
# :ns            - Switch namespace
# /              - Filter resources
# d              - Describe selected resource
# l              - View logs
# s              - Shell into container
# ctrl-d         - Delete resource
# y              - View YAML
```

### stern - Multi-Pod Log Tailing
```bash
# Install
brew install stern  # macOS

# Usage
stern <pod-name-pattern> -n <namespace>         # Tail logs matching pattern
stern . -n <namespace>                            # All pods in namespace
stern <pattern> -n <namespace> --since 10m       # Last 10 minutes
stern <pattern> -n <namespace> -c <container>    # Specific container
stern <pattern> -n <namespace> --exclude="health" # Exclude lines
stern <pattern> -n <namespace> -o json           # JSON output

# stern vs kubectl logs:
# - stern: regex pod matching, multi-pod, color-coded, follows new pods
# - kubectl logs: single pod (or -l label), no color, no auto-follow new pods
```

### kubectx / kubens - Fast Context and Namespace Switching
```bash
# Install
brew install kubectx  # macOS (includes kubens)

kubectx                 # List contexts
kubectx <context-name>  # Switch context
kubectx -                # Switch to previous context

kubens                  # List namespaces
kubens <namespace>      # Switch default namespace
kubens -                # Switch to previous namespace
```

### Other Useful Tools
```bash
# kubecolor - Colorized kubectl output
brew install kubecolor
alias kubectl=kubecolor

# kubectl-tree - Show resource ownership hierarchy
kubectl krew install tree
kubectl tree deployment <name>

# kubectl-neat - Clean up kubectl output (remove managed fields)
kubectl krew install neat
kubectl get pod <name> -o yaml | kubectl neat

# kube-capacity - Show node resource usage summary
kubectl krew install resource-capacity
kubectl resource-capacity --util
```

## Comprehensive kubectl Debugging Cheat Sheet

### Inspecting Resources
```bash
kubectl get <resource> -o wide                    # Extra columns (node, IP)
kubectl get <resource> -o yaml                    # Full YAML
kubectl get <resource> -o json                    # Full JSON
kubectl get <resource> -o jsonpath='{.spec.x}'    # Extract specific field
kubectl get <resource> --show-labels               # Show labels
kubectl get <resource> -l key=value               # Filter by label
kubectl get <resource> -A                          # All namespaces
kubectl get <resource> --sort-by=.metadata.creationTimestamp  # Sort
kubectl describe <resource> <name>                 # Human-readable details + events
kubectl diff -f <file>                             # Show diff before applying
```

### Reading Logs
```bash
kubectl logs <pod>                                # Current container log
kubectl logs <pod> --previous                     # Previous (crashed) container
kubectl logs <pod> -c <container>                 # Specific container
kubectl logs <pod> --all-containers               # All containers
kubectl logs -f <pod>                             # Follow/stream
kubectl logs <pod> --since=1h                     # Last hour
kubectl logs <pod> --since-time=2024-01-01T00:00:00Z  # Since timestamp
kubectl logs <pod> --tail=100                     # Last 100 lines
kubectl logs -l app=<label> --all-containers      # All pods with label
kubectl logs job/<job-name>                        # Job logs
```

### Executing & Debugging
```bash
kubectl exec -it <pod> -- /bin/sh                 # Interactive shell
kubectl exec -it <pod> -c <container> -- /bin/sh  # Specific container
kubectl exec <pod> -- <command>                    # Run single command
kubectl debug -it <pod> --image=busybox --target=<container>  # Ephemeral container
kubectl debug <pod> -it --copy-to=dbg --share-processes --image=ubuntu  # Copy pod
kubectl debug node/<node> -it --image=ubuntu      # Debug node
kubectl cp <pod>:<path> <local-path>              # Copy file from pod
kubectl cp <local-path> <pod>:<path>              # Copy file to pod
```

### Network Debugging
```bash
kubectl get endpoints <svc>                        # Service endpoints
kubectl get svc <name> -o wide                     # Service details
kubectl port-forward pod/<pod> <local>:<remote>    # Forward to pod
kubectl port-forward svc/<svc> <local>:<remote>    # Forward to service
kubectl run tmp --rm -it --image=nicolaka/netshoot --restart=Never -- bash  # Network debug pod
# Inside netshoot: curl, dig, nslookup, tcpdump, ping, traceroute, nmap
```

### Events & Monitoring
```bash
kubectl get events -n <ns> --sort-by=.lastTimestamp                     # Recent events
kubectl get events --field-selector involvedObject.name=<name>          # Events for resource
kubectl get events --field-selector type=Warning                        # Warning events only
kubectl get events --field-selector reason=Failed                       # Failed events
kubectl top pods -n <ns>                                                 # Pod CPU/memory
kubectl top pods -n <ns> --sort-by=memory                               # Sort by memory
kubectl top nodes                                                        # Node resource usage
```

### RBAC
```bash
kubectl auth can-i <verb> <resource> -n <ns>                            # Check permission
kubectl auth can-i <verb> <resource> --as=system:serviceaccount:<ns>:<sa>  # Check as SA
kubectl auth can-i --list -n <ns>                                       # List all permissions
kubectl auth whoami                                                      # Current identity (v1.29+)
kubectl create token <sa-name> -n <ns>                                  # Create SA token
```

### Resource Management
```bash
kubectl get resourcequota -n <ns>                  # View quotas
kubectl describe resourcequota -n <ns>             # Quota details with usage
kubectl get limitrange -n <ns>                     # View limit ranges
kubectl get priorityclass                          # Pod priority classes
```

### Quick Troubleshooting Combos
```bash
# "Why won't my pod start?"
kubectl get pod <pod> -o wide && kubectl describe pod <pod> | tail -20

# "Why is my service not reachable?"
kubectl get endpoints <svc> && kubectl get pods -l <selector> -o wide

# "What's using all the resources?"
kubectl top pods --sort-by=cpu -A | head -20
kubectl top pods --sort-by=memory -A | head -20

# "What happened recently?"
kubectl get events -A --sort-by=.lastTimestamp | tail -30

# "Show me everything about this deployment"
kubectl get deploy,rs,pods -l app=<label> -o wide -n <namespace>
```
