# 🚀 Groq + Llama 3.1 Integration

This project now supports **Groq** with **Llama 3.1** models for ultra-fast, FREE AI inference!

## ⚡ Why Groq?

| Feature | Groq + Llama 3.1 | Gemini |
|---------|------------------|--------|
| **Speed** | 300+ tokens/sec | ~50 tokens/sec |
| **Cost** | FREE (beta) | Pay per token |
| **Context** | 128k tokens | 1M tokens |
| **Latency** | Ultra-low | Low |
| **Privacy** | Better (open model) | Cloud-based |

## 🎯 Models Available

| Model | Use Case | Speed | Quality |
|-------|----------|-------|---------|
| `llama-3.1-8b-instant` | Real-time chat | ⚡⚡⚡ Fastest | Good |
| `llama-3.1-70b-versatile` | Document analysis | ⚡⚡ Fast | Excellent |
| `llama-3.3-70b-versatile` | Case prediction | ⚡ Very Fast | Best |

## 🔧 Setup

### 1. Get Your FREE Groq API Key

1. Visit [console.groq.com](https://console.groq.com/keys)
2. Sign up / Log in
3. Click "Create API Key"
4. Copy the key

### 2. Add to Environment

Create or edit `.env` file in `django_project/`:

```env
# Groq API Key (PRIMARY - Ultra-fast, FREE)
GROQ_API_KEY=gsk_your_api_key_here

# Gemini API Key (FALLBACK - Optional)
GEMINI_API_KEY=your_gemini_key_here
```

### 3. Install Dependencies

```bash
pip install groq>=0.4.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## 🔄 Automatic Fallback

The system automatically:

1. **Tries Groq first** (faster, free)
2. **Falls back to Gemini** if Groq is unavailable
3. **Uses basic analysis** if no AI is configured

## 📍 Features Using Llama 3.1

| Feature | Model Used | Benefit |
|---------|------------|---------|
| **AI Chat** | llama-3.1-8b-instant | Instant responses |
| **Document Analysis** | llama-3.1-70b-versatile | Deep legal analysis |
| **Case Predictor** | llama-3.3-70b-versatile | Accurate predictions |
| **Voice Transcription** | whisper-large-v3-turbo | Fast transcription |

## 🔍 Check AI Status

Visit `/api/ai-status/` to see which AI provider is active:

```json
{
  "active_provider": "groq",
  "providers": {
    "groq": {
      "available": true,
      "tested": true,
      "models": {
        "fast": "llama-3.1-8b-instant",
        "balanced": "llama-3.1-70b-versatile",
        "quality": "llama-3.3-70b-versatile"
      },
      "speed": "300+ tokens/second",
      "cost": "FREE (beta)"
    },
    "gemini": {
      "available": true
    }
  }
}
```

## 🎨 UI Indicators

- **AI Assistant**: Shows "Powered by Llama 3.1 (Groq)" with ⚡ Ultra-Fast badge
- **Document Analyzer**: Shows "Analyzed by Llama 3.1" in results
- **Case Predictor**: Shows active AI provider badge

## 📦 Files Modified

| File | Changes |
|------|---------|
| `core/groq_service.py` | NEW - Complete Groq/Llama integration |
| `core/gemini_service.py` | Modified to use Groq as primary |
| `core/tasks.py` | Case predictor uses Groq first |
| `core/views.py` | Added `/api/ai-status/` endpoint |
| `core/urls.py` | Added AI status URL |
| `requirements.txt` | Added `groq>=0.4.0` |
| `.env.example` | Added `GROQ_API_KEY` |
| `settings.py` | Added `GROQ_API_KEY` config |
| Templates | Updated to show AI provider |

## 🧪 Testing the Integration

```python
# In Django shell
from core.groq_service import test_groq_connection, get_available_models

# Test connection
result = test_groq_connection()
print(result)  # {'success': True, 'message': 'Groq connection successful', ...}

# Get models
models = get_available_models()
print(models)
```

## 🚨 Troubleshooting

### "Groq not available"

1. Check `GROQ_API_KEY` is set in `.env`
2. Ensure `groq` package is installed: `pip install groq`
3. Verify API key at [console.groq.com](https://console.groq.com)

### Slow responses

- Make sure Groq is being used (check `/api/ai-status/`)
- If falling back to Gemini, check Groq API key

### Rate limits

Groq beta has generous limits, but if hit:
- Wait a few seconds between requests
- Consider using smaller model (`llama-3.1-8b-instant`) for chat

## 🔮 Future: Offline with Ollama

You can also run Llama 3.1 locally with Ollama:

```bash
# Install Ollama
ollama pull llama3.1:8b

# Run locally
ollama run llama3.1:8b
```

Then modify `groq_service.py` to use Ollama endpoint for fully offline operation.

---

**Enjoy ultra-fast, FREE AI-powered legal analysis!** ⚡🤖⚖️
