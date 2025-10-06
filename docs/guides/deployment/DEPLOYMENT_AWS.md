# FakeAI AWS Deployment Guide

This guide covers deploying FakeAI on Amazon Web Services (AWS) using various services including EC2, ECS/Fargate, Lambda, and more.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [EC2 Deployment](#ec2-deployment)
3. [ECS/Fargate Deployment](#ecsfargate-deployment)
4. [Lambda Deployment](#lambda-deployment)
5. [Application Load Balancer Configuration](#application-load-balancer-configuration)
6. [Auto-Scaling Setup](#auto-scaling-setup)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- AWS CLI installed and configured
- AWS account with appropriate permissions
- Docker installed (for container deployments)
- Python 3.10+ installed locally

### AWS Permissions

Ensure your IAM user/role has permissions for:
- EC2 (launch instances, security groups)
- ECS (create clusters, task definitions, services)
- Lambda (create functions, manage roles)
- CloudWatch (logs, metrics)
- ALB (create load balancers, target groups)
- Auto Scaling (create policies, groups)

### Install AWS CLI

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Region, Output format
```

---

## EC2 Deployment

Deploy FakeAI on Amazon EC2 instances for full control over the environment.

### Step 1: Launch EC2 Instance

```bash
# Create security group
aws ec2 create-security-group \
  --group-name fakeai-sg \
  --description "Security group for FakeAI server"

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-name fakeai-sg \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name fakeai-sg \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# Launch instance (Ubuntu 22.04)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --count 1 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups fakeai-sg \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=fakeai-server}]'
```

### Step 2: Connect and Install

```bash
# SSH into instance
ssh -i your-key-pair.pem ubuntu@<instance-public-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# Create application directory
mkdir -p /opt/fakeai
cd /opt/fakeai

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install FakeAI
pip install fakeai
```

### Step 3: Configure FakeAI

```bash
# Create environment file
cat > /opt/fakeai/.env <<EOF
FAKEAI_HOST=0.0.0.0
FAKEAI_PORT=8000
FAKEAI_DEBUG=false
FAKEAI_REQUIRE_API_KEY=true
FAKEAI_API_KEYS=sk-prod-key-1,sk-prod-key-2
FAKEAI_RESPONSE_DELAY=0.5
FAKEAI_RANDOM_DELAY=true
EOF

# Set permissions
chmod 600 /opt/fakeai/.env
```

### Step 4: Create Systemd Service

```bash
# Create service file
sudo tee /etc/systemd/system/fakeai.service > /dev/null <<EOF
[Unit]
Description=FakeAI OpenAI-Compatible API Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/fakeai
Environment="PATH=/opt/fakeai/venv/bin"
EnvironmentFile=/opt/fakeai/.env
ExecStart=/opt/fakeai/venv/bin/fakeai-server --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable fakeai
sudo systemctl start fakeai

# Check status
sudo systemctl status fakeai
```

### Step 5: Verify Deployment

```bash
# Test locally
curl http://localhost:8000/health

# Test from outside
curl http://<instance-public-ip>:8000/health
```

### EC2 Best Practices

1. **Use Elastic IPs**: Assign an Elastic IP for stable addressing
2. **Enable CloudWatch Logs**: Stream application logs to CloudWatch
3. **Regular Backups**: Create AMI snapshots regularly
4. **Security**: Restrict security group access to known IPs
5. **Monitoring**: Set up CloudWatch alarms for CPU, memory, disk

---

## ECS/Fargate Deployment

Deploy FakeAI as a container on Amazon ECS with Fargate for serverless container management.

### Step 1: Create Docker Image

```dockerfile
# Create Dockerfile
cat > Dockerfile <<EOF
FROM python:3.10-slim

WORKDIR /app

# Install FakeAI
RUN pip install --no-cache-dir fakeai

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run server
CMD ["fakeai-server", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Build image
docker build -t fakeai:latest .
```

### Step 2: Push to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name fakeai

# Get login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag fakeai:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/fakeai:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/fakeai:latest
```

### Step 3: Create ECS Cluster

```bash
# Create cluster
aws ecs create-cluster --cluster-name fakeai-cluster

# Create log group
aws logs create-log-group --log-group-name /ecs/fakeai
```

### Step 4: Create Task Definition

```json
{
  "family": "fakeai-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "fakeai",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/fakeai:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FAKEAI_HOST",
          "value": "0.0.0.0"
        },
        {
          "name": "FAKEAI_PORT",
          "value": "8000"
        },
        {
          "name": "FAKEAI_DEBUG",
          "value": "false"
        },
        {
          "name": "FAKEAI_REQUIRE_API_KEY",
          "value": "true"
        }
      ],
      "secrets": [
        {
          "name": "FAKEAI_API_KEYS",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:fakeai/api-keys"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/fakeai",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 10
      }
    }
  ]
}
```

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 5: Create ECS Service

```bash
# Create service
aws ecs create-service \
  --cluster fakeai-cluster \
  --service-name fakeai-service \
  --task-definition fakeai-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/fakeai-tg/abc123,containerName=fakeai,containerPort=8000"
```

### Step 6: Verify Deployment

```bash
# List tasks
aws ecs list-tasks --cluster fakeai-cluster --service-name fakeai-service

# Describe task
aws ecs describe-tasks --cluster fakeai-cluster --tasks <task-id>

# View logs
aws logs tail /ecs/fakeai --follow
```

### ECS/Fargate Best Practices

1. **Use Secrets Manager**: Store API keys in AWS Secrets Manager
2. **Health Checks**: Configure both container and ALB health checks
3. **Resource Limits**: Set appropriate CPU and memory limits
4. **Blue/Green Deployments**: Use CodeDeploy for zero-downtime updates
5. **Monitoring**: Enable Container Insights for detailed metrics

---

## Lambda Deployment

Deploy FakeAI on AWS Lambda for event-driven, serverless operation. Note: Lambda has limitations for long-running HTTP servers.

### Lambda Adapter Approach

Use Mangum to adapt FastAPI to Lambda:

```python
# lambda_handler.py
from mangum import Mangum
from fakeai.app import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")
```

### Step 1: Create Deployment Package

```bash
# Create directory
mkdir fakeai-lambda
cd fakeai-lambda

# Install dependencies
pip install fakeai mangum -t .

# Add handler
cat > lambda_handler.py <<EOF
from mangum import Mangum
from fakeai.app import app

handler = Mangum(app, lifespan="off")
EOF

# Create ZIP
zip -r fakeai-lambda.zip .
```

### Step 2: Create Lambda Function

```bash
# Create execution role
aws iam create-role \
  --role-name fakeai-lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach basic execution policy
aws iam attach-role-policy \
  --role-name fakeai-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create function
aws lambda create-function \
  --function-name fakeai \
  --runtime python3.10 \
  --role arn:aws:iam::<account-id>:role/fakeai-lambda-role \
  --handler lambda_handler.handler \
  --zip-file fileb://fakeai-lambda.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{FAKEAI_RESPONSE_DELAY=0.1,FAKEAI_REQUIRE_API_KEY=true}"
```

### Step 3: Create API Gateway

```bash
# Create REST API
aws apigateway create-rest-api \
  --name fakeai-api \
  --description "FakeAI API Gateway"

# Get root resource ID
API_ID=$(aws apigateway get-rest-apis --query "items[?name=='fakeai-api'].id" --output text)
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID --query "items[?path=='/'].id" --output text)

# Create proxy resource
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part '{proxy+}'

RESOURCE_ID=$(aws apigateway get-resources --rest-api-id $API_ID --query "items[?path=='/{proxy+}'].id" --output text)

# Create ANY method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method ANY \
  --authorization-type NONE

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method ANY \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:<account-id>:function:fakeai/invocations

# Deploy API
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod
```

### Step 4: Grant API Gateway Permission

```bash
# Add Lambda permission
aws lambda add-permission \
  --function-name fakeai \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:<account-id>:$API_ID/*/*"
```

### Step 5: Test Deployment

```bash
# Get API URL
API_URL="https://$API_ID.execute-api.us-east-1.amazonaws.com/prod"

# Test health endpoint
curl $API_URL/health

# Test chat completion
curl $API_URL/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Lambda Limitations

1. **Timeout**: Maximum 15 minutes (29 seconds for API Gateway)
2. **Streaming**: Not supported through API Gateway
3. **Cold Starts**: Initial requests may be slower
4. **Package Size**: 50MB zipped, 250MB unzipped
5. **Concurrency**: Default 1000 concurrent executions per region

### Lambda Best Practices

1. **Use Provisioned Concurrency**: Reduce cold start latency
2. **Optimize Package Size**: Only include necessary dependencies
3. **Set Appropriate Timeout**: Balance cost vs functionality
4. **Use Environment Variables**: Store configuration
5. **Enable X-Ray**: Trace requests for debugging

---

## Application Load Balancer Configuration

Set up an Application Load Balancer to distribute traffic across multiple FakeAI instances.

### Step 1: Create Target Group

```bash
# Create target group
aws elbv2 create-target-group \
  --name fakeai-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-12345 \
  --health-check-enabled \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --matcher HttpCode=200
```

### Step 2: Create Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name fakeai-alb \
  --subnets subnet-12345 subnet-67890 \
  --security-groups sg-12345 \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4

# Get ALB ARN
ALB_ARN=$(aws elbv2 describe-load-balancers --names fakeai-alb --query "LoadBalancers[0].LoadBalancerArn" --output text)
```

### Step 3: Create Listener

```bash
# Create HTTP listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/fakeai-tg/abc123

# Create HTTPS listener (optional)
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:us-east-1:<account-id>:certificate/abc123 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/fakeai-tg/abc123
```

### Step 4: Register Targets

```bash
# For EC2 instances
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/fakeai-tg/abc123 \
  --targets Id=i-12345 Id=i-67890

# For ECS, targets are registered automatically by the service
```

### Step 5: Configure Advanced Settings

```bash
# Enable access logs
aws elbv2 modify-load-balancer-attributes \
  --load-balancer-arn $ALB_ARN \
  --attributes \
    Key=access_logs.s3.enabled,Value=true \
    Key=access_logs.s3.bucket,Value=my-alb-logs \
    Key=access_logs.s3.prefix,Value=fakeai

# Enable connection draining
aws elbv2 modify-target-group-attributes \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/fakeai-tg/abc123 \
  --attributes \
    Key=deregistration_delay.timeout_seconds,Value=30 \
    Key=stickiness.enabled,Value=true \
    Key=stickiness.type,Value=lb_cookie
```

### ALB Best Practices

1. **Health Checks**: Use /health endpoint with appropriate thresholds
2. **SSL/TLS**: Always use HTTPS in production
3. **Access Logs**: Enable for debugging and auditing
4. **Connection Draining**: Allow graceful shutdown
5. **Sticky Sessions**: Enable if needed for stateful operations

---

## Auto-Scaling Setup

Configure auto-scaling to handle variable load automatically.

### EC2 Auto Scaling

#### Step 1: Create Launch Template

```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name fakeai-lt \
  --version-description "FakeAI launch template" \
  --launch-template-data '{
    "ImageId": "ami-0c55b159cbfafe1f0",
    "InstanceType": "t3.medium",
    "KeyName": "your-key-pair",
    "SecurityGroupIds": ["sg-12345"],
    "UserData": "'$(base64 -w0 user-data.sh)'",
    "IamInstanceProfile": {"Name": "fakeai-instance-profile"},
    "TagSpecifications": [{
      "ResourceType": "instance",
      "Tags": [{"Key": "Name", "Value": "fakeai-asg-instance"}]
    }]
  }'
```

#### Step 2: Create Auto Scaling Group

```bash
# Create ASG
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name fakeai-asg \
  --launch-template LaunchTemplateName=fakeai-lt,Version='$Latest' \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 2 \
  --default-cooldown 300 \
  --health-check-type ELB \
  --health-check-grace-period 300 \
  --vpc-zone-identifier "subnet-12345,subnet-67890" \
  --target-group-arns arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/fakeai-tg/abc123
```

#### Step 3: Create Scaling Policies

```bash
# Scale up policy (CPU > 70%)
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name fakeai-asg \
  --policy-name scale-up \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    },
    "TargetValue": 70.0
  }'

# Scale based on request count
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name fakeai-asg \
  --policy-name scale-on-requests \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ALBRequestCountPerTarget",
      "ResourceLabel": "app/fakeai-alb/abc123/targetgroup/fakeai-tg/xyz789"
    },
    "TargetValue": 1000.0
  }'
```

### ECS Auto Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/fakeai-cluster/fakeai-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy (CPU)
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/fakeai-cluster/fakeai-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "TargetValue": 70.0,
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'

# Create scaling policy (Memory)
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/fakeai-cluster/fakeai-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name memory-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageMemoryUtilization"
    },
    "TargetValue": 80.0,
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'
```

### Auto-Scaling Best Practices

1. **Minimum Capacity**: Always have at least 2 instances for high availability
2. **Cooldown Periods**: Set appropriate cooldown to avoid flapping
3. **Multiple Metrics**: Use both CPU and request count
4. **Testing**: Load test to verify scaling behavior
5. **Alarms**: Set CloudWatch alarms for scaling events

---

## Monitoring and Logging

### CloudWatch Metrics

```bash
# Create custom metric filter for logs
aws logs put-metric-filter \
  --log-group-name /ecs/fakeai \
  --filter-name request-count \
  --filter-pattern '[timestamp, request_id, level, message="*request*"]' \
  --metric-transformations \
    metricName=RequestCount,metricNamespace=FakeAI,metricValue=1

# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name fakeai-dashboard \
  --dashboard-body file://dashboard.json
```

### CloudWatch Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name fakeai-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ServiceName,Value=fakeai-service Name=ClusterName,Value=fakeai-cluster

# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name fakeai-high-errors \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### X-Ray Tracing

```bash
# Enable X-Ray for Lambda
aws lambda update-function-configuration \
  --function-name fakeai \
  --tracing-config Mode=Active

# For ECS, add X-Ray daemon as sidecar container
```

### Monitoring Best Practices

1. **Set Meaningful Alarms**: CPU, memory, error rate, latency
2. **Use Dashboards**: Create centralized dashboards
3. **Enable X-Ray**: Trace requests across services
4. **Log Aggregation**: Use CloudWatch Insights for log analysis
5. **Cost Monitoring**: Track costs with AWS Cost Explorer

---

## Troubleshooting

### Common Issues

#### Issue: Service Not Starting

```bash
# Check ECS service events
aws ecs describe-services --cluster fakeai-cluster --services fakeai-service

# Check task status
aws ecs describe-tasks --cluster fakeai-cluster --tasks <task-id>

# View logs
aws logs tail /ecs/fakeai --follow
```

#### Issue: Health Check Failures

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/fakeai-tg/abc123

# Verify health endpoint
curl http://<instance-ip>:8000/health
```

#### Issue: High Latency

```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/fakeai-alb/abc123 \
  --start-time 2025-10-04T00:00:00Z \
  --end-time 2025-10-04T23:59:59Z \
  --period 300 \
  --statistics Average

# Check task CPU/memory
aws ecs describe-tasks --cluster fakeai-cluster --tasks <task-id> | \
  jq '.tasks[0].containers[0].cpu, .tasks[0].containers[0].memory'
```

#### Issue: Auto-Scaling Not Working

```bash
# Check scaling activities
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name fakeai-asg \
  --max-records 10

# Check scaling policies
aws application-autoscaling describe-scaling-policies \
  --service-namespace ecs \
  --resource-id service/fakeai-cluster/fakeai-service
```

### Debug Commands

```bash
# View task logs
aws logs tail /ecs/fakeai --follow --format short

# Describe task details
aws ecs describe-tasks --cluster fakeai-cluster --tasks <task-id>

# Check service events
aws ecs describe-services --cluster fakeai-cluster --services fakeai-service | \
  jq '.services[0].events'

# View ALB access logs (from S3)
aws s3 sync s3://my-alb-logs/fakeai/ . --exclude "*" --include "*.log.gz"
```

---

## Cost Optimization

### EC2 Cost Savings

1. **Use Reserved Instances**: Save up to 75% for predictable workloads
2. **Spot Instances**: Save up to 90% for fault-tolerant workloads
3. **Right-Sizing**: Use t3.small/medium instead of t3.large if sufficient
4. **Auto-Scaling**: Scale down during off-peak hours

### ECS/Fargate Cost Savings

1. **Use Fargate Spot**: Save up to 70% on Fargate pricing
2. **Right-Size Tasks**: Use minimum CPU/memory needed
3. **Optimize Images**: Smaller images = faster starts = lower costs
4. **Scheduled Scaling**: Reduce capacity during off-hours

### Lambda Cost Savings

1. **Optimize Memory**: Balance memory vs execution time
2. **Provisioned Concurrency**: Only use when needed
3. **Request Batching**: Combine multiple operations
4. **Reduce Cold Starts**: Keep functions warm during peak times

---

## Security Best Practices

1. **Use IAM Roles**: Never hardcode credentials
2. **Secrets Manager**: Store API keys securely
3. **VPC Endpoints**: Keep traffic within AWS network
4. **Security Groups**: Principle of least privilege
5. **Enable Encryption**: At rest (EBS, S3) and in transit (TLS)
6. **Regular Updates**: Keep AMIs and containers updated
7. **CloudTrail**: Enable audit logging
8. **WAF**: Add AWS WAF for additional protection

---

## Next Steps

1. Set up CI/CD pipeline with CodePipeline
2. Implement blue/green deployments
3. Configure multi-region deployment
4. Set up disaster recovery plan
5. Implement comprehensive monitoring

For more information, see:
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [AWS Auto Scaling Documentation](https://docs.aws.amazon.com/autoscaling/)
