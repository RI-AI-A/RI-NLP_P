# Ollama Setup Guide

## Quick Start

### 1. Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Windows:**
Download from https://ollama.com/download

### 2. Start Ollama Service

```bash
# Start Ollama (runs in background)
ollama serve
```

### 3. Pull the LLM Model

```bash
# Pull Llama 3.2 3B (recommended for this project)
ollama pull llama3.2:3b

# Alternative models:
# ollama pull mistral:7b        # Larger, more capable
# ollama pull llama3.2:1b        # Smaller, faster
```

### 4. Test Ollama

```bash
# Test the model
ollama run llama3.2:3b "Hello, how are you?"
```

### 5. Configure the NLP Service

Update your `.env` file:
```bash
USE_LLM=true
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
LLM_BASE_URL=http://localhost:11434
```

### 6. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 7. Start the NLP Service

```bash
uvicorn api_service.main:app --host 0.0.0.0 --port 8000 --reload
```

## Model Recommendations

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| llama3.2:1b | ~1GB | Very Fast | Good | Development, testing |
| llama3.2:3b | ~2GB | Fast | Very Good | **Recommended for MVP** |
| mistral:7b | ~4GB | Medium | Excellent | Production with GPU |
| llama3.1:8b | ~5GB | Slower | Excellent | High-quality responses |

## Troubleshooting

### Ollama Not Running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve
```

### Model Not Found
```bash
# List installed models
ollama list

# Pull the model if missing
ollama pull llama3.2:3b
```

### Slow Performance
- Use a smaller model (llama3.2:1b)
- Reduce `LLM_MAX_TOKENS` in `.env`
- Enable caching: `ENABLE_LLM_CACHING=true`

### Out of Memory
- Use a smaller model
- Close other applications
- Reduce concurrent requests

## Switching to Cloud API (Optional)

If Ollama performance is insufficient, you can switch to OpenAI:

```bash
# In .env
USE_LLM=true
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-your-key-here
```

Or Anthropic:
```bash
# In .env
USE_LLM=true
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-haiku-20241022
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Performance Tips

1. **Enable Caching**: Set `ENABLE_LLM_CACHING=true` to cache responses
2. **Adjust Temperature**: Lower temperature (0.3-0.5) for more consistent results
3. **Limit Tokens**: Set `LLM_MAX_TOKENS=300` for faster responses
4. **Use GPU**: Ollama automatically uses GPU if available (NVIDIA/AMD)

## Verification

Test the LLM integration:
```bash
# Test endpoint
curl -X POST http://localhost:8000/nlp/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What were the sales yesterday?",
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_role": "manager"
  }'
```

Check logs for LLM usage:
```bash
tail -f api.log | grep LLM
```
