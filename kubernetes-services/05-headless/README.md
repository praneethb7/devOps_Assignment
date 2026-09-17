# Headless

Setting `clusterIP: None` turns off the virtual IP and kube-proxy altogether. The Service still
watches its selector and still maintains an EndpointSlice — but DNS answers a lookup of the
Service name with the **Pod IPs themselves**. The client connects straight to a Pod; nothing
load-balances in between.

## Manifests

[`web-headless.yaml`](web-headless.yaml) has no `type` line, just `clusterIP: None`.

[`web-statefulset.yaml`](web-statefulset.yaml) runs three Nginx replicas as a StatefulSet
labelled `app: web-stateful`, with `serviceName: web-headless`. That field is the reason this
folder uses a StatefulSet rather than reusing the shared Deployment: it is what makes CoreDNS
publish a DNS name per replica.

```bash
kubectl apply -f 05-headless/web-headless.yaml -f 05-headless/web-statefulset.yaml
```

```
### the StatefulSet Pods and their IPs
NAME             IP
web-stateful-0   10.244.0.8
web-stateful-1   10.244.0.9
web-stateful-2   10.244.0.10
```

Stable, ordinal names — `-0`, `-1`, `-2` — rather than a Deployment's random suffixes.

## No IP, but still endpoints

```
### kubectl get svc web-headless -o wide
NAME           TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)    AGE   SELECTOR
web-headless   ClusterIP   None         <none>        8080/TCP   17s   app=web-stateful

### endpointslices
NAME                 ADDRESSTYPE   PORTS   ENDPOINTS                           AGE
web-headless-vl7j5   IPv4          80      10.244.0.8,10.244.0.9,10.244.0.10   17s
```

`TYPE` still says `ClusterIP` — headless is not a separate type, it is a ClusterIP Service
that declined its IP. The EndpointSlice is identical in shape to the one in
[01-clusterip](../01-clusterip/); what changed is who consumes it. There, kube-proxy turned it
into forwarding rules. Here, CoreDNS turns it into A records.

## The one-line difference

```
### nslookup of the headless Service
Name:	web-headless.default.svc.cluster.local
Address: 10.244.0.9
Name:	web-headless.default.svc.cluster.local
Address: 10.244.0.8
Name:	web-headless.default.svc.cluster.local
Address: 10.244.0.10

### the same lookup against the ClusterIP Service, for comparison
Name:	web-clusterip.default.svc.cluster.local
Address: 10.96.6.96
```

Three Pod IPs versus one virtual IP. That is the entire concept. The client gets the full
list and picks — usually the first one its resolver hands back, which is why DNS round-robin
is a much weaker form of balancing than kube-proxy's.

## Per-Pod names

```
### per-Pod DNS names, which only a headless Service gives you
Name:	web-stateful-0.web-headless.default.svc.cluster.local
Address: 10.244.0.8
Name:	web-stateful-1.web-headless.default.svc.cluster.local
Address: 10.244.0.9
Name:	web-stateful-2.web-headless.default.svc.cluster.local
Address: 10.244.0.10
```

`<pod>.<service>.<namespace>.svc.cluster.local` — addressable individually, and the name
survives a restart even though the IP will not. This is what makes stateful clustering work:
a database replica can be told "your primary is `db-0.db`", a Kafka broker can advertise a
name its peers can dial, and a client that must talk to one specific member can.

## Connecting

```
### curl the headless name
HTTP 200 via 10.244.0.10:80

### curl one specific Pod by name
HTTP 200 via 10.244.0.9:80
```

```bash
kubectl exec client -- curl -s -o /dev/null -w "HTTP %{http_code} via %{remote_ip}:%{remote_port}\n" http://web-headless:80
kubectl exec client -- curl -s -o /dev/null -w "HTTP %{http_code} via %{remote_ip}:%{remote_port}\n" http://web-stateful-1.web-headless:80
```

Two things to notice. `remote_ip` is a **Pod** IP, not a Service IP — the opposite of the
ClusterIP result, and the clearest proof that nothing is proxying. And the port is `80`, not
the Service's `8080`: with no kube-proxy in the path there is nothing to remap ports, so the
client has to use the container's real port. The `port: 8080` field is not doing nothing —
it still populates SRV records — but it does not rewrite plain connections.
