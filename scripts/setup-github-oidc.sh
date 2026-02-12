#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub Actions OIDC Setup for AWS${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Prompt for GitHub details
read -p "Enter your GitHub username/organization: " GITHUB_ORG
read -p "Enter your GitHub repository name: " GITHUB_REPO

# Get AWS Account ID
echo -e "\n${YELLOW}Fetching AWS Account ID...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}Error: Unable to fetch AWS Account ID. Please check your AWS credentials.${NC}"
    exit 1
fi

echo -e "${GREEN}AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"

# Check if OIDC provider already exists
echo -e "\n${YELLOW}Checking if OIDC provider already exists...${NC}"
OIDC_PROVIDER_ARN=$(aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn" --output text 2>/dev/null)

if [ -z "$OIDC_PROVIDER_ARN" ]; then
    echo -e "${YELLOW}Creating OIDC provider...${NC}"
    aws iam create-open-id-connect-provider \
        --url https://token.actions.githubusercontent.com \
        --client-id-list sts.amazonaws.com \
        --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
        --tags Key=Purpose,Value=GitHubActions Key=Project,Value=EKS-MultiService
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ OIDC provider created successfully${NC}"
        OIDC_PROVIDER_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
    else
        echo -e "${RED}Error: Failed to create OIDC provider${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ OIDC provider already exists: ${OIDC_PROVIDER_ARN}${NC}"
fi

# Create trust policy in current directory
echo -e "\n${YELLOW}Creating trust policy...${NC}"
cat > ./trust-policy.json <<EOFTP
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:${GITHUB_ORG}/${GITHUB_REPO}:*"
        }
      }
    }
  ]
}
EOFTP

echo -e "${GREEN}✓ Trust policy created${NC}"

# Create IAM role
ROLE_NAME="GitHubActionsRole-EKS-MultiService"
echo -e "\n${YELLOW}Creating IAM role: ${ROLE_NAME}...${NC}"

# Check if role already exists
ROLE_EXISTS=$(aws iam get-role --role-name ${ROLE_NAME} 2>/dev/null)

if [ $? -eq 0 ]; then
    echo -e "${YELLOW}Role already exists. Updating trust policy...${NC}"
    aws iam update-assume-role-policy \
        --role-name ${ROLE_NAME} \
        --policy-document file://./trust-policy.json
    echo -e "${GREEN}✓ Trust policy updated${NC}"
else
    aws iam create-role \
        --role-name ${ROLE_NAME} \
        --assume-role-policy-document file://./trust-policy.json \
        --description "Role for GitHub Actions to manage EKS infrastructure" \
        --tags Key=Purpose,Value=GitHubActions Key=Project,Value=EKS-MultiService
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ IAM role created successfully${NC}"
    else
        echo -e "${RED}Error: Failed to create IAM role${NC}"
        exit 1
    fi
fi

# Create custom policy for Terraform operations
echo -e "\n${YELLOW}Creating custom IAM policy for Terraform operations...${NC}"
POLICY_NAME="GitHubActions-Terraform-EKS-Policy"

cat > ./terraform-policy.json <<'EOFPOLICY'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "eks:*",
        "iam:*",
        "logs:*",
        "s3:*",
        "dynamodb:*",
        "rds:*",
        "elasticache:*",
        "secretsmanager:*",
        "kms:*",
        "elasticloadbalancing:*",
        "autoscaling:*",
        "cloudwatch:*",
        "route53:*",
        "acm:*",
        "sts:*"
      ],
      "Resource": "*"
    }
  ]
}
EOFPOLICY

# Check if policy exists
POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='${POLICY_NAME}'].Arn" --output text)

if [ -z "$POLICY_ARN" ]; then
    POLICY_ARN=$(aws iam create-policy \
        --policy-name ${POLICY_NAME} \
        --policy-document file://./terraform-policy.json \
        --description "Policy for GitHub Actions to manage EKS infrastructure via Terraform" \
        --tags Key=Purpose,Value=GitHubActions Key=Project,Value=EKS-MultiService \
        --query 'Policy.Arn' \
        --output text)
    echo -e "${GREEN}✓ Custom policy created: ${POLICY_ARN}${NC}"
else
    echo -e "${GREEN}✓ Policy already exists: ${POLICY_ARN}${NC}"
fi

# Attach policy to role
echo -e "\n${YELLOW}Attaching policy to role...${NC}"
aws iam attach-role-policy \
    --role-name ${ROLE_NAME} \
    --policy-arn ${POLICY_ARN}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Policy attached successfully${NC}"
fi

# Clean up temporary files
rm -f ./trust-policy.json ./terraform-policy.json

# Display summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo -e "1. Add this secret to your GitHub repository:"
echo -e "   ${GREEN}Repository → Settings → Secrets and variables → Actions → New repository secret${NC}"
echo ""
echo -e "   Secret Name:  ${GREEN}AWS_ROLE_ARN${NC}"
echo -e "   Secret Value: ${GREEN}arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}${NC}"
echo ""
echo -e "2. Your GitHub Actions workflow should use:"
echo -e "   ${GREEN}aws-actions/configure-aws-credentials@v4${NC}"
echo -e "   with:"
echo -e "     ${GREEN}role-to-assume: \${{ secrets.AWS_ROLE_ARN }}${NC}"
echo -e "     ${GREEN}aws-region: us-east-1${NC}"
echo ""
echo -e "3. The OIDC provider ARN is:"
echo -e "   ${GREEN}${OIDC_PROVIDER_ARN}${NC}"
echo ""
echo -e "${YELLOW}Note: The role has been configured to trust this repository:${NC}"
echo -e "   ${GREEN}${GITHUB_ORG}/${GITHUB_REPO}${NC}"
echo ""
echo -e "${RED}Important: For production use, consider using more restrictive IAM policies!${NC}"
echo ""