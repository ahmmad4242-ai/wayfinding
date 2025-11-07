#!/usr/bin/env bash
set -e

##############################################
# Floor Plan Analyzer - Deployment Script
# للنشر على VPS
##############################################

PROJECT_NAME="floor-plan-analyzer"
DEPLOY_DIR="/opt/${PROJECT_NAME}"
BACKUP_DIR="/opt/backups/${PROJECT_NAME}"
DOCKER_IMAGE="fpa:latest"

echo "🚀 Starting deployment of Floor Plan Analyzer..."

# Colors for output
RED='\033[0:31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root or with sudo${NC}"
    exit 1
fi

# Function to print colored messages
print_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Docker installation
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    echo "Install with: curl -fsSL https://get.docker.com | bash"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed!"
    echo "Install with: pip3 install docker-compose"
    exit 1
fi

# Create deployment directory
print_info "Creating deployment directory..."
mkdir -p ${DEPLOY_DIR}
mkdir -p ${BACKUP_DIR}
mkdir -p ${DEPLOY_DIR}/data/{uploads,outputs,cache}

# Backup existing deployment (if exists)
if [ -d "${DEPLOY_DIR}/src" ]; then
    print_info "Backing up existing deployment..."
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    tar -czf ${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz -C ${DEPLOY_DIR} . 2>/dev/null || true
    print_info "Backup created: backup_${TIMESTAMP}.tar.gz"
fi

# Copy files to deployment directory
print_info "Copying application files..."
rsync -av --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='data/' \
    ./ ${DEPLOY_DIR}/

# Copy .env if provided
if [ -f ".env" ]; then
    cp .env ${DEPLOY_DIR}/.env
    print_info ".env file copied"
else
    print_warning "No .env file found. Using .env.example as template."
    cp .env.example ${DEPLOY_DIR}/.env
    print_warning "⚠️  Please edit ${DEPLOY_DIR}/.env with your configuration!"
fi

# Set proper permissions
print_info "Setting permissions..."
chown -R $SUDO_USER:$SUDO_USER ${DEPLOY_DIR} 2>/dev/null || true
chmod -R 755 ${DEPLOY_DIR}
chmod 600 ${DEPLOY_DIR}/.env

# Stop existing containers
print_info "Stopping existing containers..."
cd ${DEPLOY_DIR}
docker-compose down 2>/dev/null || true

# Pull/Build images
print_info "Building Docker images..."
docker-compose build --no-cache

# Start services
print_info "Starting services..."
docker-compose up -d

# Wait for services to be healthy
print_info "Waiting for services to be ready..."
sleep 10

# Check health
print_info "Checking service health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_info "✅ API is healthy!"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""

# Display status
print_info "Checking container status..."
docker-compose ps

# Display logs
print_info "Recent logs:"
docker-compose logs --tail=20

echo ""
print_info "============================================"
print_info "✅ Deployment completed successfully!"
print_info "============================================"
echo ""
print_info "API URL: http://$(hostname -I | awk '{print $1}'):8000"
print_info "Docs: http://$(hostname -I | awk '{print $1}'):8000/api/docs"
echo ""
print_info "Useful commands:"
echo "  - View logs: cd ${DEPLOY_DIR} && docker-compose logs -f"
echo "  - Restart: cd ${DEPLOY_DIR} && docker-compose restart"
echo "  - Stop: cd ${DEPLOY_DIR} && docker-compose stop"
echo "  - Update: ./infra/update.sh"
echo ""
