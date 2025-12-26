#!/bin/bash
# scripts/backup.sh - Manual backup script

set -e

NAMESPACE="${1:-production}"
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)
BACKUP_DIR="./backups"
BACKUP_FILE="notefy-manual-backup-${TIMESTAMP}.sql.gz"

echo "🔄 Starting manual backup for ${NAMESPACE} environment..."

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Get database credentials from secret
POSTGRES_USER=$(kubectl get secret postgres-secret -n ${NAMESPACE} -o jsonpath='{.data.POSTGRES_USER}' | base64 -d)
POSTGRES_PASSWORD=$(kubectl get secret postgres-secret -n ${NAMESPACE} -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)
POSTGRES_DB=$(kubectl get secret postgres-secret -n ${NAMESPACE} -o jsonpath='{.data.POSTGRES_DB}' | base64 -d)

# Get postgres pod name
POSTGRES_POD=$(kubectl get pods -n ${NAMESPACE} -l app=postgres -o jsonpath='{.items[0].metadata.name}')

echo "📦 Creating backup from pod: ${POSTGRES_POD}"

# Create backup
kubectl exec -n ${NAMESPACE} ${POSTGRES_POD} -- bash -c "PGPASSWORD=${POSTGRES_PASSWORD} pg_dump -U ${POSTGRES_USER} -d ${POSTGRES_DB}" | gzip > "${BACKUP_DIR}/${BACKUP_FILE}"

BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)

echo "✅ Backup completed successfully!"
echo "📁 File: ${BACKUP_DIR}/${BACKUP_FILE}"
echo "💾 Size: ${BACKUP_SIZE}"

# List recent backups
echo ""
echo "📋 Recent backups:"
ls -lht ${BACKUP_DIR}/ | head -n 6

---

#!/bin/bash
# scripts/restore.sh - Restore database from backup

set -e

if [ -z "$1" ]; then
    echo "❌ Usage: $0 <backup-file> [namespace]"
    echo "Example: $0 backups/notefy-backup-2025-01-15-020000.sql.gz production"
    exit 1
fi

BACKUP_FILE="$1"
NAMESPACE="${2:-production}"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "⚠️  WARNING: This will restore the database in ${NAMESPACE} environment"
echo "📁 From file: ${BACKUP_FILE}"
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 0
fi

# Get database credentials
POSTGRES_USER=$(kubectl get secret postgres-secret -n ${NAMESPACE} -o jsonpath='{.data.POSTGRES_USER}' | base64 -d)
POSTGRES_PASSWORD=$(kubectl get secret postgres-secret -n ${NAMESPACE} -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)
POSTGRES_DB=$(kubectl get secret postgres-secret -n ${NAMESPACE} -o jsonpath='{.data.POSTGRES_DB}' | base64 -d)

# Get postgres pod
POSTGRES_POD=$(kubectl get pods -n ${NAMESPACE} -l app=postgres -o jsonpath='{.items[0].metadata.name}')

echo "🔄 Restoring to pod: ${POSTGRES_POD}"

# Scale down application to prevent connections
echo "⏸️  Scaling down application..."
kubectl scale deployment notefy -n ${NAMESPACE} --replicas=0

# Wait for pods to terminate
sleep 10

# Drop and recreate database
echo "🗑️  Dropping existing database..."
kubectl exec -n ${NAMESPACE} ${POSTGRES_POD} -- bash -c "PGPASSWORD=${POSTGRES_PASSWORD} psql -U ${POSTGRES_USER} -c 'DROP DATABASE IF EXISTS ${POSTGRES_DB};'"
kubectl exec -n ${NAMESPACE} ${POSTGRES_POD} -- bash -c "PGPASSWORD=${POSTGRES_PASSWORD} psql -U ${POSTGRES_USER} -c 'CREATE DATABASE ${POSTGRES_DB};'"

# Restore backup
echo "📦 Restoring backup..."
gunzip -c "${BACKUP_FILE}" | kubectl exec -i -n ${NAMESPACE} ${POSTGRES_POD} -- bash -c "PGPASSWORD=${POSTGRES_PASSWORD} psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}"

# Scale up application
echo "▶️  Scaling up application..."
REPLICAS=3
if [ "${NAMESPACE}" == "staging" ]; then
    REPLICAS=2
fi
kubectl scale deployment notefy -n ${NAMESPACE} --replicas=${REPLICAS}

echo "✅ Restore completed successfully!"
echo "🔍 Verify the application: https://notefy.ramtiin.ir"

---

#!/bin/bash
# scripts/setup-k3s.sh - Initial K3s cluster setup

set -e

echo "🚀 Setting up K3s cluster for Notefy..."

# Install K3s
echo "📦 Installing K3s..."
curl -sfL https://get.k3s.io | sh -

# Configure kubectl
echo "⚙️  Configuring kubectl..."
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
echo "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml" >> ~/.bashrc

# Wait for K3s to be ready
echo "⏳ Waiting for K3s to be ready..."
sleep 30

# Install Nginx Ingress Controller
echo "🌐 Installing Nginx Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.4/deploy/static/provider/cloud/deploy.yaml

# Wait for ingress controller
echo "⏳ Waiting for Ingress Controller..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

# Install cert-manager
echo "🔒 Installing cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml

# Wait for cert-manager
echo "⏳ Waiting for cert-manager..."
kubectl wait --namespace cert-manager \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/instance=cert-manager \
  --timeout=120s

# Create ClusterIssuer
echo "📜 Creating Let's Encrypt ClusterIssuer..."
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@ramtiin.ir
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Install ArgoCD
echo "🔄 Installing ArgoCD..."
kubectl create namespace argocd || true
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD
echo "⏳ Waiting for ArgoCD..."
kubectl wait --namespace argocd \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=argocd-server \
  --timeout=300s

# Get ArgoCD password
echo "🔑 ArgoCD initial password:"
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo ""

# Install monitoring stack
echo "📊 Installing Prometheus & Grafana..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

# Install Loki
echo "📝 Installing Loki..."
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set grafana.enabled=false \
  --set promtail.enabled=true

# Create namespaces
echo "📦 Creating application namespaces..."
kubectl create namespace production || true
kubectl create namespace staging || true

echo ""
echo "✅ K3s cluster setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Configure DNS records to point to this server"
echo "2. Create database secrets:"
echo "   kubectl create secret generic postgres-secret \\"
echo "     --from-literal=POSTGRES_DB=notefy_prod \\"
echo "     --from-literal=POSTGRES_USER=notefy \\"
echo "     --from-literal=POSTGRES_PASSWORD=\$(openssl rand -base64 32) \\"
echo "     -n production"
echo ""
echo "3. Create Telegram secrets (optional):"
echo "   kubectl create secret generic telegram-secret \\"
echo "     --from-literal=TELEGRAM_BOT_TOKEN=your_token \\"
echo "     --from-literal=TELEGRAM_CHAT_ID=your_chat_id \\"
echo "     -n production"
echo ""
echo "4. Apply ArgoCD applications:"
echo "   kubectl apply -f argocd/application-prod.yaml"
echo "   kubectl apply -f argocd/application-staging.yaml"
echo ""
echo "5. Apply monitoring ingress:"
echo "   kubectl apply -f monitoring/ingress.yaml"
echo ""
echo "6. Access ArgoCD:"
echo "   kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo "   Username: admin"
echo "   Password: (shown above)"