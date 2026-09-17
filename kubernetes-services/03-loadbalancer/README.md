# LoadBalancer

`type: LoadBalancer` is how a Service gets a public address on a cloud provider. Kubernetes
creates the ClusterIP and the NodePort exactly as before, then asks the cloud controller
manager for a load balancer that forwards to that node port on every node. On AWS that is an
NLB or ELB, on GCP a forwarding rule, on Azure a Load Balancer resource.

The key point is that it is **additive**: all three layers exist at once, and the ones
underneath keep working whether or not the top one is ever fulfilled.

## Manifest

[`web-loadbalancer.yaml`](web-loadbalancer.yaml): same selector and ports, `type: LoadBalancer`.
No `nodePort` is given, so Kubernetes allocates one.

```bash
kubectl apply -f 03-loadbalancer/web-loadbalancer.yaml
```

## Pending, on purpose

```
### kubectl get svc web-loadbalancer -o wide   (20s after apply)
NAME               TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE   SELECTOR
web-loadbalancer   LoadBalancer   10.107.154.114   <pending>     8080:32378/TCP   20s   app=web

### what it actually got
type=LoadBalancer clusterIP=10.107.154.114 nodePort=32378 externalIPs=
```

`EXTERNAL-IP` is `<pending>` and will stay that way forever. Minikube has no cloud controller
manager, so nothing is listening for the request Kubernetes just made. This is not an error
and not a misconfiguration — it is what `type: LoadBalancer` looks like on any cluster without
a provider integration, and recognising it saves an afternoon of debugging.

Everything underneath was still created and still works:

```
### inside the cluster
HTTP 200 via 10.107.154.114:8080

### inside the node, on the node port it was given (32378)
HTTP/1.1 200 OK
```

```bash
kubectl exec client -- curl -s -o /dev/null -w "HTTP %{http_code} via %{remote_ip}:%{remote_port}\n" http://web-loadbalancer:8080
minikube ssh -- "curl -sI http://192.168.49.2:32378 | head -1"
```

Compare with [02-nodeport](../02-nodeport/): identical behaviour, and the node port here was
auto-allocated as `32378` rather than pinned. The three layers, bottom to top, are ClusterIP →
NodePort → cloud load balancer, and only the third one is missing.

The same tunnel trick reaches it from the laptop:

```
### minikube service web-loadbalancer --url
http://127.0.0.1:56934

### through the tunnel: http://127.0.0.1:56934
HTTP 200
```

`minikube tunnel`, run in a second terminal with `sudo`, goes one step further and assigns a
real `EXTERNAL-IP` by faking the cloud provider. It was not needed to show the point here.

## Where it fits

One `type: LoadBalancer` Service means one cloud load balancer, billed per hour, per Service.
That is why real clusters usually have exactly one — in front of an Ingress controller — and
route everything else through it by hostname and path, rather than giving every microservice
its own.
