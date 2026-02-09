# Retail Intelligence NLP Service

Production-grade NLP microservice for a Retail Intelligence Decision Support System. This service provides intent classification, slot filling, query routing, RAG-lite retrieval, and comprehensive guardrails for natural language queries about retail analytics.

## 🎯 Overview

This NLP service is designed to:
- Classify user intents (KPI queries, branch status, tasks, events, promotions, chitchat)
- Extract entities and slots from natural language queries
- Route queries to appropriate backend API endpoints
- Generate explainable responses using RAG-lite (FAISS + Sentence-Transformers)
- Apply safety guardrails (profanity, PII, hallucination detection, confidence thresholding)
- Log all queries and collect user feedback for continuous improvement

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  Routers: /nlp/query | /nlp/logs | /nlp/feedback | /health │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │ Orchestration Service │
         └───────────┬───────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
┌────▼────┐   ┌─────▼──────┐  ┌────▼─────┐
│ Intent  │   │    Slot    │  │  Query   │
│Classifier│   │   Filling  │  │  Router  │
└────┬────┘   └─────┬──────┘  └────┬─────┘
     │              │              │
     └──────────────┼──────────────┘
                    │
         ┌──────────▼──────────┐
         │   Guardrails Check  │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  Response Generator │
         │   (RAG-lite FAISS)  │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  PostgreSQL Logging │
         └─────────────────────┘
```

## 📋 Features

### NLP Capabilities
- **Intent Classification**: LLM-powered (Ollama/OpenAI/Anthropic) with rule-based fallback
- **Slot Filling**: LLM-powered entity extraction with context understanding
- **Query Routing**: Maps intents + slots to REST API endpoints (inc. Situation/Recommendation APIs)
- **RAG-lite Retrieval**: FAISS vector search over knowledge base (KPI docs, business rules, analytics docs)
- **Response Generation**: Natural language generation using LLM with retrieved context

### Safety & Quality
- **Profanity Filter**: Blocks inappropriate language
- **PII Redaction**: Detects and removes emails, phone numbers, SSNs, credit cards
- **Hallucination Detection**: Basic checks for unsupported claims
- **Confidence Thresholding**: Rejects low-confidence predictions
- **Scope Validation**: Ensures queries are within retail domain

### Production Features
- **Structured Logging**: JSON logs with structlog
- **Database Logging**: PostgreSQL with query logs and user feedback
- **Health Checks**: Comprehensive health endpoint
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Database Migrations**: Alembic for schema versioning

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 15+
- **Ollama** (for LLM support) - See [OLLAMA_SETUP.md](OLLAMA_SETUP.md)

### Installation & Run

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Set up Ollama (for LLM support)
# See OLLAMA_SETUP.md for detailed instructions
ollama serve  # In a separate terminal
ollama pull llama3.2:3b

# Set up environment
cp .env.example .env
# Edit .env with your database credentials and LLM settings

# Run database migrations
alembic upgrade head

# Start the service
uvicorn api_service.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📚 API Documentation

### POST /nlp/query

Process a natural language query.

**Request:**
```json
{
  "query": "How busy was branch A yesterday?",
  "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_role": "manager"
}
```

**Response:**
```json
{
  "intent": "kpi_query",
  "slots": {
    "branch_id": "A",
    "time_range": "yesterday",
    "kpi_type": "traffic"
  },
  "routed_endpoint": "/kpis/branch/A?date=yesterday&kpi_type=traffic",
  "response_text": "I'll retrieve the traffic KPI data for A during yesterday...",
  "confidence": 0.91,
  "sources": ["kpi_docs", "business_rules"]
}
```

### POST /nlp/feedback

Submit user feedback for a query.

**Request:**
```json
{
  "query_id": "123e4567-e89b-12d3-a456-426614174000",
  "rating": 5,
  "comment": "Very helpful response"
}
```

### GET /nlp/logs

Retrieve query logs with filtering.

**Query Parameters:**
- `conversation_id`: Filter by conversation
- `user_role`: Filter by role (manager/analyst/staff)
- `intent`: Filter by intent
- `start_date`: Filter by start date
- `end_date`: Filter by end date
- `limit`: Number of results (default: 100, max: 1000)
- `offset`: Pagination offset

### GET /health

Comprehensive health check.

**Response:**
```json
{
  "status": "healthy",
  "details": {
    "api": "healthy",
    "database": "healthy",
    "intent_classifier": "healthy",
    "retrieval_system": "healthy (13 documents)"
  }
}
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nlp_service --cov=api_service

# Run specific test file
pytest tests/test_intent_classifier.py -v

# Run specific test
pytest tests/test_query_routing.py::test_kpi_query_routing -v
```

## 📊 Evaluation

Run offline evaluation on labeled data:

```bash
# Prepare CSV file with columns: query, true_intent, true_slots
# Example: evaluation_data.csv

# Run evaluation
python pipelines/evaluation.py evaluation_data.csv evaluation_report.json
```

**Metrics Calculated:**
- Intent Accuracy
- Slot F1 Score
- Confidence Calibration (ECE)
- Rejection Rate
- Query Resolution Rate

## 🔧 Configuration

### Environment Variables

See `.env.example` for all configuration options:

- **Database**: `DATABASE_URL`, `DATABASE_URL_SYNC`
- **API**: `API_HOST`, `API_PORT`, `API_WORKERS`
- **Models**: `INTENT_MODEL_NAME`, `EMBEDDING_MODEL_NAME`, `SPACY_MODEL`
- **FAISS**: `FAISS_INDEX_PATH`, `FAISS_TOP_K`
- **Thresholds**: `INTENT_CONFIDENCE_THRESHOLD`, `GUARDRAIL_CONFIDENCE_THRESHOLD`
- **Guardrails**: `ENABLE_PROFANITY_FILTER`, `ENABLE_PII_REDACTION`

### Model Configuration

The service supports two modes:

**LLM Mode (Default)**:
- **LLM Provider**: Ollama (local), OpenAI, or Anthropic
- **Default Model**: `llama3.2:3b` (Ollama)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- **Features**: Natural language understanding, context-aware responses

**Rule-Based Mode (Fallback)**:
- **Intent Classification**: `distilbert-base-uncased` or `facebook/bart-large-mnli`
- **NER**: `en_core_web_sm` (spaCy)
- **Response**: Template-based

## 🗄️ Database Schema

### nlp_queries_log
- `id` (UUID, PK)
- `conversation_id` (UUID, indexed)
- `user_role` (String)
- `query_text` (Text)
- `intent` (String, indexed)
- `confidence` (Float)
- `routed_endpoint` (String)
- `created_at` (DateTime, indexed)

### nlp_feedback
- `id` (UUID, PK)
- `query_id` (UUID, FK → nlp_queries_log)
- `rating` (Integer, 1-5)
- `comment` (Text, nullable)
- `created_at` (DateTime)

## 🔄 Integration Contract

This NLP service is designed to integrate with other microservices:

### Input Contract
- Accepts natural language queries via REST API
- Requires conversation_id and user_role for context
- Returns structured JSON with intent, slots, and routing information

### Output Contract
- **Never accesses CV service directly**
- **Only calls backend APIs** via routed endpoints
- **Returns structured + explainable outputs**
- **Can be replaced by LLM later** (same input/output format)

### Downstream Integration
All downstream systems can consume the JSON response:
- `routed_endpoint`: Use this to call the appropriate backend API
- `slots`: Extract parameters for API calls
- `response_text`: Display to user or use for further processing
- `confidence`: Use for filtering or user warnings

## 📦 Project Structure

```
retail-intel-nlp-backend/
├── nlp_service/              # Core NLP components
│   ├── intent_classifier.py  # BERT-based intent classification
│   ├── slot_filling.py       # spaCy NER + regex slot extraction
│   ├── query_router.py       # Intent → API endpoint mapping
│   ├── embedding_service.py  # Sentence-Transformers embeddings
│   ├── retrieval.py          # FAISS vector search
│   ├── response_generator.py # RAG-lite response generation
│   ├── guardrails.py         # Safety and quality checks
│   └── config.py             # NLP configuration
├── api_service/              # FastAPI application
│   ├── main.py               # FastAPI app setup
│   ├── routers/              # API endpoints
│   │   ├── nlp.py            # /nlp/query endpoint
│   │   ├── queries.py        # /nlp/logs endpoint
│   │   ├── feedback.py       # /nlp/feedback endpoint
│   │   └── health.py         # /health endpoint
│   ├── services/             # Business logic
│   │   ├── orchestration_service.py  # Main pipeline orchestration
│   │   ├── retrieval_service.py      # Retrieval wrapper
│   │   └── logging_service.py        # Structured logging
│   ├── deps.py               # FastAPI dependencies
│   └── config.py             # API configuration
├── db/                       # Database layer
│   ├── base.py               # SQLAlchemy base
│   ├── session.py            # Session management
│   ├── models.py             # Database models
│   └── migrations/           # Alembic migrations
├── schemas/                  # Pydantic schemas
│   ├── nlp_request.py        # Request schemas
│   ├── nlp_response.py       # Response schemas
│   ├── feedback.py           # Feedback schemas
│   └── logs.py               # Log schemas
├── pipelines/                # Offline pipelines
│   ├── preprocessing.py      # Text preprocessing
│   ├── evaluation.py         # Offline evaluation
│   └── offline_indexing.py   # FAISS index building
├── tests/                    # Unit tests
│   ├── test_intent_classifier.py
│   └── test_query_routing.py
├── requirements.txt          # Python dependencies
├── alembic.ini               # Alembic configuration
├── pytest.ini                # Pytest configuration
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🔐 Security Considerations

- **PII Protection**: Automatic detection and redaction of sensitive information
- **Input Validation**: Pydantic schemas validate all inputs
- **SQL Injection**: SQLAlchemy ORM prevents SQL injection
- **Rate Limiting**: Can be added via middleware (not included)
- **Authentication**: Placeholder in deps.py for future implementation

## 🚧 Future Enhancements

### LLM Replacement Path
This service is designed to be easily replaced by a larger LLM:
1. Keep the same API contract (input/output schemas)
2. Replace orchestration_service.py with LLM calls
3. Use the same guardrails and logging
4. Maintain backward compatibility

### Model Improvements
- Fine-tune BERT on retail-specific data
- Add custom NER model for retail entities
- Implement active learning from user feedback
- Add multi-language support

### Features
- Real-time model updates
- A/B testing framework
- Advanced hallucination detection
- Contextual conversation memory
- Multi-turn dialogue support

## 📝 License

This project is part of a B2B SaaS graduation project.

## 🤝 Contributing

This is an academic project. For questions or suggestions, please contact the project team.

## 📞 Support

For issues or questions:
1. Check the `/health` endpoint for service status
2. Review logs
3. Check database connectivity
4. Verify model downloads completed

## 🎓 Academic Context

This NLP service is designed to be:
- **Academically defensible**: Clear architecture, well-documented, testable
- **Modular**: Each component can be tested and replaced independently
- **Production-grade**: Follows best practices for logging, error handling, and monitoring
- **Future-proof**: Easy to replace with LLM while maintaining the same interface

---

**Version**: 1.0.0  
**Last Updated**: 2026-02-08
