#!/bin/bash

# Docker Build and Push Helper Script
# Usage: ./docker-helper.sh [build|push|build-push|login] [service-name]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="eks-multi-service"

# Available services
SERVICES=(
    "frontend"
    "api-gateway"
    "auth-service"
    "product-service"
    "order-service"
    "payment-service"
)

# Functions
function print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function print_error() {
    echo -e "${RED}✗ $1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

function get_account_id() {
    aws sts get-caller-identity --query Account --output text 2>/dev/null || {
        print_error "Failed to get AWS account ID. Please configure AWS credentials."
        exit 1
    }
}

function get_registry_url() {
    local account_id=$(get_account_id)
    echo "${account_id}.dkr.ecr.${AWS_REGION}.amazonaws.com"
}

function ecr_login() {
    print_header "Logging into Amazon ECR"
    
    local registry_url=$(get_registry_url)
    
    aws ecr get-login-password --region ${AWS_REGION} | \
        docker login --username AWS --password-stdin ${registry_url}
    
    if [ $? -eq 0 ]; then
        print_success "Successfully logged into ECR: ${registry_url}"
    else
        print_error "Failed to login to ECR"
        exit 1
    fi
}

function build_image() {
    local service=$1
    local tag=${2:-latest}
    
    print_header "Building Docker Image: ${service}"
    
    # Check if service directory exists
    if [ ! -d "services/${service}" ]; then
        print_error "Service directory not found: services/${service}"
        exit 1
    fi
    
    # Check if Dockerfile exists
    if [ ! -f "services/${service}/Dockerfile" ]; then
        print_error "Dockerfile not found: services/${service}/Dockerfile"
        exit 1
    fi
    
    local image_name="${PROJECT_NAME}/${service}:${tag}"
    
    echo -e "${YELLOW}Building: ${image_name}${NC}"
    
    # Build with BuildKit
    DOCKER_BUILDKIT=1 docker build \
        -t ${image_name} \
        -f services/${service}/Dockerfile \
        services/${service}/
    
    if [ $? -eq 0 ]; then
        print_success "Successfully built: ${image_name}"
        
        # Display image size
        local size=$(docker images ${image_name} --format "{{.Size}}")
        echo -e "${GREEN}Image size: ${size}${NC}"
    else
        print_error "Build failed for ${service}"
        exit 1
    fi
}

function push_image() {
    local service=$1
    local tag=${2:-latest}
    
    print_header "Pushing Docker Image: ${service}"
    
    local registry_url=$(get_registry_url)
    local local_image="${PROJECT_NAME}/${service}:${tag}"
    local remote_image="${registry_url}/${PROJECT_NAME}/${service}:${tag}"
    
    # Tag for ECR
    echo -e "${YELLOW}Tagging: ${local_image} → ${remote_image}${NC}"
    docker tag ${local_image} ${remote_image}
    
    # Push to ECR
    echo -e "${YELLOW}Pushing: ${remote_image}${NC}"
    docker push ${remote_image}
    
    if [ $? -eq 0 ]; then
        print_success "Successfully pushed: ${remote_image}"
    else
        print_error "Push failed for ${service}"
        exit 1
    fi
}

function build_and_push() {
    local service=$1
    local tag=${2:-latest}
    
    build_image ${service} ${tag}
    ecr_login
    push_image ${service} ${tag}
}

function build_all() {
    print_header "Building All Services"
    
    for service in "${SERVICES[@]}"; do
        echo ""
        build_image ${service} latest
    done
    
    print_success "All services built successfully!"
}

function push_all() {
    print_header "Pushing All Services"
    
    ecr_login
    
    for service in "${SERVICES[@]}"; do
        echo ""
        push_image ${service} latest
    done
    
    print_success "All services pushed successfully!"
}

function show_usage() {
    echo "Usage: $0 [command] [service] [tag]"
    echo ""
    echo "Commands:"
    echo "  login                  - Login to Amazon ECR"
    echo "  build [service] [tag]  - Build Docker image for a service"
    echo "  push [service] [tag]   - Push Docker image to ECR"
    echo "  build-push [service] [tag] - Build and push in one command"
    echo "  build-all              - Build all services"
    echo "  push-all               - Push all services to ECR"
    echo "  list                   - List all available services"
    echo ""
    echo "Services:"
    for service in "${SERVICES[@]}"; do
        echo "  - ${service}"
    done
    echo ""
    echo "Examples:"
    echo "  $0 login"
    echo "  $0 build frontend"
    echo "  $0 build frontend v1.2.3"
    echo "  $0 push frontend latest"
    echo "  $0 build-push api-gateway v2.0.0"
    echo "  $0 build-all"
}

function list_services() {
    print_header "Available Services"
    
    for service in "${SERVICES[@]}"; do
        if [ -d "services/${service}" ]; then
            echo -e "${GREEN}✓ ${service}${NC}"
        else
            echo -e "${RED}✗ ${service} (directory not found)${NC}"
        fi
    done
}

function validate_service() {
    local service=$1
    
    if [[ ! " ${SERVICES[@]} " =~ " ${service} " ]]; then
        print_error "Invalid service: ${service}"
        echo ""
        list_services
        exit 1
    fi
}

# Main script
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

COMMAND=$1

case ${COMMAND} in
    login)
        ecr_login
        ;;
    build)
        if [ -z "$2" ]; then
            print_error "Service name required"
            show_usage
            exit 1
        fi
        validate_service $2
        build_image $2 ${3:-latest}
        ;;
    push)
        if [ -z "$2" ]; then
            print_error "Service name required"
            show_usage
            exit 1
        fi
        validate_service $2
        ecr_login
        push_image $2 ${3:-latest}
        ;;
    build-push)
        if [ -z "$2" ]; then
            print_error "Service name required"
            show_usage
            exit 1
        fi
        validate_service $2
        build_and_push $2 ${3:-latest}
        ;;
    build-all)
        build_all
        ;;
    push-all)
        push_all
        ;;
    list)
        list_services
        ;;
    *)
        print_error "Unknown command: ${COMMAND}"
        echo ""
        show_usage
        exit 1
        ;;
esac

print_success "Done!"