# 🚀 Deployment Guide

This guide covers deploying the Slack Bot to various environments.

## 📋 **Prerequisites**

- Docker and Docker Compose installed
- GitHub account (for CI/CD)
- Cloud provider account (AWS, GCP, Azure, or similar)
- Domain name (for production)

## 🐳 **Local Development Deployment**

### **1. Using Docker Compose**

```bash
# Clone the repository
git clone https://github.com/your-org/slack-bot.git
cd slack-bot

# Copy environment file
cp env.example .env

# Edit .env with your actual values
nano .env

# Build and run
docker-compose up --build

# Run with database (optional)
docker-compose --profile with-db up --build

# Run with caching (optional)
docker-compose --profile with-cache up --build
```

### **2. Direct Python Execution**

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export $(cat .env | xargs)

# Run the application
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🏗️ **Production Deployment Options**

### **Option 1: Docker Container Platforms**

#### **Fly.io Deployment**

1. **Install Fly CLI**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Create fly.toml**
```toml
app = "your-slack-bot"
primary_region = "sjc"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"
  ENVIRONMENT = "production"

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"
```

3. **Deploy**
```bash
# Login to Fly
fly auth login

# Create app
fly apps create your-slack-bot

# Set secrets
fly secrets set SLACK_BOT_TOKEN=your-token
fly secrets set PROPELAUTH_API_KEY=your-key
# ... set all required secrets

# Deploy
fly deploy
```

#### **Railway Deployment**

1. **Connect GitHub Repository**
   - Go to [Railway](https://railway.app)
   - Connect your GitHub repository
   - Railway will auto-detect the Dockerfile

2. **Set Environment Variables**
   - In Railway dashboard, go to Variables
   - Add all required environment variables from `.env.example`

3. **Deploy**
   - Railway will automatically deploy on git push

#### **Heroku Deployment**

1. **Create heroku.yml**
```yaml
build:
  docker:
    web: Dockerfile
run:
  web: python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
```

2. **Deploy**
```bash
# Install Heroku CLI
# Create app
heroku create your-slack-bot

# Set stack to container
heroku stack:set container

# Set environment variables
heroku config:set SLACK_BOT_TOKEN=your-token
heroku config:set PROPELAUTH_API_KEY=your-key
# ... set all required variables

# Deploy
git push heroku main
```

### **Option 2: Kubernetes Deployment**

#### **Create Kubernetes Manifests**

1. **Deployment**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: slack-bot
  labels:
    app: slack-bot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: slack-bot
  template:
    metadata:
      labels:
        app: slack-bot
    spec:
      containers:
      - name: slack-bot
        image: ghcr.io/your-org/slack-bot:latest
        ports:
        - containerPort: 8000
        env:
        - name: PORT
          value: "8000"
        - name: ENVIRONMENT
          value: "production"
        envFrom:
        - secretRef:
            name: slack-bot-secrets
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

2. **Service**
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: slack-bot-service
spec:
  selector:
    app: slack-bot
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
```

3. **Ingress**
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: slack-bot-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: slack-bot-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: slack-bot-service
            port:
              number: 80
```

4. **Deploy to Kubernetes**
```bash
# Create namespace
kubectl create namespace slack-bot

# Create secrets
kubectl create secret generic slack-bot-secrets \
  --from-env-file=.env \
  --namespace=slack-bot

# Apply manifests
kubectl apply -f k8s/ --namespace=slack-bot

# Check deployment
kubectl get pods --namespace=slack-bot
```

### **Option 3: Cloud Provider Specific**

#### **AWS ECS Deployment**

1. **Create ECS Task Definition**
2. **Set up Application Load Balancer**
3. **Configure ECS Service**
4. **Use AWS Secrets Manager for environment variables**

#### **Google Cloud Run Deployment**

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT-ID/slack-bot

# Deploy to Cloud Run
gcloud run deploy slack-bot \
  --image gcr.io/PROJECT-ID/slack-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production
```

## 🔧 **Environment-Specific Configuration**

### **Staging Environment**

```bash
# Use staging branch
git checkout develop

# Set staging environment variables
ENVIRONMENT=staging
PROPELAUTH_URL=https://staging.propelauthtest.com
SLACK_OAUTH_REDIRECT_URI=https://staging.your-domain.com/auth/slack/callback
```

### **Production Environment**

```bash
# Use main branch
git checkout main

# Set production environment variables
ENVIRONMENT=production
DEVELOPMENT_MODE=false
LOG_LEVEL=INFO
SSL_REDIRECT=true
SECURE_COOKIES=true
```

## 📊 **Monitoring & Observability**

### **Health Checks**

The application provides several health check endpoints:
- `/healthz` - Basic health check
- `/health` - Detailed health information
- `/` - Root health check

### **Logging**

Configure structured logging:
```bash
LOG_LEVEL=INFO  # or DEBUG, WARNING, ERROR
```

### **Metrics** (Optional)

Enable Prometheus metrics:
```bash
ENABLE_METRICS=true
METRICS_PORT=9090
```

### **Error Tracking** (Optional)

Configure Sentry:
```bash
SENTRY_DSN=your-sentry-dsn
```

## 🔒 **Security Considerations**

### **Environment Variables**

- Never commit `.env` files to git
- Use secret management services in production
- Rotate secrets regularly

### **HTTPS/TLS**

- Always use HTTPS in production
- Configure SSL redirect: `SSL_REDIRECT=true`
- Use secure cookies: `SECURE_COOKIES=true`

### **Network Security**

- Restrict access to health endpoints if needed
- Use firewalls and security groups
- Enable rate limiting: `RATE_LIMIT_ENABLED=true`

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Container won't start**
   - Check environment variables
   - Verify Docker image builds locally
   - Check logs: `docker logs container-name`

2. **Health checks failing**
   - Verify application is listening on correct port
   - Check if all required environment variables are set
   - Test health endpoint manually

3. **Slack commands not working**
   - Verify Slack app configuration
   - Check webhook URLs are accessible
   - Validate signing secret

4. **PropelAuth integration issues**
   - Verify OAuth redirect URIs match
   - Check PropelAuth client credentials
   - Ensure PropelAuth URL is correct

### **Debugging Commands**

```bash
# Check container logs
docker logs slack-bot

# Execute shell in container
docker exec -it slack-bot /bin/bash

# Test health endpoint
curl http://localhost:8000/healthz

# Check environment variables
docker exec slack-bot env | grep SLACK
```

## 📈 **Scaling Considerations**

### **Horizontal Scaling**

- The application is stateless and can be scaled horizontally
- Use load balancers to distribute traffic
- Consider using Redis for session storage if needed

### **Database Scaling**

- Supabase handles scaling automatically
- Consider read replicas for high-traffic scenarios
- Implement connection pooling if needed

### **Performance Optimization**

- Enable caching with Redis
- Use CDN for static assets
- Implement request rate limiting
- Monitor response times and optimize slow endpoints

## 🔄 **CI/CD Pipeline**

The GitHub Actions pipeline automatically:

1. **Tests** code on every push/PR
2. **Builds** Docker images
3. **Scans** for security vulnerabilities
4. **Deploys** to staging (develop branch)
5. **Deploys** to production (main branch)

### **Manual Deployment**

If you need to deploy manually:

```bash
# Build image
docker build -t slack-bot .

# Tag for registry
docker tag slack-bot your-registry/slack-bot:latest

# Push to registry
docker push your-registry/slack-bot:latest

# Deploy to your platform
# (platform-specific commands)
``` 