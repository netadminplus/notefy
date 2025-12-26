# Notefy - Production-Grade DevOps Project

![Notefy Banner](https://via.placeholder.com/1200x300/3b82f6/ffffff?text=Notefy+-+Smart+Note+Taking)

[![CI/CD Pipeline](https://github.com/netadminplus/notefy/actions/workflows/ci-cd.yaml/badge.svg)](https://github.com/netadminplus/notefy/actions)
[![codecov](https://codecov.io/gh/netadminplus/notefy/branch/main/graph/badge.svg)](https://codecov.io/gh/netadminplus/notefy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, cloud-native note-taking application built to demonstrate production-grade DevOps practices including GitOps, CI/CD automation, and comprehensive observability.

## 🌟 Features

- **Modern Web Interface**: Beautiful, responsive UI built with Tailwind CSS
- **Full CRUD Operations**: Create, Read, Update, Delete notes
- **Rich Features**: Tags, search, color coding, pinning, export (JSON/Markdown)
- **No Authentication**: Public collaborative note board
- **Production-Ready**: Designed for high availability and scalability

## 🏗️ Architecture

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   GitHub     │────────▶│  GitHub      │────────▶│   ArgoCD     │
│  Repository  │         │  Actions     │         │   GitOps     │
└──────────────┘         └──────────────┘         └──────────────┘
                                │                          │
                                ▼                          ▼
                         ┌──────────────┐         ┌──────────────┐
                         │   Docker     │         │  Kubernetes  │
                         │     Hub      │         │   Cluster    │
                         └──────────────┘         └──────────────┘
                                                          │
                         ┌────────────────────────────────┤
                         │                                │
                    ┌────▼────┐                    ┌─────▼─────┐
                    │Production│                    │  Staging  │
                    │Namespace │                    │ Namespace │
                    └─────────┘                    └───────────┘
                         │
                    ┌────▼────────┐
                    │ Monitoring  │
                    │ Prometheus  │
                    │  Grafana    │
                    └─────────────┘
```

## 🚀 Tech Stack

### Application
- **Backend**: Python 3.11 + Flask
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy
- **Server**: Gunicorn (4 workers)
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript

### DevOps & Infrastructure
- **Container**: Docker
- **Orchestration**: Kubernetes (K3s)
- **GitOps**: ArgoCD
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana + Loki
- **Ingress**: Nginx Ingress Controller
- **Certificates**: cert-manager (Let's Encrypt)

### Observability
- **Metrics**: Prometheus + prometheus-flask-exporter
- **Logs**: Loki + Promtail (structured JSON logging)
- **Dashboards**: Grafana
- **Alerts**: Prometheus Alertmanager

## 📁 Project Structure

```
notefy/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models
│   ├── routes.py            # API endpoints
│   ├── config.py            # Configuration
│   └── templates/           # HTML templates
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── load/                # Load tests (Locust)
├── k8s/
│   ├── production/          # Production manifests
│   └── staging/             # Staging manifests
├── argocd/                  # ArgoCD applications
├── monitoring/              # Prometheus, Grafana configs
├── scripts/                 # Helper scripts
├── .github/
│   └── workflows/           # CI/CD pipelines
├── Dockerfile
├── docker-compose.yaml      # Local development
├── requirements.txt
└── README.md
```

## 🔧 Local Development Setup (macOS)

### Prerequisites
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install python@3.11 docker kubectl helm
```

### Quick Start
```bash
# 1. Clone repository
git clone https://github.com/netadminplus/notefy.git
cd notefy

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run with Docker Compose
docker-compose up -d

# 5. Access application
open http://localhost:5000

# 6. Run tests
pytest --cov=app

# 7. Run linting
black .
flake8 .
pylint app/
```

### Development Workflow
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Run tests
pytest tests/unit/ -v
pytest tests/integration/ -v

# Load testing
locust -f tests/load/test_locust.py --host=http://localhost:5000

# Stop services
docker-compose down
```

## 🖥️ Production Deployment (Ubuntu 22.04)

### Step 1: Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl git

# Clone repository
git clone https://github.com/netadminplus/notefy.git
cd notefy

# Run setup script
chmod +x scripts/setup-k3s.sh
sudo ./scripts/setup-k3s.sh
```

### Step 2: Configure DNS

Add A records in your DNS provider:
```
notefy.ramtiin.ir          → YOUR_SERVER_IP
staging-notefy.ramtiin.ir  → YOUR_SERVER_IP
grafana.ramtiin.ir         → YOUR_SERVER_IP
prometheus.ramtiin.ir      → YOUR_SERVER_IP
argocd.ramtiin.ir          → YOUR_SERVER_IP
```

### Step 3: Create Secrets

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

# Telegram notification secret (optional)
kubectl create secret generic telegram-secret \
  --from-literal=TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN \
  --from-literal=TELEGRAM_CHAT_ID=YOUR_CHAT_ID \
  -n production
```

### Step 4: Setup GitHub Secrets

Go to GitHub repo → Settings → Secrets and add:

```
DOCKER_USERNAME: your_dockerhub_username
DOCKER_PASSWORD: your_dockerhub_password
TELEGRAM_BOT_TOKEN: your_telegram_bot_token
TELEGRAM_CHAT_ID: your_telegram_chat_id
```

### Step 5: Deploy with ArgoCD

```bash
# Apply ArgoCD applications
kubectl apply -f argocd/application-prod.yaml
kubectl apply -f argocd/application-staging.yaml

# Apply monitoring ingress
kubectl apply -f monitoring/ingress.yaml

# Apply ArgoCD ingress
kubectl apply -f argocd/argocd-ingress.yaml

# Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

### Step 6: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n production
kubectl get pods -n staging
kubectl get pods -n monitoring
kubectl get pods -n argocd

# Check ingress
kubectl get ingress -A

# Test endpoints
curl https://notefy.ramtiin.ir/health
curl https://staging-notefy.ramtiin.ir/health
```

## 🔄 CI/CD Pipeline

### Pipeline Stages

1. **Lint** - Code quality checks (Black, Flake8, Pylint)
2. **Test** - Unit, integration tests with coverage
3. **Build** - Docker image build and push
4. **Deploy Staging** - Auto-deploy to staging on `staging` branch
5. **Deploy Production** - Manual approval for `main` branch

### Workflow Triggers

```yaml
Push to main → Production deployment (manual approval)
Push to staging → Staging deployment (automatic)
Pull request → Tests only
```

### Deployment Flow

```
Code Push → GitHub Actions → Build Docker Image → Push to Docker Hub
                                                           ↓
ArgoCD polls Git repo → Detects new image tag → Syncs to K8s → Rolling update
                                                           ↓
                                              Health checks pass → Telegram notification
```

## 📊 Monitoring & Observability

### Access Dashboards

- **Grafana**: https://grafana.ramtiin.ir
  - Username: `admin`
  - Password: Get from secret: `kubectl get secret -n monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d`

- **Prometheus**: https://prometheus.ramtiin.ir
- **ArgoCD**: https://argocd.ramtiin.ir

### Key Metrics

The application exposes the following metrics at `/metrics`:

- `flask_http_request_total` - Total HTTP requests
- `flask_http_request_duration_seconds` - Request latency histogram
- `flask_http_request_exceptions_total` - Exception count
- Application-specific metrics (notes created, searches, exports)

### Grafana Dashboards

Import the pre-configured dashboards from `monitoring/grafana/dashboards/`:

1. **Application Overview**
   - Request rate
   - Error rate
   - Latency (p50, p95, p99)
   - Active users

2. **Infrastructure**
   - Pod CPU/Memory
   - Database connections
   - Disk usage

3. **Business Metrics**
   - Notes created per hour
   - Popular tags
   - Search queries

### Alerts

Configured in `monitoring/prometheus/alerts.yaml`:

- High error rate (>5% for 5m)
- High latency (p95 > 1s for 5m)
- Application down (2m)
- Database down (1m)
- High memory/CPU usage
- Pod restarting frequently

## 💾 Backup & Restore

### Automated Backups

Daily backups run at 2:00 AM UTC via CronJob:
```bash
# Check backup jobs
kubectl get cronjobs -n production

# View backup logs
kubectl logs -n production job/postgres-backup-<timestamp>

# List backups
kubectl exec -n production <backup-pod> -- ls -lh /backups/
```

### Manual Backup

```bash
# Create backup
./scripts/backup.sh production

# Backups are stored in ./backups/
ls -lh backups/
```

### Restore from Backup

```bash
# Restore production
./scripts/restore.sh backups/notefy-backup-2025-01-15-020000.sql.gz production

# Restore staging
./scripts/restore.sh backups/notefy-backup-2025-01-15-020000.sql.gz staging
```

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit/ -v --cov=app
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Load Tests
```bash
# Run load test with 100 concurrent users
locust -f tests/load/test_locust.py \
  --host=https://notefy.ramtiin.ir \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless

# With web UI
locust -f tests/load/test_locust.py --host=https://notefy.ramtiin.ir
# Open http://localhost:8089
```

### Success Criteria
- Unit test coverage > 80%
- All integration tests pass
- Load test: 100 users, p95 < 500ms, error rate < 1%

## 🐛 Troubleshooting

### Application Won't Start

```bash
# Check pod status
kubectl get pods -n production
kubectl describe pod <pod-name> -n production
kubectl logs <pod-name> -n production

# Check database connection
kubectl exec -n production <notefy-pod> -- curl localhost:5000/health
```

### Database Issues

```bash
# Check postgres pod
kubectl get pods -n production -l app=postgres
kubectl logs -n production <postgres-pod>

# Connect to database
kubectl exec -it -n production <postgres-pod> -- psql -U notefy -d notefy_prod
```

### Ingress Not Working

```bash
# Check ingress
kubectl get ingress -n production
kubectl describe ingress notefy-ingress -n production

# Check certificate
kubectl get certificate -n production
kubectl describe certificate notefy-tls -n production

# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx <ingress-controller-pod>
```

### ArgoCD Sync Issues

```bash
# Check application status
argocd app get notefy-production

# Force sync
argocd app sync notefy-production --force

# Check sync status
argocd app wait notefy-production
```

### High Latency

```bash
# Check resource usage
kubectl top pods -n production

# Check database queries
kubectl logs -n production <notefy-pod> | grep "slow query"

# Scale up if needed
kubectl scale deployment notefy -n production --replicas=5
```

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale production
kubectl scale deployment notefy -n production --replicas=5

# Scale staging
kubectl scale deployment notefy -n staging --replicas=3

# Auto-scaling (HPA)
kubectl autoscale deployment notefy -n production \
  --cpu-percent=70 \
  --min=3 \
  --max=10
```

### Vertical Scaling

Edit `k8s/production/deployment.yaml`:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## 🔒 Security Notes

**⚠️ This is a DevOps demo project. The following are intentional vulnerabilities for educational purposes:**

1. Hardcoded AWS credentials in `app/config.py`
2. SQL injection vulnerability in search endpoint
3. Outdated Flask version (2.2.0)
4. Container running as root user

**These will be addressed in the DevSecOps phase with:**
- Secret scanning (GitGuardian, TruffleHog)
- SAST (Bandit, SonarQube)
- DAST (OWASP ZAP)
- Container scanning (Trivy, Grype)
- Dependency scanning (Snyk, Dependabot)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for DevOps webinar demonstrating production best practices
- Showcases GitOps, CI/CD, and observability patterns
- Designed for educational purposes

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/netadminplus/notefy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/netadminplus/notefy/discussions)
- **Email**: support@ramtiin.ir

---

**Made with ❤️ for DevOps Excellence**