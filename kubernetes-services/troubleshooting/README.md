# Troubleshooting: the empty EndpointSlice

The single most common Service failure is not a Service failure at all: the selector does not
match the Pods, so the Service exists, has an IP, resolves in DNS, and routes to nothing.

[`empty-endpoints.yaml`](empty-endpoints.yaml) is a ClusterIP Service selecting
`app: web-backend`, while the Pods running in the cluster are labelled `app: web`.

```bash
kubectl apply -f troubleshooting/empty-endpoints.yaml
```

## The symptom

```
### kubectl get svc broken-service -o wide
NAME             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE   SELECTOR
broken-service   ClusterIP   10.109.27.214   <none>        8080/TCP   5s    app=web-backend

### kubectl get endpointslices -l kubernetes.io/service-name=broken-service
NAME                   ADDRESSTYPE   PORTS     ENDPOINTS   AGE
broken-service-ml5ph   IPv4          <unset>   <unset>     5s

### kubectl describe svc broken-service
Selector:                 app=web-backend
IP:                       10.109.27.214
TargetPort:               http/TCP
Endpoints:
```

The Service looks healthy from every angle a beginner checks. It has a ClusterIP. `kubectl get
svc` reports nothing unusual. Only the endpoints give it away: an EndpointSlice with `<unset>`
ports and no addresses, and an `Endpoints:` line in `describe` with nothing after it.

What a client sees:

```
### what a client sees
HTTP 000
curl exit code: 7 (7 = could not connect)
```

Exit code 7, not a DNS failure — the name resolved fine. kube-proxy simply has no endpoint to
forward to, so the connection is refused immediately. A `Connection refused` against a Service
that resolves is almost always this.

## The diagnosis

Compare the two labels directly:

```
### the labels the Pods actually carry
web-7c9cd446bb-2pncn app=web,pod-template-hash=7c9cd446bb
web-7c9cd446bb-kcprj app=web,pod-template-hash=7c9cd446bb
web-7c9cd446bb-sbpvl app=web,pod-template-hash=7c9cd446bb
```

`app=web` on the Pods, `app=web-backend` in the selector. Nothing matches, so the endpoint
controller has nothing to write.

## The fix

```
### fix it and look again
service/broken-service patched
NAME                   ADDRESSTYPE   PORTS   ENDPOINTS                          AGE
broken-service-ml5ph   IPv4          80      10.244.0.3,10.244.0.6,10.244.0.5   8s
HTTP 200
```

```bash
kubectl patch svc broken-service -p '{"spec":{"selector":{"app":"web"}}}'
```

Endpoints appear within seconds of the selector matching — the controller is watching, and no
restart of anything is needed.

## The checklist

When a Service does not answer, in this order:

1. `kubectl get endpointslices -l kubernetes.io/service-name=<svc>` — empty means it is a
   **selector or readiness** problem, not a networking one.
2. If it is empty: does the selector match the Pod labels (`kubectl get pods --show-labels`),
   and are the Pods actually `Ready`? An unready Pod is deliberately left out of the endpoint
   list, which is the mechanism that makes readiness probes useful.
3. If it is *not* empty and connections still fail: check `targetPort` against the port the
   container really listens on — the Service will happily forward to a closed port.
4. If the name does not resolve at all, it is DNS, not the Service: check CoreDNS with
   `kubectl get pods -n kube-system -l k8s-app=kube-dns`.
