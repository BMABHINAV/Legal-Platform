"""
Groq AI integration with Llama 3.1 models for ultra-fast inference.

Models available:
- llama-3.1-70b-versatile: Best quality, good for complex legal analysis
- llama-3.1-8b-instant: Fastest, good for quick chat responses
- llama-3.3-70b-versatile: Latest 70B model with improved performance

Groq provides 300+ tokens/second inference speed, making it ideal for real-time chat.
"""
import os
import json
from django.conf import settings

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


# Model configurations
LLAMA_MODELS = {
    'fast': 'llama-3.1-8b-instant',      # Fastest responses, good for chat
    'balanced': 'llama-3.1-70b-versatile', # Best balance of speed and quality
    'quality': 'llama-3.3-70b-versatile',  # Highest quality for complex analysis
}

# Default model for different use cases
MODEL_FOR_CHAT = LLAMA_MODELS['fast']
MODEL_FOR_ANALYSIS = LLAMA_MODELS['balanced']
MODEL_FOR_PREDICTION = LLAMA_MODELS['quality']


def get_groq_client():
    """Initialize and return Groq client"""
    if not GROQ_AVAILABLE:
        return None
    
    api_key = getattr(settings, 'GROQ_API_KEY', '') or os.getenv('GROQ_API_KEY', '')
    if not api_key:
        return None
    
    return Groq(api_key=api_key)


def is_groq_available():
    """Check if Groq API is configured and available"""
    return get_groq_client() is not None


# ============================================================================
# CHAT FUNCTIONALITY
# ============================================================================

CHAT_SYSTEM_PROMPT = """You are a knowledgeable and helpful Indian Legal AI Assistant powered by Llama 3.1.

Your role:
1. Assist users with legal queries related to Indian law (IPC, CrPC, Contract Act, Constitution, etc.)
2. Explain complex legal concepts in simple, easy-to-understand language
3. Guide users on legal procedures and rights
4. Provide information in the user's preferred language

Important guidelines:
- Always clarify that you are an AI assistant and not a substitute for a qualified lawyer
- Be empathetic, professional, and accurate
- For specific cases or legal actions, strongly advise consulting a licensed advocate
- Keep responses concise but comprehensive
- Cite relevant laws and sections when applicable
- If unsure, acknowledge limitations and recommend professional consultation

You are fast, efficient, and always ready to help with legal knowledge."""


def get_multilingual_system_prompt(lang_code: str = 'en') -> str:
    """Get system prompt with language instruction."""
    from .language_service import get_ai_language_instruction
    
    lang_instruction = get_ai_language_instruction(lang_code)
    
    return f"""{CHAT_SYSTEM_PROMPT}

LANGUAGE INSTRUCTION: {lang_instruction}
Respond naturally in the requested language. Use the appropriate script (Devanagari for Hindi/Marathi, Tamil script for Tamil, etc.)
If the user writes in a regional language, continue the conversation in that language."""


def chat_with_llama(message: str, history: list = None, model: str = None, lang_code: str = 'en') -> dict:
    """
    Chat with Llama 3.1 via Groq for ultra-fast responses.
    
    Args:
        message: User's current message
        history: List of previous messages [{'role': 'user'|'assistant', 'content': '...'}]
        model: Specific model to use (defaults to fast model)
        lang_code: Language code for response (en, hi, ta, te, bn, mr, etc.)
    
    Returns:
        dict with 'success', 'text' or 'error'
    """
    client = get_groq_client()
    
    if not client:
        return {
            'success': False,
            'error': 'GROQ_API_KEY is not configured. Please add it to your environment variables to enable Llama 3.1.',
            'model_used': None
        }
    
    model = model or MODEL_FOR_CHAT
    
    try:
        # Build messages array with language-aware system prompt
        system_prompt = get_multilingual_system_prompt(lang_code)
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        if history:
            for msg in history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role in ['user', 'assistant'] and content:
                    messages.append({"role": role, "content": content})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Make API call
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            top_p=0.9,
        )
        
        reply = response.choices[0].message.content
        
        if not reply or not reply.strip():
            return {
                'success': False,
                'error': 'Received empty response from AI',
                'model_used': model
            }
        
        return {
            'success': True,
            'text': reply.strip(),
            'model_used': model,
            'tokens_used': {
                'prompt': response.usage.prompt_tokens,
                'completion': response.usage.completion_tokens,
                'total': response.usage.total_tokens
            }
        }
    
    except Exception as e:
        print(f"Groq Chat Error: {e}")
        return {
            'success': False,
            'error': str(e),
            'model_used': model
        }


# ============================================================================
# DOCUMENT ANALYSIS FUNCTIONALITY
# ============================================================================

ANALYSIS_SYSTEM_PROMPT = """You are an expert Indian legal document analyzer powered by Llama 3.1.

Your task is to analyze legal documents and provide comprehensive analysis in VALID JSON format only.
Do not include any text before or after the JSON. Just output pure JSON.

Analyze for:
1. Document type classification
2. Risk assessment of each clause
3. Plain language summary (in both English and Hindi)
4. Key points extraction
5. Legal references (IPC, CPC, Contract Act, etc.)
6. Overall health score (0-100, where 100 is safest)"""

ANALYSIS_USER_PROMPT = """Analyze this legal document and respond ONLY with valid JSON:

{
  "documentType": "rental-agreement|employment-contract|sale-deed|power-of-attorney|partnership-deed|loan-agreement|non-disclosure-agreement|legal-notice|court-order|will-testament|other",
  "typeLabel": "Human readable document type",
  "healthScore": 0-100,
  "risks": [
    {
      "originalText": "exact clause text from document",
      "riskLevel": "high|medium|low",
      "explanation": "why this is risky",
      "plainLanguage": "simple explanation anyone can understand",
      "legalReference": "relevant legal section if applicable",
      "suggestion": "recommended change"
    }
  ],
  "summary": {
    "keyPoints": ["point 1", "point 2"],
    "plainSummaryEn": "English summary in simple language",
    "plainSummaryHi": "Hindi summary in simple language",
    "parties": ["Party A", "Party B"],
    "effectiveDate": "if mentioned",
    "expiryDate": "if mentioned",
    "monetaryValue": "if mentioned"
  },
  "recommendations": ["recommendation 1", "recommendation 2"],
  "suggestedLawyerCategories": ["property", "civil", "corporate", etc]
}

DOCUMENT TEXT:
"""


def analyze_document_with_llama(text: str, filename: str, model: str = None) -> dict:
    """
    Analyze a legal document using Llama 3.1 via Groq.
    
    Args:
        text: Document text content
        filename: Name of the uploaded file
        model: Specific model to use (defaults to balanced model)
    
    Returns:
        dict with analysis results
    """
    client = get_groq_client()
    
    if not client:
        return None  # Fall back to other analysis methods
    
    model = model or MODEL_FOR_ANALYSIS
    
    try:
        messages = [
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": ANALYSIS_USER_PROMPT + text[:50000]}  # Limit text size
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,  # Lower temperature for more consistent analysis
            max_tokens=4096,
            top_p=0.95,
        )
        
        response_text = response.choices[0].message.content
        
        # Clean up the response
        cleaned_response = response_text.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        analysis = json.loads(cleaned_response)
        
        # Calculate risk level based on health score
        health_score = analysis.get('healthScore', 50)
        if health_score >= 80:
            risk_level = 'safe'
        elif health_score >= 60:
            risk_level = 'low'
        elif health_score >= 40:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        # Process risks
        risks = []
        for i, risk in enumerate(analysis.get('risks', [])):
            risks.append({
                'id': f'risk-{i + 1}',
                'original_text': risk.get('originalText', ''),
                'risk_level': risk.get('riskLevel', 'low'),
                'explanation': risk.get('explanation', ''),
                'plain_language': risk.get('plainLanguage', ''),
                'legal_reference': risk.get('legalReference'),
                'suggestion': risk.get('suggestion'),
            })
        
        # Build summary
        summary_data = analysis.get('summary', {})
        summary = {
            'type': analysis.get('documentType', 'other'),
            'type_label': analysis.get('typeLabel', 'Legal Document'),
            'key_points': summary_data.get('keyPoints', []),
            'plain_summary_en': summary_data.get('plainSummaryEn', 'Unable to generate summary.'),
            'plain_summary_hi': summary_data.get('plainSummaryHi', 'सारांश उत्पन्न करने में असमर्थ।'),
            'parties': summary_data.get('parties', []),
            'effective_date': summary_data.get('effectiveDate'),
            'expiry_date': summary_data.get('expiryDate'),
            'monetary_value': summary_data.get('monetaryValue'),
        }
        
        return {
            'file_name': filename,
            'file_type': filename.split('.')[-1] if '.' in filename else 'unknown',
            'document_type': analysis.get('documentType', 'other'),
            'health_score': min(100, max(0, health_score)),
            'risk_level': risk_level,
            'risks': risks,
            'summary': summary,
            'recommendations': analysis.get('recommendations', []),
            'suggested_lawyer_categories': analysis.get('suggestedLawyerCategories', ['other']),
            'ai_model': f'Llama 3.1 ({model})',
        }
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in Llama analysis: {e}")
        return None
    except Exception as e:
        print(f"Groq Analysis Error: {e}")
        return None


# ============================================================================
# CASE PREDICTION / AI JUDGE FUNCTIONALITY
# ============================================================================

JUDGE_SYSTEM_PROMPT = """You are an AI Judge Simulator powered by Llama 3.1, specializing in Indian legal precedents.

Your role is to analyze case facts and predict outcomes based on:
1. Indian legal precedents from Supreme Court and High Courts
2. Relevant statutes (IPC, CrPC, CPC, Contract Act, Constitution, etc.)
3. Legal principles and doctrines

You must provide:
1. A win probability percentage (0-100)
2. Supporting precedents that favor the case
3. Challenging precedents that oppose the case
4. Detailed legal analysis
5. Recommendations for strengthening the case

IMPORTANT: Always emphasize that this is an AI prediction and not legal advice.
Real court outcomes depend on many factors including judge discretion, evidence quality, and legal representation."""

PREDICTION_PROMPT_TEMPLATE = """Analyze this legal case and predict the outcome. Respond in VALID JSON format only.

Case Type: {case_type}
Case Facts: {case_facts}

Respond with this JSON structure:
{{
  "winProbability": 0-100,
  "confidence": "high|medium|low",
  "supportingPrecedents": [
    {{
      "caseName": "Case Name vs State/Party (Year)",
      "citation": "AIR/SCC citation",
      "relevance": "How this case supports the claim",
      "keyPrinciple": "Legal principle established"
    }}
  ],
  "opposingPrecedents": [
    {{
      "caseName": "Case Name vs State/Party (Year)",
      "citation": "AIR/SCC citation",
      "relevance": "How this case challenges the claim",
      "keyPrinciple": "Legal principle that may work against"
    }}
  ],
  "analysis": {{
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "keyFactors": ["factor 1", "factor 2"],
    "applicableLaws": ["IPC Section X", "Contract Act Section Y"],
    "detailedAnalysis": "Comprehensive legal analysis of the case"
  }},
  "recommendations": ["recommendation 1", "recommendation 2"],
  "disclaimer": "Standard disclaimer about AI prediction limitations"
}}"""


def predict_case_outcome(case_type: str, case_facts: str, model: str = None) -> dict:
    """
    Predict case outcome using Llama 3.1 as an AI Judge.
    
    Args:
        case_type: Type of legal case (criminal, civil, family, etc.)
        case_facts: Detailed facts of the case
        model: Specific model to use (defaults to quality model for best predictions)
    
    Returns:
        dict with prediction results
    """
    client = get_groq_client()
    
    if not client:
        return {
            'success': False,
            'error': 'GROQ_API_KEY is not configured. Please add it to enable AI Judge predictions.'
        }
    
    model = model or MODEL_FOR_PREDICTION
    
    try:
        prompt = PREDICTION_PROMPT_TEMPLATE.format(
            case_type=case_type,
            case_facts=case_facts[:30000]  # Limit facts size
        )
        
        messages = [
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.4,  # Slightly creative but mostly factual
            max_tokens=4096,
            top_p=0.95,
        )
        
        response_text = response.choices[0].message.content
        
        # Clean up JSON response
        cleaned_response = response_text.strip()
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
        
        prediction = json.loads(cleaned_response)
        
        return {
            'success': True,
            'win_probability': prediction.get('winProbability', 50),
            'confidence': prediction.get('confidence', 'medium'),
            'supporting_precedents': prediction.get('supportingPrecedents', []),
            'opposing_precedents': prediction.get('opposingPrecedents', []),
            'analysis': prediction.get('analysis', {}),
            'recommendations': prediction.get('recommendations', []),
            'disclaimer': prediction.get('disclaimer', 'This is an AI prediction and not legal advice.'),
            'model_used': model,
            'tokens_used': {
                'prompt': response.usage.prompt_tokens,
                'completion': response.usage.completion_tokens,
                'total': response.usage.total_tokens
            }
        }
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in case prediction: {e}")
        return {
            'success': False,
            'error': 'Failed to parse AI response. Please try again.'
        }
    except Exception as e:
        print(f"Groq Prediction Error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================================
# VOICE INPUT TRANSCRIPTION (using Groq's Whisper)
# ============================================================================

def transcribe_audio(audio_file_path: str, language: str = 'en') -> dict:
    """
    Transcribe audio using Groq's Whisper model.
    
    Args:
        audio_file_path: Path to audio file
        language: Language code (en, hi, etc.)
    
    Returns:
        dict with transcription results
    """
    client = get_groq_client()
    
    if not client:
        return {
            'success': False,
            'error': 'GROQ_API_KEY is not configured.'
        }
    
    try:
        with open(audio_file_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
                language=language if language != 'en' else None,  # Auto-detect for English
                response_format="text"
            )
        
        return {
            'success': True,
            'text': transcription,
            'language': language,
            'translated': transcription  # Whisper returns in original language
        }
    
    except Exception as e:
        print(f"Groq Transcription Error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_legal_interpretation(text: str, source_language: str = 'en') -> dict:
    """
    Get legal interpretation of user's voice input using Llama 3.1.
    
    Args:
        text: Transcribed text from voice input
        source_language: Original language of the input
    
    Returns:
        dict with legal interpretation
    """
    client = get_groq_client()
    
    if not client:
        return {
            'success': False,
            'error': 'GROQ_API_KEY is not configured.'
        }
    
    # Language mapping
    language_names = {
        'hi': 'Hindi', 'ta': 'Tamil', 'te': 'Telugu', 'bn': 'Bengali',
        'mr': 'Marathi', 'gu': 'Gujarati', 'pa': 'Punjabi', 'kn': 'Kannada',
        'ml': 'Malayalam', 'or': 'Odia', 'en': 'English'
    }
    
    try:
        prompt = f"""A user seeking legal help in India spoke the following in {language_names.get(source_language, 'their language')}:

"{text}"

Please analyze this and provide:

1. **Summary of Legal Issue**: What is the user's problem in simple terms?

2. **Applicable Indian Laws**: What laws/sections may be relevant? (e.g., IPC, CrPC, CPC, Contract Act, etc.)

3. **Type of Legal Matter**: Is this criminal, civil, family, property, consumer, labor, or other?

4. **Recommended Actions**: What should the user do next?

5. **Type of Lawyer Needed**: What kind of advocate would be best for this case?

6. **Urgency Level**: Is this urgent (requires immediate action) or can it wait?

Respond in a clear, structured format that a common person can understand.
If the issue is not legal in nature, politely clarify and suggest appropriate help."""

        messages = [
            {
                "role": "system", 
                "content": "You are an expert Indian legal assistant. Help users understand their legal issues in simple terms. Be empathetic and helpful."
            },
            {"role": "user", "content": prompt}
        ]
        
        response = client.chat.completions.create(
            model=MODEL_FOR_ANALYSIS,
            messages=messages,
            temperature=0.5,
            max_tokens=2048,
        )
        
        interpretation = response.choices[0].message.content
        
        return {
            'success': True,
            'interpretation': interpretation.strip(),
            'model_used': MODEL_FOR_ANALYSIS,
            'tokens_used': response.usage.total_tokens
        }
    
    except Exception as e:
        print(f"Groq Legal Interpretation Error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_available_models() -> dict:
    """Get list of available Llama models with their descriptions"""
    return {
        'llama-3.1-8b-instant': {
            'name': 'Llama 3.1 8B Instant',
            'description': 'Fastest model, ideal for real-time chat',
            'context_window': 131072,
            'speed': 'Ultra Fast (300+ tokens/sec)'
        },
        'llama-3.1-70b-versatile': {
            'name': 'Llama 3.1 70B Versatile',
            'description': 'Balanced model for most tasks',
            'context_window': 131072,
            'speed': 'Fast (100+ tokens/sec)'
        },
        'llama-3.3-70b-versatile': {
            'name': 'Llama 3.3 70B Versatile',
            'description': 'Latest and most capable model',
            'context_window': 131072,
            'speed': 'Fast (100+ tokens/sec)'
        }
    }


def test_groq_connection() -> dict:
    """Test if Groq API is properly configured and working"""
    client = get_groq_client()
    
    if not client:
        return {
            'connected': False,
            'error': 'GROQ_API_KEY not configured'
        }
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'Groq connection successful' in one line."}],
            max_tokens=50
        )
        
        return {
            'connected': True,
            'message': response.choices[0].message.content,
            'model': 'llama-3.1-8b-instant'
        }
    except Exception as e:
        return {
            'connected': False,
            'error': str(e)
        }
