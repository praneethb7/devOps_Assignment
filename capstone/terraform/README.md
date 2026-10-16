# AWS VPC and EKS

Status: configuration initialized, validated and tested with mocked providers. No real AWS plan, apply or destroy was run. The project owner selected code preparation without provisioning.

Architecture: a VPC with two public subnets, two private subnets across two availability zones, an internet gateway, one NAT gateway, separate route tables, EKS control plane and a managed worker group (desired 2, minimum 1, maximum 3). Worker nodes use private subnets. The EKS API supports private access and restricts public access to supplied trusted CIDRs. EKS access entries grant the supplied administrator principal cluster access. An OIDC role restricts the EBS CSI driver to its service account. An EBS CSI addon and encrypted gp3 StorageClass support PostgreSQL persistence.

## Validate without credentials or cloud costs

```bash
terraform init -backend=false
terraform fmt -check -recursive
terraform validate
terraform test
```

`terraform test` mocks providers; no AWS resources are created. Never present this output as a real AWS plan or deployment.

## Future AWS run

Only run after explicitly approving AWS provisioning and configuring an account. EKS control plane, EC2 workers, NAT gateway, public IPv4, CloudWatch and storage can incur charges.

```bash
aws sso login --profile <your-profile>
export AWS_PROFILE=<your-profile>
aws sts get-caller-identity
cp terraform.tfvars.example terraform.tfvars
# Edit the administrator IAM ARN and trusted public IP /32. Keep credentials out.
# Confirm that the selected Kubernetes version is supported in the account/region.
terraform init
terraform plan -out=deployment.tfplan
terraform apply deployment.tfplan
$(terraform output -raw configure_kubectl)
kubectl get nodes
kubectl apply -f ../k8s/storageclass-eks.yaml
```

The placeholder account number and documentation IP in the example must be replaced. No AWS credentials are embedded. Before using a shared environment, configure a remote encrypted state backend and locking; this standalone exercise defaults to ignored local state.

Install an Ingress controller for EKS and Metrics Server, then install the application chart with published image SHA tags and a DNS hostname you control. If GHCR packages remain private, create a registry Secret and configure imagePullSecrets (or make the demonstration packages public). Set up TLS through the Ingress values. This project does not configure a public DNS zone or certificate automatically.

Delete Ingress LoadBalancer services first so their AWS load balancers are removed. Remove application PVCs if no longer needed, then:

```bash
terraform plan -destroy
terraform destroy
```

Verify that the cluster, worker group, NAT gateway, EIP and disks were removed. The AWS Console and real destroy screenshots remain outstanding because no cloud provisioning was authorized.
