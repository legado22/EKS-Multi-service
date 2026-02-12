# Multi-Service E-Commerce Platform on Amazon EKS

A production-ready, highly available multi-tenant e-commerce platform deployed on Amazon EKS using Terraform for infrastructure provisioning and Kubernetes for container orchestration.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Infrastructure Components](#infrastructure-components)
- [Getting Started](#getting-started)
- [Deployment](#deployment)
- [Monitoring & Observability](#monitoring--observability)
- [Security](#security)
- [Cost Optimization](#cost-optimization)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎯 Overview

This project demonstrates a real-world microservices architecture running on Amazon EKS, featuring:

- **5 Microservices**: Frontend, API Gateway, Product Catalog, Order Management, and User Service
- **3 Database Types**: RDS PostgreSQL, ElastiCache Redis, and DocumentDB
- **Infrastructure as Code**: Complete Terraform modules for reproducible deployments
- **High Availability**: Multi-AZ deployment across 3 availability zones
- **Auto-scaling**: Both horizontal pod autoscaling and cluster autoscaling
- **Full Observability**: Integrated monitoring, logging, and tracing

## 🏗️ Architecture

### High-Level Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  Application  │
                    │ Load Balancer │
                    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐   ┌──────────────┐
│   Frontend   │    │ API Gateway  │   │   Ingress    │
│   Service    │───▶│   Service    │   │  Controller  │
└──────────────┘    └──────┬───────┘   └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐   ┌──────────────┐
│   Product    │    │    Order     │   │     User     │
│   Catalog    │    │  Management  │   │   Service    │
│  (FastAPI)   │    │(Spring Boot) │   │     (Go)     │
└──────┬───────┘    └──────┬───────┘   └──────┬───────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐   ┌──────────────┐
│     RDS      │    │  DocumentDB  │   │     RDS      │
│  PostgreSQL  │    │  (MongoDB)   │   │  PostgreSQL  │
└──────────────┘    └──────┬───────┘   └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ ElastiCache  │
                    │    Redis     │
                    └──────────────┘
```

### Network Architecture
```
VPC (10.0.0.0/16)
│
├── Public Subnets (10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24)
│   ├── NAT Gateways
│   ├── Load Balancers
│   └── Bastion Hosts
│
├── Private Subnets - Application (10.0.10.0/24, 10.0.11.0/24, 10.0.12.0/24)
│   ├── EKS Worker Nodes
│   ├── Application Pods
│   └── Fargate Pods
│
└── Private Subnets - Database (10.0.20.0/24, 10.0.21.0/24, 10.0.22.0/24)
    ├── RDS PostgreSQL
    ├── ElastiCache Redis
    └── DocumentDB Cluster
```

## 🔧 Components

### Microservices

| Service | Technology | Purpose | Database |
|---------|-----------|---------|----------|
| **Frontend** | React/Next.js | Customer-facing UI | - |
| **API Gateway** | Node.js/Express | Backend-for-Frontend pattern | Redis (Cache) |
| **Product Catalog** | Python/FastAPI | Product management & search | PostgreSQL |
| **Order Management** | Java/Spring Boot | Order processing & fulfillment | DocumentDB |
| **User Service** | Go | Authentication & user profiles | PostgreSQL |

### Data Stores

- **Amazon RDS PostgreSQL 15**: Relational data for products and users
- **Amazon ElastiCache Redis 7.x**: Session management and application caching
- **Amazon DocumentDB 5.x**: Document storage for orders and audit logs

### Platform Services

- **AWS Load Balancer Controller**: Manages ALB/NLB for ingress
- **External DNS**: Automatic DNS record management
- **External Secrets Operator**: Syncs secrets from AWS Secrets Manager
- **Metrics Server**: Resource metrics for HPA
- **Cluster Autoscaler**: Node group scaling
- **Prometheus & Grafana**: Monitoring and visualization
- **FluentBit**: Log aggregation to CloudWatch

## 📦 Prerequisites

### Required Tools

- **Terraform** >= 1.6.0
- **kubectl** >= 1.28.0
- **AWS CLI** >= 2.13.0
- **Helm** >= 3.12.0
- **eksctl** (optional, for easier cluster management)

### AWS Account Requirements

- IAM user/role with sufficient permissions for:
  - VPC, EC2, EKS
  - RDS, ElastiCache, DocumentDB
  - IAM role creation
  - CloudWatch, Secrets Manager
- AWS account with appropriate service quotas

### Knowledge Prerequisites

- Basic understanding of Kubernetes concepts
- Familiarity with AWS services
- Terraform basics
- Container orchestration principles

## 📁 Project Structure
```
eks-multi-service/
│
├── terraform/                          # Infrastructure as Code
│   ├── modules/                        # Reusable Terraform modules
│   │   ├── vpc/                        # VPC, subnets, NAT gateways
│   │   ├── eks/                        # EKS cluster configuration
│   │   ├── rds/                        # RDS PostgreSQL setup
│   │   ├── elasticache/                # Redis cluster
│   │   ├── documentdb/                 # DocumentDB cluster
│   │   ├── iam/                        # IAM roles and policies
│   │   └── security-groups/            # Security group rules
│   │
│   ├── environments/                   # Environment-specific configs
│   │   ├── dev/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── terraform.tfvars
│   │   ├── staging/
│   │   └── prod/
│   │
│   ├── main.tf                         # Root module
│   ├── variables.tf                    # Input variables
│   ├── outputs.tf                      # Output values
│   ├── versions.tf                     # Provider versions
│   └── backend.tf                      # Remote state configuration
│
├── kubernetes/                         # Kubernetes manifests
│   ├── namespaces/                     # Namespace definitions
│   ├── deployments/                    # Application deployments
│   │   ├── frontend/
│   │   ├── api-gateway/
│   │   ├── product-service/
│   │   ├── order-service/
│   │   └── user-service/
│   ├── services/                       # Service definitions
│   ├── ingress/                        # Ingress rules
│   ├── configmaps/                     # Configuration data
│   ├── secrets/                        # Secret references (External Secrets)
│   ├── hpa/                            # Horizontal Pod Autoscalers
│   └── network-policies/               # Network security policies
│
├── helm-charts/                        # Helm chart configurations
│   ├── monitoring/                     # Prometheus & Grafana
│   ├── ingress-controller/             # AWS Load Balancer Controller
│   ├── external-secrets/               # External Secrets Operator
│   └── external-dns/                   # External DNS
│
├── scripts/                            # Automation scripts
│   ├── setup.sh                        # Initial setup script
│   ├── deploy.sh                       # Deployment automation
│   ├── destroy.sh                      # Cleanup script
│   └── validate.sh                     # Health check script
│
├── docs/                               # Documentation
│   ├── architecture.md                 # Detailed architecture
│   ├── deployment-guide.md             # Step-by-step deployment
│   ├── troubleshooting.md              # Common issues and solutions
│   └── best-practices.md               # Recommendations
│
├── .gitignore
├── README.md                           # This file
└── LICENSE
```

## 🏛️ Infrastructure Components

### Amazon EKS Cluster

- **Version**: 1.29 (or latest stable)
- **Node Groups**:
  - **General Purpose**: t3.medium (2-10 nodes, auto-scaling)
  - **Compute Optimized**: c5.large (1-5 nodes, for CPU-intensive workloads)
  - **Spot Instances**: Mixed instances for cost optimization
- **Fargate Profiles**: For stateless, burstable workloads
- **Add-ons**: VPC CNI, CoreDNS, kube-proxy, EBS CSI driver

### Networking

- **VPC CIDR**: 10.0.0.0/16
- **Subnets**:
  - 3x Public subnets (for load balancers)
  - 3x Private subnets (for applications)
  - 3x Private subnets (for databases)
- **NAT Gateways**: 3 (one per AZ for high availability)
- **VPC Endpoints**: S3, ECR, CloudWatch, Secrets Manager
- **Security Groups**: Least privilege access control

### Databases

#### RDS PostgreSQL
- **Engine**: PostgreSQL 15.x
- **Instance Class**: db.t3.medium (adjustable)
- **Multi-AZ**: Enabled
- **Backup**: Automated daily backups, 7-day retention
- **Encryption**: At-rest and in-transit

#### ElastiCache Redis
- **Engine**: Redis 7.x
- **Node Type**: cache.t3.medium
- **Cluster Mode**: Enabled with 3 shards
- **Replicas**: 1 replica per shard
- **Automatic Failover**: Enabled

#### DocumentDB
- **Engine**: MongoDB 5.0 compatible
- **Instance Class**: db.t3.medium
- **Cluster Size**: 1 primary + 2 replicas
- **Backup**: Continuous backup to S3
- **Encryption**: Enabled

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/eks-multi-service.git
cd eks-multi-service
```

### 2. Configure AWS Credentials
```bash
aws configure
# OR
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 3. Initialize Terraform Backend
```bash
cd terraform/environments/dev
terraform init
```

### 4. Review and Customize Variables

Edit `terraform.tfvars`:
```hcl
environment         = "dev"
region             = "us-east-1"
cluster_name       = "eks-ecommerce-dev"
cluster_version    = "1.29"
vpc_cidr           = "10.0.0.0/16"

# Node group configuration
node_group_desired = 3
node_group_min     = 2
node_group_max     = 10

# Database configuration
db_instance_class     = "db.t3.medium"
redis_node_type       = "cache.t3.medium"
documentdb_instance_class = "db.t3.medium"

# Tags
tags = {
  Environment = "dev"
  Project     = "ecommerce-platform"
  ManagedBy   = "terraform"
}
```

## 📤 Deployment

### Phase 1: Infrastructure Provisioning
```bash
# Navigate to environment directory
cd terraform/environments/dev

# Plan the deployment
terraform plan -out=tfplan

# Apply the infrastructure
terraform apply tfplan

# Save outputs
terraform output -json > outputs.json
```

### Phase 2: Configure kubectl
```bash
# Update kubeconfig
aws eks update-kubeconfig --name eks-ecommerce-dev --region us-east-1

# Verify connection
kubectl get nodes
kubectl get namespaces
```

### Phase 3: Install Platform Services
```bash
# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=eks-ecommerce-dev \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Install External DNS
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
helm install external-dns external-dns/external-dns \
  -n kube-system \
  -f helm-charts/external-dns/values.yaml

# Install External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace

# Install Monitoring Stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --create-namespace \
  -f helm-charts/monitoring/values.yaml
```

### Phase 4: Deploy Applications
```bash
# Create namespaces
kubectl apply -f kubernetes/namespaces/

# Deploy applications
kubectl apply -f kubernetes/deployments/
kubectl apply -f kubernetes/services/
kubectl apply -f kubernetes/ingress/

# Configure autoscaling
kubectl apply -f kubernetes/hpa/

# Verify deployments
kubectl get pods -n ecommerce
kubectl get svc -n ecommerce
kubectl get ingress -n ecommerce
```

## 📊 Monitoring & Observability

### Access Grafana Dashboard
```bash
# Port forward to Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Access at: http://localhost:3000
# Default credentials: admin / prom-operator
```

### Pre-configured Dashboards

- **Cluster Overview**: Overall cluster health and resource usage
- **Node Metrics**: Individual node performance
- **Pod Metrics**: Container-level resource consumption
- **Application Metrics**: Custom application metrics
- **Database Metrics**: RDS, Redis, and DocumentDB performance

### CloudWatch Container Insights
```bash
# View logs
aws logs tail /aws/containerinsights/eks-ecommerce-dev/application --follow

# View metrics in AWS Console
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#container-insights:
```

### Tracing with X-Ray

- X-Ray daemon runs as DaemonSet
- Automatic trace collection for instrumented applications
- View traces in AWS X-Ray console

## 🔒 Security

### IAM Roles for Service Accounts (IRSA)

Each microservice has dedicated IAM roles with least privilege:

- Product Service: RDS access only
- Order Service: DocumentDB and S3 access
- User Service: RDS and Secrets Manager access
- API Gateway: Redis and CloudWatch access

### Secrets Management

- **External Secrets Operator**: Syncs secrets from AWS Secrets Manager
- **Automatic Rotation**: Secrets rotated every 90 days
- **Encryption**: All secrets encrypted at rest with KMS

### Network Security

- **Security Groups**: Strict ingress/egress rules
- **Network Policies**: Pod-to-pod communication restrictions
- **Private Subnets**: Applications and databases not directly accessible
- **TLS/SSL**: All external communication encrypted

### Pod Security

- **Pod Security Standards**: Restricted policy enforced
- **Security Context**: Non-root containers, read-only file systems
- **Resource Limits**: CPU and memory limits prevent resource exhaustion
- **Image Scanning**: ECR scans for vulnerabilities

## 💰 Cost Optimization

### Estimated Monthly Costs (Dev Environment)

| Component | Configuration | Estimated Cost |
|-----------|--------------|----------------|
| EKS Cluster | Control Plane | $73 |
| EC2 Instances | 3x t3.medium | $90 |
| RDS PostgreSQL | db.t3.medium | $100 |
| ElastiCache Redis | cache.t3.medium x3 | $120 |
| DocumentDB | db.t3.medium x3 | $150 |
| NAT Gateways | 3x NAT Gateway | $100 |
| Load Balancers | 1x ALB | $20 |
| Data Transfer | ~100GB/month | $10 |
| **Total** | | **~$663/month** |

### Cost Optimization Strategies

1. **Use Spot Instances**: 60-90% savings on worker nodes
2. **Right-sizing**: Monitor and adjust instance sizes
3. **Auto-scaling**: Scale down during off-peak hours
4. **Reserved Instances**: 40-60% savings for production
5. **Fargate for Burst**: Pay only for actual usage
6. **S3 Lifecycle Policies**: Archive old logs and backups
7. **Single NAT Gateway**: Use one NAT Gateway in dev (not prod)

## 🔧 Troubleshooting

### Cluster Access Issues
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Update kubeconfig
aws eks update-kubeconfig --name eks-ecommerce-dev --region us-east-1

# Check IAM authenticator
kubectl get configmap -n kube-system aws-auth -o yaml
```

### Pod Scheduling Issues
```bash
# Check node capacity
kubectl describe nodes

# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Check resource quotas
kubectl get resourcequota -n <namespace>
```

### Database Connection Issues
```bash
# Test connectivity from pod
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql -h <rds-endpoint> -U admin -d productdb

# Check security groups
aws ec2 describe-security-groups --group-ids <sg-id>

# Verify secrets
kubectl get secret -n ecommerce db-credentials -o yaml
```

### Load Balancer Issues
```bash
# Check ALB controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Verify ingress
kubectl describe ingress -n ecommerce

# Check target groups in AWS Console
aws elbv2 describe-target-groups
```

## 📚 Additional Resources

- [AWS EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Terraform AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- AWS EKS team for comprehensive documentation
- Kubernetes community for amazing tools
- Terraform community for infrastructure patterns

---

**Note**: This is a reference architecture for learning and development. For production deployments, additional security hardening, disaster recovery planning, and compliance measures should be implemented.