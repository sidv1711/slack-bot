# 🤖 AI-Powered Slack Bot - Microservice Architecture

An intelligent Slack bot with modular AI capabilities built on a scalable microservice architecture.

## 🏗️ Architecture Overview

```
┌─────────────────┐     HTTP API     ┌─────────────────┐
│   Slack Bot     │ ◄──────────────► │ AI Microservice │
│   (Port 8000)   │                  │   (Port 8001)   │
│                 │                  │                 │
│ • Slack Events  │                  │ • NL2SQL        │
│ • User Auth     │                  │ • Code Gen      │
│ • Responses     │                  │ • General Chat  │
└─────────────────┘                  └─────────────────┘
```

### 🎯 **Key Benefits**
- **Modularity**: Independent AI and Slack services
- **Scalability**: Scale AI processing independently
- **Maintainability**: Update AI without touching Slack code
- **Flexibility**: Easy AI provider swapping

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key
- Slack App credentials

### 1. Environment Setup
```bash
cp env.example .env
# Edit .env with your credentials
```

### 2. Start Services
```bash
docker-compose up --build
```

### 3. Verify Services
- **Slack Bot**: http://localhost:8000/health
- **AI Service**: http://localhost:8001/health  
- **API Docs**: http://localhost:8001/docs

## 🔧 Configuration

### Required Environment Variables
```bash
# Slack Configuration
SLACK_BOT_TOKEN=<SLACK_TOKEN>
SLACK_SIGNING_SECRET=your-signing-secret

# AI Configuration  
OPENAI_API_KEY=your-openai-key

# Authentication (Optional)
AUTH_URL=your-auth-url
AUTH_API_KEY=your-auth-key

# Database (Optional - for NL2SQL)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

## 🌐 API Endpoints

The AI microservice provides RESTful endpoints:

- `POST /api/v1/ai/process` - Main AI routing
- `POST /api/v1/nl2sql/convert` - Natural Language to SQL
- `POST /api/v1/code/generate` - Code generation
- `POST /api/v1/chat/respond` - General conversation
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## 🤖 Slack Commands

### Slash Commands
- `/hello` - Get a personalized greeting from the bot
- `/ai [question]` - Ask AI anything (automatically routes to appropriate service)
- `/test-executions [test_id] [limit]` - View test execution history
- `/connect-slack` - Connect your Slack workspace

### AI Capabilities
The bot automatically routes your requests to the most appropriate AI service:

1. **General Chat**
   - Natural dialogue and conversation
   - Question answering and explanations
   - Creative brainstorming
   - Problem discussion
   - Knowledge in science, technology, history, and more

2. **Code Generation**
   - Generate code in multiple languages:
     - Python, JavaScript, TypeScript
     - Java, Go, Rust
     - C++, C#, SQL
   - Features:
     - Function and class generation
     - Algorithm implementation
     - API client code
     - Data processing scripts
     - Test code generation
     - Code documentation

3. **NL2SQL (Database Queries)**
   - Convert natural language to SQL queries
   - Supported operations:
     - Filtering by test_uid, status, execution_time
     - Time-based queries (last week, yesterday, etc.)
     - Status filtering (failed, passed, etc.)
     - Results in formatted tables
   - Safety features:
     - SQL injection prevention
     - Read-only operations
     - Query validation

### Example Usage
```
# General Questions
/ai What is machine learning?
/ai Explain REST APIs to me

# Database Queries
/ai Show me failed tests from yesterday
/ai Count how many tests passed this week

# Code Generation
/ai Write a Python function to calculate fibonacci numbers
/ai Create a JavaScript function that validates emails

# Test Executions
/test-executions TEST_ID 5
/test-executions TEST_ID limit=10
```

## 🧪 Testing

### Run Architecture Tests
```bash
python test_microservice_architecture.py
```

### Run Unit Tests  
```bash
pytest tests/
```

## 🐳 Deployment

The application is deployed using Docker containers and Cloudflare tunnels for secure connectivity.

### RYVN Deployment

The bot is deployed using RYVN, a modern deployment platform that handles:
- Automated versioning and tagging
- Multi-component deployment
- Environment management
- Container registry integration

#### Components
The application consists of two main components:
1. **Web Server** (Port 8000)
   - Main Slack bot service
   - Handles Slack events and commands
   - Manages user authentication

2. **AI Service** (Port 8001)
   - Independent AI microservice
   - Handles NL2SQL, code generation, and general chat
   - Scalable independently

#### Environments
- **Staging**: Development environment
- **Production**: Live environment

#### Deployment Process
1. **Version Generation**
   - Automated version tagging
   - Semantic versioning support
   - Release notes generation

2. **Build & Push**
   - Multi-architecture Docker builds
   - Container registry integration
   - Automated security scanning

3. **Release Management**
   - Channel-based deployments
   - Stable channel for production
   - PR channel for testing

#### Configuration
The deployment is configured via `.github/ryvn.yml` (example configuration):
```yaml
name: slack-bot
registry:
  type: ecr
  region: us-west-2
components:
  - name: web-server
    type: service
    dockerfile: Dockerfile
    port: 8000
    image: slack-bot-web
  - name: ai-service
    type: service
    dockerfile: ai-microservice/Dockerfile
    port: 8001
    image: slack-bot-ai
environments:
  - name: staging
    channel: stable
    namespace: staging
channels:
  - name: stable
    branch: main
  - name: pr
    pull_request: true
```

### Cloudflare Tunnel
The application uses a Cloudflare tunnel for secure access:
- Secure edge connections for redundancy
- Automatic reconnection on failures
- End-to-end encryption

### CI/CD Pipeline
The CI/CD pipeline is configured to:
1. Run tests and security scans
2. Build multi-architecture Docker images
3. Push to GitHub Container Registry
4. Deploy to staging/production environments

Key files:
- `.github/workflows/ci.yml` for the main CI/CD pipeline

## 📁 Project Structure

```
├── src/                    # Main Slack bot service
│   ├── bot/               # Slack event handling
│   ├── services/          # HTTP client for AI service
│   └── config/            # Configuration
├── ai-microservice/       # Independent AI service
│   ├── src/
│   │   ├── api/          # REST API endpoints
│   │   ├── services/     # AI processing services
│   │   └── models/       # Request/response models
│   └── Dockerfile
├── tests/                 # Unit tests
├── scripts/              # Database setup scripts
└── docs/                 # Documentation
```

## 🔄 Adding New AI Services

The microservice architecture makes it easy to add new AI capabilities:

1. **Add Service**: Create new service in `ai-microservice/src/services/`
2. **Register**: Add to `AIRouterService` in `ai_router_service.py`
3. **API Endpoint**: Add REST endpoint in `api/routes.py`
4. **Deploy**: Restart AI microservice only

## 📚 Documentation

- **Architecture**: [MICROSERVICE_ARCHITECTURE.md](./MICROSERVICE_ARCHITECTURE.md)
- **API Docs**: http://localhost:8001/docs (when running)
- **Deployment**: [docs/deployment.md](./docs/deployment.md)

## 🛠️ Development

### Local Development
```bash
# Start main bot only
cd src && python -m uvicorn main:app --reload --port 8000

# Start AI service only  
cd ai-microservice && python -m uvicorn src.main:app --reload --port 8001
```

### Adding Features
- **Slack Features**: Modify `src/` directory
- **AI Features**: Modify `ai-microservice/` directory
- **Independent deployment** of each service

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes to appropriate service
4. Test with `test_microservice_architecture.py`
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ using FastAPI, Docker, and OpenAI**