#!/bin/bash

# Resume Bot Backend - Docker Build and Push Script
# This script builds and pushes the Docker image to ECR with meaningful naming and timestamp tags

set -e

# Change to the directory where this script is located
cd "$(dirname "${BASH_SOURCE[0]}")"

# Configuration
AWS_REGION=${AWS_REGION:-"ca-central-1"}
ECR_REPOSITORY="resume-bot/backend-lambda"
IMAGE_TAG_PREFIX="backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install it first."
    exit 1
fi

print_info "Starting Resume Bot Backend Docker build and push process..."

# Generate timestamp and commit info
TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")
if git rev-parse --git-dir > /dev/null 2>&1; then
    COMMIT_SHA=$(git rev-parse --short HEAD)
else
    COMMIT_SHA="local"
fi

IMAGE_TAG="${IMAGE_TAG_PREFIX}-${TIMESTAMP}-${COMMIT_SHA}"

print_info "Image tag: ${IMAGE_TAG}"

# Get AWS account ID for ECR registry
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ $? -ne 0 ]; then
    print_error "Failed to get AWS account ID. Make sure AWS CLI is configured."
    exit 1
fi

ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
FULL_IMAGE_URI="${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}"
LATEST_IMAGE_URI="${ECR_REGISTRY}/${ECR_REPOSITORY}:latest"

print_info "ECR Registry: ${ECR_REGISTRY}"
print_info "Repository: ${ECR_REPOSITORY}"
print_info "Full Image URI: ${FULL_IMAGE_URI}"

# Login to ECR
print_info "Logging into Amazon ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

if [ $? -ne 0 ]; then
    print_error "Failed to login to ECR"
    exit 1
fi

print_success "Successfully logged into ECR"

# Create ECR repository if it doesn't exist
print_info "Ensuring ECR repository exists..."
aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${AWS_REGION} > /dev/null 2>&1 || {
    print_warning "Repository ${ECR_REPOSITORY} does not exist. Creating..."
    aws ecr create-repository \
        --repository-name ${ECR_REPOSITORY} \
        --region ${AWS_REGION} \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
    
    if [ $? -eq 0 ]; then
        print_success "Repository ${ECR_REPOSITORY} created successfully"
    else
        print_error "Failed to create repository"
        exit 1
    fi
}

# Build Docker image
print_info "Building Docker image..."
cd ".." # Navigate to resume-bot-backend directory

docker build \
    -f Dockerfile.lambda \
    -t ${FULL_IMAGE_URI} \
    -t ${LATEST_IMAGE_URI} \
    --build-arg BUILD_TIMESTAMP=${TIMESTAMP} \
    --build-arg BUILD_COMMIT=${COMMIT_SHA} \
    .

if [ $? -eq 0 ]; then
    print_success "Docker image built successfully"
else
    print_error "Docker build failed"
    exit 1
fi

# Push Docker image
print_info "Pushing Docker image to ECR..."

# Push timestamped version
print_info "Pushing tagged image: ${IMAGE_TAG}"
docker push ${FULL_IMAGE_URI}

if [ $? -eq 0 ]; then
    print_success "Tagged image pushed successfully"
else
    print_error "Failed to push tagged image"
    exit 1
fi

# Push latest version
print_info "Pushing latest image..."
docker push ${LATEST_IMAGE_URI}

if [ $? -eq 0 ]; then
    print_success "Latest image pushed successfully"
else
    print_error "Failed to push latest image"
    exit 1
fi

# Output summary
echo
print_success "🎉 Docker image build and push completed successfully!"
echo
echo "📦 Repository: ${ECR_REPOSITORY}"
echo "🏷️  Image Tag: ${IMAGE_TAG}"
echo "🔗 Full Image URI: ${FULL_IMAGE_URI}"
echo "📅 Build Timestamp: ${TIMESTAMP}"
echo "🔨 Commit SHA: ${COMMIT_SHA}"
echo "🌐 AWS Region: ${AWS_REGION}"
echo
print_info "You can now use this image URI in your CDK deployment:"
print_info "  ${FULL_IMAGE_URI}"
echo
print_info "Or reference the latest version:"
print_info "  ${LATEST_IMAGE_URI}"