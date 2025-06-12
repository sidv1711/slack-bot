#!/bin/bash

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)

# Replace placeholders in task definition
sed "s/\${AWS_ACCOUNT_ID}/$AWS_ACCOUNT_ID/g; s/\${AWS_REGION}/$AWS_REGION/g" task-definition.json > task-definition-temp.json

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition-temp.json

# Clean up
rm task-definition-temp.json 