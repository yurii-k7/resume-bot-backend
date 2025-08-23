#!/bin/bash

# Resume Bot Backend - Deploy Latest ECR Image
# This script gets the latest ECR image and deploys it using direct Lambda update

set -e

# Change to the directory where this script is located
cd "$(dirname "${BASH_SOURCE[0]}")"

# Configuration
AWS_REGION=${AWS_REGION:-"ca-central-1"}
ECR_REPOSITORY="resume-bot/backend-lambda"
LAMBDA_FUNCTION_NAME="resume-bot-backend"
STACK_NAME="ResumeBotBackendStack"

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

print_info "Starting Resume Bot Backend deployment using direct Lambda update"

# Check prerequisites
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ $? -ne 0 ]; then
    print_error "Failed to get AWS account ID. Make sure AWS CLI is configured."
    exit 1
fi

ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Step 1: Get the latest ECR image
print_info "Getting latest ECR image from repository: ${ECR_REPOSITORY}"

# Check if repository exists
aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${AWS_REGION} > /dev/null 2>&1
if [ $? -ne 0 ]; then
    print_error "ECR repository ${ECR_REPOSITORY} does not exist"
    print_info "Please run the build-and-push script first: ./resume-bot-backend/scripts/build-and-push.sh"
    exit 1
fi

# Get the most recent timestamped tag (exclude 'latest' tag)
# First get all tags from the most recent image, then filter out 'latest' in bash
ALL_TAGS=$(aws ecr describe-images \
    --repository-name ${ECR_REPOSITORY} \
    --region ${AWS_REGION} \
    --query 'sort_by(imageDetails,&imagePushedAt)[-1].imageTags' \
    --output text)

# Filter out 'latest' tag and get the first remaining tag
LATEST_TAG=""
for tag in $ALL_TAGS; do
    if [[ "$tag" != "latest" ]]; then
        LATEST_TAG="$tag"
        break
    fi
done

if [ "$LATEST_TAG" == "None" ] || [ -z "$LATEST_TAG" ]; then
    print_error "No images found in ECR repository ${ECR_REPOSITORY}"
    print_info "Please run the build-and-push script first: ./resume-bot-backend/scripts/build-and-push.sh"
    exit 1
fi

ECR_IMAGE_URI="${ECR_REGISTRY}/${ECR_REPOSITORY}:${LATEST_TAG}"
print_success "Found latest ECR image: ${ECR_IMAGE_URI}"

# Get image details for summary
IMAGE_PUSHED_AT=$(aws ecr describe-images \
    --repository-name ${ECR_REPOSITORY} \
    --region ${AWS_REGION} \
    --query "sort_by(imageDetails,&imagePushedAt)[-1].imagePushedAt" \
    --output text)

print_info "Image pushed at: ${IMAGE_PUSHED_AT}"

# Step 2: Deploy using direct Lambda update
print_info "Deploying using direct Lambda update..."

# Check if Lambda function exists
aws lambda get-function --function-name ${LAMBDA_FUNCTION_NAME} --region ${AWS_REGION} > /dev/null 2>&1
if [ $? -ne 0 ]; then
    print_error "Lambda function ${LAMBDA_FUNCTION_NAME} does not exist"
    print_info "Please deploy the CDK stack first"
    exit 1
fi

# Update Lambda function with new image
print_info "Updating Lambda function: ${LAMBDA_FUNCTION_NAME}"
aws lambda update-function-code \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --image-uri ${ECR_IMAGE_URI} \
    --region ${AWS_REGION} > /dev/null

if [ $? -ne 0 ]; then
    print_error "Failed to update Lambda function"
    exit 1
fi

# Wait for update to complete
print_info "Waiting for Lambda function update to complete..."
aws lambda wait function-updated \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --region ${AWS_REGION}

if [ $? -eq 0 ]; then
    print_success "Lambda function updated successfully!"
else
    print_error "Lambda function update timeout or failed"
    exit 1
fi

# Step 3: Verify deployment
print_info "Verifying deployment..."

CURRENT_IMAGE=$(aws lambda get-function \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --region ${AWS_REGION} \
    --query 'Code.ImageUri' \
    --output text)

print_info "Current Lambda Image URI: ${CURRENT_IMAGE}"

if [[ "$CURRENT_IMAGE" == "$ECR_IMAGE_URI" ]]; then
    print_success "✅ Lambda function is using the correct ECR image!"
else
    print_warning "⚠️  Lambda function image URI doesn't match expected URI"
    print_info "Expected: ${ECR_IMAGE_URI}"
    print_info "Current:  ${CURRENT_IMAGE}"
fi

# Final summary
echo
print_success "🎉 Resume Bot Backend deployment completed!"
echo
print_info "📋 Deployment Summary:"
echo "   📦 ECR Repository: ${ECR_REPOSITORY}"
echo "   🏷️  Image Tag: ${LATEST_TAG}"
echo "   🔗 ECR Image URI: ${ECR_IMAGE_URI}"
echo "   🔧 Lambda Function: ${LAMBDA_FUNCTION_NAME}"
echo "   🚀 Deploy Method: Direct Lambda Update"
echo "   🌐 AWS Region: ${AWS_REGION}"
echo "   📅 Image Pushed: ${IMAGE_PUSHED_AT}"
echo
print_info "Your Resume Bot backend is now running the latest containerized image!"

# Show usage examples
echo
print_info "💡 Usage:"
echo "   ./deploy-latest-image.sh"