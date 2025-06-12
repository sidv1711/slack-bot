# AI Microservice

A standalone FastAPI microservice that provides AI-powered functionality for the Slack bot, including natural language to SQL conversion, code generation, and general chat capabilities.

## 🎯 **Purpose**

This microservice decouples AI functionality from the main Slack bot application, enabling:
- **Independent scaling** of AI services
- **Easy AI model swapping** without affecting the Slack bot
- **Service isolation** for better maintenance and testing
- **API-first design** for integration with multiple clients

## 🏗️ **Architecture**

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│   Slack Bot     │ ←──────────────→ │  AI Microservice│
│   (Main App)    │                  │                 │
│                 │                  │ ┌─────────────┐ │
│ ┌─────────────┐ │                  │ │AI Router    │ │
│ │SlackService │ │                  │ │Service      │ │
│ └─────────────┘ │                  │ └─────────────┘ │
│ ┌─────────────┐ │                  │ ┌─────────────┐ │
│ │AI Client    │ │                  │ │NL2SQL       │ │
│ │Service      │ │                  │ │Service      │ │
│ └─────────────┘ │                  │ └─────────────┘ │
└─────────────────┘                  │ ┌─────────────┐ │
                                     │ │Code Gen     │ │
                                     │ │Service      │ │
                                     │ └─────────────┘ │
                                     │ ┌─────────────┐ │
                                     │ │General Chat │ │
                                     │ │Service      │ │
                                     │ └─────────────┘ │
                                     └─────────────────┘
```

## 🚀 **Services Included**

### **1. AI Router Service**
- **Intent Classification**: Automatically routes requests to appropriate AI services
- **Confidence Scoring**: Provides routing confidence for transparency
- **Fallback Handling**: Routes to general chat when other services fail

### **2. NL2SQL Service**
- **Natural Language to SQL**: Converts questions to SQL queries
- **Query Execution**: Safely executes queries against the database
- **Table Formatting**: Returns beautifully formatted results for Slack
- **Safety Features**: SQL injection prevention, read-only access

### **3. Code Generation Service**
- **Multi-language Support**: Python, JavaScript, TypeScript, etc.
- **Context-aware**: Uses conversation context for better results
- **Usage Examples**: Provides code explanations and usage examples

### **4. General Chat Service**
- **Conversational AI**: Handles general questions and conversations
- **Follow-up Questions**: Suggests relevant follow-up questions
- **Context Retention**: Maintains conversation context

## 📡 **API Endpoints**

### **Main Processing Endpoint**
```
POST /api/v1/ai/process
{
  "user_input": "Show me failed tests from yesterday",
  "context": {"user_id": "123", "platform": "slack"}
}
```

### **Service-Specific Endpoints**
```
POST /api/v1/nl2sql/convert     # Natural Language to SQL
POST /api/v1/code/generate      # Code Generation  
POST /api/v1/chat/respond       # General Chat
```

### **Health & Monitoring**
```
GET  /health                    # Health check
GET  /api/v1/services/status    # Service status
GET  /api/v1/metrics           # Performance metrics
GET  /docs                     # Interactive API docs
```

## 🛠️ **Quick Start**

### **Standalone Development**
```bash
cd ai-microservice

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your OpenAI API key and database credentials

# Run the service
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload
```

### **With Docker**
```bash
# Build and run
docker-compose up --build

# Or run standalone
docker-compose -f ai-microservice/docker-compose.yml up --build
```

### **Integrated with Main App**
```bash
# From main project directory
docker-compose up --build
# This starts both the Slack bot and AI microservice
```

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Core
ENVIRONMENT=development|production
LOG_LEVEL=DEBUG|INFO|WARN|ERROR

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

# Database (for NL2SQL)
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Service
AI_SERVICE_PORT=8001
AI_SERVICE_HOST=0.0.0.0
```

## 🧪 **Testing**

### **Health Check**
```bash
curl http://localhost:8001/health
```

### **AI Processing**
```bash
curl -X POST http://localhost:8001/api/v1/ai/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Show me the last 5 test runs",
    "context": {"user_id": "test"}
  }'
```

### **NL2SQL Direct**
```bash
curl -X POST http://localhost:8001/api/v1/nl2sql/convert \
  -H "Content-Type: application/json" \
  -d '{
    "natural_query": "How many tests failed yesterday?",
    "execute_query": true
  }'
```

## 📊 **Monitoring**

- **Health Endpoint**: `/health` for service availability
- **Metrics Endpoint**: `/api/v1/metrics` for performance data
- **Logs**: Structured logging with configurable levels
- **Docker Health Checks**: Built-in container health monitoring

## 🔄 **Integration**

The AI microservice is designed to be easily swappable:

1. **Direct Integration**: Main app uses `AIClientService` for HTTP calls
2. **Service Discovery**: Configurable service URL via environment variables
3. **Fallback Strategy**: Graceful degradation when service is unavailable
4. **API Versioning**: Future-proof API design with versioned endpoints

## 🚢 **Deployment**

### **Docker Swarm**
```bash
docker stack deploy -c docker-compose.yml ai-services
```

### **Kubernetes**
```bash
kubectl apply -f k8s/ai-microservice.yaml
```

### **Cloud Services**
- **AWS**: Deploy with ECS or Lambda
- **Google Cloud**: Use Cloud Run or GKE
- **Azure**: Deploy with Container Instances or AKS

## 🔐 **Security**

- **API Key Authentication**: Optional API key for service-to-service auth
- **CORS Configuration**: Configurable cross-origin settings
- **Input Validation**: Pydantic models for request validation
- **SQL Injection Prevention**: Safe query generation and execution
- **Rate Limiting**: Built-in FastAPI rate limiting capabilities

## 📈 **Scaling**

- **Horizontal Scaling**: Deploy multiple instances behind a load balancer
- **Service Isolation**: Scale individual AI services independently
- **Resource Management**: Configure CPU/memory limits per service
- **Auto-scaling**: Use container orchestration for automatic scaling

## 🤝 **Contributing**

1. **Add New AI Services**: Extend `BaseAIService` class
2. **Update Router**: Register new services in `AIRouterService`
3. **Add Endpoints**: Create new API endpoints in `routes.py`
4. **Testing**: Add comprehensive tests for new functionality

---

**Built with FastAPI, OpenAI GPT, and ❤️ for modular AI architecture!** 