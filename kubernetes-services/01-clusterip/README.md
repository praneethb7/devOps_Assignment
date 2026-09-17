# ClusterIP

The default type, and the one every other type is built on. Kubernetes allocates a virtual IP
out of the Service CIDR, and kube-proxy programs the node so packets sent to that IP and port
are rewritten to one of the matching Pod IPs. The virtual IP is not assigned to any interface
anywhere — it exists only as forwarding rules inside the cluster, which is exactly why nothing
outside can route to it.

Use it for anything only other Pods need to call: a backend behind a frontend, a cache, an
internal API, a database.

## Manifest

[`web-clusterip.yaml`](web-clusterip.yaml) selects `app: web`, listens on `8080`, and forwards
to the Pods' named `http` port (80). The two ports differ on purpose — `port` is the front
door clients dial, `targetPort` is where the container actually listens.

```bash
kubectl apply -f 01-clusterip/web-clusterip.yaml
```

## The Service and its endpoints

```
### kubectl get svc web-clusterip -o wide
NAME            TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)    AGE   SELECTOR
web-clusterip   ClusterIP   10.96.6.96   <none>        8080/TCP   25s   app=web

### kubectl get endpointslices -l kubernetes.io/service-name=web-clusterip
NAME                  ADDRESSTYPE   PORTS   ENDPOINTS                          AGE
web-clusterip-2ssjv   IPv4          80      10.244.0.3,10.244.0.5,10.244.0.6   25s
```

The Service got `10.96.6.96`. Its EndpointSlice lists all three Pod IPs on port 80 — the
selector matched, and the controller resolved the *named* `targetPort: http` to the number 80.

## Reaching it from inside the cluster

All three of the assignment's addressing styles, from the `client` Pod:

```
### curl by short name
HTTP 200 via 10.96.6.96:8080

### curl by FQDN
<title>Welcome to nginx!</title>

### curl by ClusterIP (10.96.6.96)
HTTP 200 via 10.96.6.96:8080
```

```bash
kubectl exec client -- curl -s -o /dev/null -w "HTTP %{http_code} via %{remote_ip}:%{remote_port}\n" http://web-clusterip:8080
kubectl exec client -- curl -s http://web-clusterip.default.svc.cluster.local:8080 | grep -o "<title>.*</title>"
kubectl exec client -- curl -s -o /dev/null -w "HTTP %{http_code} via %{remote_ip}:%{remote_port}\n" http://10.96.6.96:8080
```

Note what `%{remote_ip}` reports: `10.96.6.96`, the virtual IP — never a Pod IP. As far as
curl is concerned it opened a connection to the Service and that is where it stayed. The
rewrite to a real Pod happens in the kernel, below the client.

DNS confirms the short name and the VIP are the same thing:

```
### nslookup from the dns Pod
Server:		10.96.0.10
Address:	10.96.0.10:53

Name:	web-clusterip.default.svc.cluster.local
Address: 10.96.6.96
```

## Load balancing is real

Since curl always reports the VIP, the way to see which Pod served a request is to look at
the Pods. Thirty requests to the Service, counted in each Pod's access log:

```
### 30 requests to the Service, counted per Pod (delta over the run)
web-7c9cd446bb-2pncn     13 requests
web-7c9cd446bb-kcprj     13 requests
web-7c9cd446bb-sbpvl      4 requests
```

```bash
kubectl exec client -- sh -c 'for i in $(seq 1 30); do curl -s -o /dev/null http://web-clusterip:8080; done'
kubectl logs <pod> | grep -c 'GET /'
```

Spread across all three, but not evenly. kube-proxy picks an endpoint at random per
connection; it is a Layer 4 coin flip, not a round robin, so over thirty requests the split
is lumpy. That is expected and worth knowing before someone files a bug about it.

## From the laptop: two ways, one of which fails

```
### from the laptop
curl exit code: 28 (28 = timed out)
```

```bash
curl -s -m 3 http://10.96.6.96:8080
```

That timeout is the whole point of ClusterIP. The address is meaningful only where kube-proxy
has installed rules for it, and the laptop is outside the cluster. (With the Docker driver on
macOS the Pod and Service networks live inside Docker's VM, so even the node network is out of
reach.)

For debugging, `port-forward` tunnels through the API server instead:

```
### kubectl port-forward svc/web-clusterip 8080:8080
Forwarding from 127.0.0.1:8080 -> 80
Forwarding from [::1]:8080 -> 80

### curl http://localhost:8080 from the laptop
HTTP 200
<title>Welcome to nginx!</title>
```

Worth reading the arrow carefully: `127.0.0.1:8080 -> 80`. `port-forward` on a Service resolves
the Service's endpoints and forwards to a *Pod's* port 80 — it does not go through the virtual
IP at all, so it proves the Pods work, not that the Service does. Use it as a developer
convenience, not as a test of the Service.
