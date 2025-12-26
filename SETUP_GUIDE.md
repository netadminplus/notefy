# Notefy Complete Setup Guide

This guide provides step-by-step instructions to deploy Notefy from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Server Preparation](#server-preparation)
4. [Kubernetes Cluster Setup](#kubernetes-cluster-setup)
5. [DNS Configuration](#dns-configuration)
6. [Secrets Management](#secrets-management)
7. [GitHub Configuration](#github-configuration)
8. [ArgoCD Deployment](#argocd-deployment)
9. [First Deployment](#first-deployment)
10. [Verification](#verification)
11. [Post-Deployment](#post-deployment)

---

## Prerequisites

### For Local Development (macOS)
- macOS 12+ (Monterey or later)
- 8GB+ RAM
- 20GB+ free disk space
- Admin/sudo access

### For Production Server
- Ubuntu 22.04 LTS
- 4+ CPU cores
- 8GB+ RAM
- 50GB+ SSD storage
- Public IP address
- Root or sudo access

### Required Accounts
- GitHub account
- Docker Hub account
- Domain name (e.g., ramtiin.ir)
- Telegram Bot (optional, for notifications)

---

## Local Development Setup

### Step 1: Install Development Tools

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11
brew install python@3.11

# Install Docker Desktop
brew install --cask docker

# Start Docker Desktop from Applications

# Install kubectl
brew install kubectl

# Install Helm
brew install helm

# Verify installations
python3.11 --version  # Should show 3.11.x
docker --version      # Should show Docker version
kubectl version --client
helm version
```

### Step 2: Clone and Setup Project

```bash
# Clone repository
git clone https://github.com/netadminplus/notefy.git
cd notefy

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Run Locally

```bash
# Start services with Docker Compose
docker-compose up -d

# Wait for services to start (30 seconds)
sleep 30

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app

# Access application
open http://localhost:5000

# Access Grafana
open http://localhost:3000
# Login: admin / admin

# Access Prometheus
open http://localhost:9090
```

### Step 4: Run Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html

# Run integration tests
pytest tests/integration/ -v

# Run all tests
pytest -v
```

### Step 5: Code Quality Checks

```bash
# Format code with Black
black .

# Check linting with Flake8
flake8 app/

# Run Pylint
pylint app/ --fail-under=7.0
```

### Step 6: Load Testing

```bash
# Install Locust (if not installed)
pip install locust

# Run load test with web UI
locust -f tests/load/test_locust.py --host=http://localhost:5000

# Open browser to http://localhost:8089
# Set users: 50, spawn rate: 5, duration: 2m

# Or run headless
locust -f tests/load/test_locust.py \
  --host=http://localhost:5000 \
  --users=50 \
  --spawn-rate=5 \
  --run-time=2m \
  --headless
```

---

## Server Preparation

### Step 1: Initial Server Setup

```bash
# SSH into your Ubuntu server
ssh root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y

# Install basic tools
apt install -y curl git vim htop net-tools

# Create non-root user (recommended)
adduser devops
usermod -aG sudo devops

# Switch to new user
su - devops
```

### Step 2: Configure Firewall

```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow K3s (6443)
sudo ufw allow 6443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Step 3: Configure DNS (Before proceeding)

**Important**: Configure DNS before installing SSL certificates

Go to your DNS provider and add these A records:

```
Record Type: A
Name                           Value
----                           -----
notefy.ramtiin.ir             YOUR_SERVER_IP
staging-notefy.ramtiin.ir     YOUR_SERVER_IP
grafana.ramtiin.ir            YOUR_SERVER_IP
prometheus.ramtiin.ir         YOUR_SERVER_IP
argocd.ramtiin.ir             YOUR_SERVER_IP
```

Wait 5-10 minutes for DNS propagation, then verify:

```bash
# Check DNS resolution
dig notefy.ramtiin.ir
dig staging-notefy.ramtiin.ir
dig grafana.ramtiin.ir

# Or use nslookup
nslookup notefy.ramtiin.ir
```

---

## Kubernetes Cluster Setup

### Step 1: Install K3s

```bash
# Clone the repository
git clone https://github.com/netadminplus/notefy.git
cd notefy

# Make setup script executable
chmod +x scripts/setup-k3s.sh

# Run setup script
sudo ./scripts/setup-k3s.sh
```

This script will:
- Install K3s (lightweight Kubernetes)
- Install Nginx Ingress Controller
- Install cert-manager for SSL
- Create Let's Encrypt ClusterIssuer
- Install ArgoCD
- Install Prometheus + Grafana monitoring stack
- Install Loki for log aggregation
- Create production and staging namespaces

The script takes about 10-15 minutes to complete.

### Step 2: Verify K3s Installation

```bash
# Check K3s is running
sudo systemctl status k3s

# Configure kubectl for non-root user
mkdir -p $HOME/.kube
sudo cp /etc/rancher/k3s/k3s.yaml $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
export KUBECONFIG=$HOME/.kube/config
echo "export KUBECONFIG=$HOME/.kube/config" >> ~/.bashrc

# Verify cluster
kubectl get nodes
kubectl get pods -A

# Should see pods running in:
# - kube-system
# - ingress-nginx
# - cert-manager
# - argocd
# - monitoring
```

### Step 3: Get ArgoCD Password

```bash
# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# Save this password! You'll need it to login to ArgoCD
echo "ArgoCD Password: $(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d)"
```

---

## Secrets Management

### Step 1: Create PostgreSQL Secrets

```bash
# Production database secret
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_DB=notefy_prod \
  --from-literal=POSTGRES_USER=notefy \
  --from-literal=POSTGRES_PASSWORD=$(openssl rand -base64 32) \
  -n production

# Staging database secret
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_DB=notefy_staging \
  --from-literal=POSTGRES_USER=notefy \
  --from-literal=POSTGRES_PASSWORD=$(openssl rand -base64 32) \
  -n staging

# Verify secrets
kubectl get secrets -n production
kubectl get secrets -n staging
```

### Step 2: Create Telegram Secrets (Optional)

First, create a Telegram bot:

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow instructions
3. Save the bot token
4. Send a message to your bot
5. Get your chat ID: `https://api.telegram.org/bot<TOKEN>/getUpdates`

```bash
# Create Telegram secrets
kubectl create secret generic telegram-secret \
  --from-literal=TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN \
  --from-literal=TELEGRAM_CHAT_ID=YOUR_CHAT_ID \
  -n production

kubectl create secret generic telegram-secret \
  --from-literal=TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN \
  --from-literal=TELEGRAM_CHAT_ID=YOUR_CHAT_ID \
  -n staging

# Verify
kubectl get secret telegram-secret -n production
```

---

## GitHub Configuration

### Step 1: Fork/Create Repository

```bash
# If you cloned, update remote
cd notefy
git remote set-url origin https://github.com/YOUR_USERNAME/notefy.git

# Or create new repository on GitHub and push
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/notefy.git
git push -u origin main

# Create staging branch
git checkout -b staging
git push -u origin staging
```

### Step 2: Configure GitHub Secrets

Go to your GitHub repository:
1. Click **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**

Add these secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `DOCKER_USERNAME` | your_dockerhub_username | Docker Hub username |
| `DOCKER_PASSWORD` | your_dockerhub_password | Docker Hub password or token |
| `TELEGRAM_BOT_TOKEN` | your_bot_token | From @BotFather (optional) |
| `TELEGRAM_CHAT_ID` | your_chat_id | Your Telegram chat ID (optional) |

### Step 3: Create GitHub Environments

1. Go to **Settings** → **Environments**
2. Click **New environment**

Create two environments:

**Staging Environment:**
- Name: `staging`
- Protection rules: None (auto-deploy)

**Production Environment:**
- Name: `production`
- Protection rules:
  - ☑ Required reviewers (add yourself)
  - ☑ Wait timer: 5 minutes (optional)

---

## ArgoCD Deployment

### Step 1: Access ArgoCD

```bash
# Port forward ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# On your local machine, create SSH tunnel
ssh -L 8080:localhost:8080 devops@YOUR_SERVER_IP

# Open browser to: https://localhost:8080
# Username: admin
# Password: (from earlier step)
```

### Step 2: Configure ArgoCD

```bash
# Install ArgoCD CLI
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo chmod +x /usr/local/bin/argocd

# Login to ArgoCD
argocd login localhost:8080 --username admin --password YOUR_PASSWORD --insecure

# Change admin password
argocd account update-password
```

### Step 3: Apply ArgoCD Applications

```bash
# Update repository URL in ArgoCD manifests
cd ~/notefy
sed -i 's|netadminplus|YOUR_GITHUB_USERNAME|g' argocd/application-prod.yaml
sed -i 's|netadminplus|YOUR_GITHUB_USERNAME|g' argocd/application-staging.yaml

# Apply applications
kubectl apply -f argocd/application-prod.yaml
kubectl apply -f argocd/application-staging.yaml

# Verify applications
argocd app list

# Watch sync status
argocd app get notefy-production
argocd app get notefy-staging
```

### Step 4: Apply Ingress for Services

```bash
# Apply monitoring ingress
kubectl apply -f monitoring/ingress.yaml

# Apply ArgoCD ingress
kubectl apply -f argocd/argocd-ingress.yaml

# Wait for certificates to be issued (2-3 minutes)
kubectl get certificate -n production
kubectl get certificate -n staging
kubectl get certificate -n monitoring
kubectl get certificate -n argocd

# All should show READY=True
```

---

## First Deployment

### Step 1: Build and Push Initial Image

On your local machine:

```bash
# Login to Docker Hub
docker login

# Build image
docker build -t YOUR_DOCKERHUB_USERNAME/notefy:production-latest .
docker build -t YOUR_DOCKERHUB_USERNAME/notefy:staging-latest .

# Push images
docker push YOUR_DOCKERHUB_USERNAME/notefy:production-latest
docker push YOUR_DOCKERHUB_USERNAME/notefy:staging-latest
```

### Step 2: Trigger Initial Sync

```bash
# SSH back to server
ssh devops@YOUR_SERVER_IP

# Sync ArgoCD applications
argocd app sync notefy-production
argocd app sync notefy-staging

# Watch deployment
kubectl get pods -n production -w
kubectl get pods -n staging -w

# Wait for all pods to be Running (2-3 minutes)
```

### Step 3: Trigger CI/CD Pipeline

On your local machine:

```bash
# Make a small change
echo "# Notefy - DevOps Excellence" > README.md

# Commit and push to staging
git checkout staging
git add README.md
git commit -m "Initial deployment to staging"
git push origin staging

# Watch GitHub Actions
# Go to: https://github.com/YOUR_USERNAME/notefy/actions

# After staging succeeds, push to production
git checkout main
git merge staging
git push origin main

# Approve production deployment in GitHub Actions
```

---

## Verification

### Step 1: Check All Services

```bash
# Check pods in all namespaces
kubectl get pods -n production
kubectl get pods -n staging
kubectl get pods -n monitoring
kubectl get pods -n argocd

# All pods should be Running

# Check ingress
kubectl get ingress -A

# All should have ADDRESS assigned
```

### Step 2: Test Endpoints

```bash
# Test production
curl -f https://notefy.ramtiin.ir/health
curl -f https://notefy.ramtiin.ir/metrics

# Test staging
curl -f https://staging-notefy.ramtiin.ir/health

# Test monitoring
curl -f https://grafana.ramtiin.ir
curl -f https://prometheus.ramtiin.ir
curl -f https://argocd.ramtiin.ir
```

### Step 3: Access Web Interfaces

Open in browser:

1. **Production**: https://notefy.ramtiin.ir
   - Create a test note
   - Try search
   - Export notes

2. **Staging**: https://staging-notefy.ramtiin.ir
   - Verify staging environment works

3. **Grafana**: https://grafana.ramtiin.ir
   - Login: admin / (get password: `kubectl get secret -n monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d`)
   - Check dashboards

4. **Prometheus**: https://prometheus.ramtiin.ir
   - Check targets are up
   - Query: `flask_http_request_total`

5. **ArgoCD**: https://argocd.ramtiin.ir
   - Login: admin / YOUR_PASSWORD
   - Verify applications are synced

### Step 4: Run Smoke Tests

```bash
# Create test note via API
curl -X POST https://notefy.ramtiin.ir/api/notes \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deployment Test",
    "content": "Testing deployment",
    "tags": ["test", "deployment"]
  }'

# Get all notes
curl https://notefy.ramtiin.ir/api/notes

# Search
curl "https://notefy.ramtiin.ir/api/search?q=deployment"

# Check stats
curl https://notefy.ramtiin.ir/api/stats
```

---

## Post-Deployment

### Step 1: Setup Monitoring

```bash
# Get Grafana password
kubectl get secret -n monitoring monitoring-grafana \
  -o jsonpath="{.data.admin-password}" | base64 -d

# Login to Grafana: https://grafana.ramtiin.ir
# Add Prometheus data source (should be auto-configured)
# Add Loki data source (should be auto-configured)
# Import dashboards from monitoring/grafana/dashboards/
```

### Step 2: Test Backups

```bash
# Trigger manual backup
./scripts/backup.sh production

# Check backup was created
ls -lh backups/

# Test restore (on staging!)
./scripts/restore.sh backups/notefy-backup-*.sql.gz staging
```

### Step 3: Setup Monitoring Alerts

```bash
# Check alert rules are loaded
kubectl exec -n monitoring monitoring-kube-prometheus-prometheus-0 -- \
  promtool check rules /etc/prometheus/rules/prometheus-monitoring-kube-prometheus-prometheus-rulefiles-0/*.yaml

# Verify alertmanager is running
kubectl get pods -n monitoring -l app.kubernetes.io/name=alertmanager
```

### Step 4: Load Test Production

```bash
# On your local machine
locust -f tests/load/test_locust.py \
  --host=https://notefy.ramtiin.ir \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless

# Monitor in Grafana while load testing
# Check:
# - Request rate increases
# - Latency stays < 500ms (p95)
# - Error rate stays < 1%
# - CPU/Memory usage
```

---

## Success Checklist

✅ **Infrastructure**
- [ ] K3s cluster running
- [ ] All namespaces created
- [ ] Ingress controller working
- [ ] Cert-manager issuing certificates
- [ ] DNS records resolving

✅ **Applications**
- [ ] Production deployment healthy
- [ ] Staging deployment healthy
- [ ] Database pods running
- [ ] All pods passing health checks

✅ **GitOps**
- [ ] ArgoCD applications synced
- [ ] Auto-sync working
- [ ] GitHub Actions pipeline passing

✅ **Monitoring**
- [ ] Prometheus scraping metrics
- [ ] Grafana dashboards showing data
- [ ] Loki collecting logs
- [ ] Alerts configured

✅ **Access**
- [ ] https://notefy.ramtiin.ir (Production)
- [ ] https://staging-notefy.ramtiin.ir (Staging)
- [ ] https://grafana.ramtiin.ir (Monitoring)
- [ ] https://prometheus.ramtiin.ir (Metrics)
- [ ] https://argocd.ramtiin.ir (GitOps)

✅ **Testing**
- [ ] All unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] Load tests meeting SLA (p95 < 500ms)
- [ ] Smoke tests passing

✅ **Backups**
- [ ] Daily backup CronJob configured
- [ ] Manual backup tested
- [ ] Restore procedure tested
- [ ] Telegram notifications working

---

## Next Steps

1. **Security Hardening** (for DevSecOps phase):
   - Implement secret scanning
   - Add SAST/DAST tools
   - Container vulnerability scanning
   - Network policies

2. **Advanced Monitoring**:
   - Custom Grafana dashboards
   - Alert routing to PagerDuty/Slack
   - Distributed tracing (Jaeger)
   - Log analysis automation

3. **Performance Optimization**:
   - Database query optimization
   - Redis caching layer
   - CDN for static assets
   - Database read replicas

4. **High Availability**:
   - Multi-node K3s cluster
   - PostgreSQL replication
   - Geographic redundancy
   - Auto-scaling policies

---

## Troubleshooting

See main README.md for detailed troubleshooting guide.

---

**Congratulations! You've successfully deployed Notefy with a complete DevOps pipeline!** 🎉