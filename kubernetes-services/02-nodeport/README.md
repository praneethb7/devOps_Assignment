# NodePort

A NodePort Service is a ClusterIP Service plus one extra thing: kube-proxy opens a port in the
30000–32767 range on **every** node in the cluster and forwards it to the Service. Anyone who
can reach any node's IP can reach the app at `<node-ip>:<nodePort>` — including on nodes that
are not running a single one of the Pods, which forward the traffic on.

## Manifest

[`web-nodeport.yaml`](web-nodeport.yaml) is the ClusterIP manifest with `type: NodePort` and a
fixed `nodePort: 30080`. Leaving `nodePort` out lets Kubernetes allocate one, which is what
you normally want — a hard-coded node port is a cluster-wide reservation and two Services
cannot share it.

```bash
kubectl apply -f 02-nodeport/web-nodeport.yaml
```

## What it got

```
### kubectl get svc web-nodeport -o wide
NAME           TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE   SELECTOR
web-nodeport   NodePort   10.105.220.99   <none>        8080:30080/TCP   5s    app=web
```

`PORT(S)` reads `8080:30080/TCP`, and that colon is the whole type: **8080 on the ClusterIP,
30080 on the node**. It still has a ClusterIP (`10.105.220.99`) — NodePort does not replace
ClusterIP, it adds to it.

## Three vantage points

```
### inside the cluster, like any ClusterIP
HTTP 200 via 10.105.220.99:8080

### from inside the node, on the node port
HTTP/1.1 200 OK

### from the laptop, straight at the node IP
HTTP 000
curl exit code: 28
```

```bash
kubectl exec client -- curl -s -o /dev/null -w "HTTP %{http_code} via %{remote_ip}:%{remote_port}\n" http://web-nodeport:8080
minikube ssh -- "curl -sI http://192.168.49.2:30080 | head -1"
curl -s -m 3 http://192.168.49.2:30080
```

The first two are the type working as designed. The third is not a NodePort failure: with the
Docker driver on macOS, `192.168.49.2` is an address inside Docker's Linux VM and the Mac has
no route to it. On a Linux host, or on a real cluster with a reachable node IP, that same curl
would return 200.

`minikube service` bridges the gap by opening a tunnel from localhost to the node port:

```
### minikube service web-nodeport --url
http://127.0.0.1:56891
! Because you are using a Docker driver on darwin, the terminal needs to be open to run it.

### through the minikube tunnel: http://127.0.0.1:56891
HTTP 200
<title>Welcome to nginx!</title>
```

The warning is worth heeding — the tunnel only lives as long as that command is running.

## Where it fits

NodePort is the honest, lowest-level way out of a cluster, and mostly a building block rather
than a destination. In production you rarely hand users a `:30080` URL; you put a LoadBalancer
or an Ingress controller in front, and both of those are sitting on a node port underneath.
