"""
AI Service for document analysis and chat.
Primary: Groq with Llama 3.1 (ultra-fast, free)
Fallback: Google Gemini
"""
import os
import json
import re
from django.conf import settings

# Try importing Groq first (primary)
try:
    from .groq_service import (
        is_groq_available,
        chat_with_llama,
        analyze_document_with_llama,
        predict_case_outcome,
        get_available_models
    )
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Gemini as fallback
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def get_ai_provider():
    """Determine which AI provider to use"""
    if GROQ_AVAILABLE and is_groq_available():
        return 'groq'
    elif GENAI_AVAILABLE:
        api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
        if api_key:
            return 'gemini'
    return None


def get_gemini_model():
    """Initialize and return Gemini model"""
    if not GENAI_AVAILABLE:
        return None
    
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
    if not api_key:
        return None
    
    client = genai.Client(api_key=api_key)
    return client


ANALYSIS_PROMPT = """You are an expert Indian legal document analyzer. Analyze the following document text and provide a comprehensive analysis in JSON format.

IMPORTANT: You must respond ONLY with valid JSON, no markdown, no code blocks, just raw JSON.

Analyze for:
1. Document type classification
2. Risk assessment of each clause
3. Plain language summary in both English and Hindi
4. Key points extraction
5. Legal references (IPC, CPC, Contract Act, etc.)
6. Overall health score (0-100, where 100 is safest)

Response format:
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
  "suggestedLawyerCategories": ["property", "civil", etc]
}

Document text to analyze:
"""


CHAT_SYSTEM_INSTRUCTION = """You are a helpful and knowledgeable Indian Legal AI Assistant. 
Your goal is to assist users with legal queries, explain legal concepts in simple terms, and guide them on procedural matters in the Indian context.

Guidelines:
1. Always clarify that you are an AI assistant and not a substitute for a qualified lawyer.
2. Provide information based on Indian laws (IPC, CrPC, Contract Act, Constitution, etc.).
3. Be empathetic but professional.
4. If a query is about a specific case or requires specific legal action, strongly advise consulting a lawyer.
5. Keep answers concise and easy to understand.
"""


def analyze_document_with_ai(text, filename):
    """
    Analyze a document using AI.
    Primary: Groq with Llama 3.1 (ultra-fast, free)
    Fallback: Google Gemini
    """
    provider = get_ai_provider()
    
    # Try Groq first (faster and free)
    if provider == 'groq':
        try:
            print("📡 Using Groq/Llama 3.1 for document analysis...")
            result = analyze_document_with_llama(text, filename)
            if result and not result.get('error'):
                result['ai_provider'] = 'groq-llama-3.1'
                return result
        except Exception as e:
            print(f"Groq analysis failed, falling back to Gemini: {e}")
    
    # Fallback to Gemini
    client = get_gemini_model()
    
    if not client:
        return create_fallback_analysis(filename, text)
    
    try:
        print("📡 Using Gemini for document analysis...")
        result = client.models.generate_content(
            model='models/gemini-2.0-flash',
            contents=ANALYSIS_PROMPT + text
        )
        response_text = result.text
        
        # Clean up the response
        cleaned_response = response_text.replace('```json\n', '').replace('```\n', '').replace('```', '').strip()
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
            'ai_provider': 'gemini',
        }
    except Exception as e:
        print(f"Error analyzing document with Gemini: {e}")
        return create_fallback_analysis(filename, text)


def create_fallback_analysis(filename, text):
    """Create a basic analysis when AI is not available"""
    lower_text = text.lower()
    
    document_type = 'other'
    type_label = 'Legal Document'
    suggested_categories = ['other']
    
    if 'rent' in lower_text or 'lease' in lower_text or 'tenant' in lower_text:
        document_type = 'rental-agreement'
        type_label = 'Rental/Lease Agreement'
        suggested_categories = ['property']
    elif 'employment' in lower_text or 'salary' in lower_text or 'employee' in lower_text:
        document_type = 'employment-contract'
        type_label = 'Employment Contract'
        suggested_categories = ['labor']
    elif 'sale deed' in lower_text or 'conveyance' in lower_text:
        document_type = 'sale-deed'
        type_label = 'Sale Deed'
        suggested_categories = ['property']
    elif 'power of attorney' in lower_text or 'poa' in lower_text:
        document_type = 'power-of-attorney'
        type_label = 'Power of Attorney'
        suggested_categories = ['civil']
    elif 'partnership' in lower_text:
        document_type = 'partnership-deed'
        type_label = 'Partnership Deed'
        suggested_categories = ['corporate']
    elif 'loan' in lower_text or 'borrow' in lower_text:
        document_type = 'loan-agreement'
        type_label = 'Loan Agreement'
        suggested_categories = ['civil']
    
    return {
        'file_name': filename,
        'file_type': filename.split('.')[-1] if '.' in filename else 'unknown',
        'document_type': document_type,
        'health_score': 50,
        'risk_level': 'medium',
        'risks': [],
        'summary': {
            'type': document_type,
            'type_label': type_label,
            'key_points': ['Document needs manual review'],
            'plain_summary_en': 'AI analysis is currently unavailable. Please review the document manually or try again later.',
            'plain_summary_hi': 'AI विश्लेषण वर्तमान में उपलब्ध नहीं है। कृपया दस्तावेज़ की मैन्युअल रूप से समीक्षा करें।',
            'parties': [],
            'effective_date': None,
            'expiry_date': None,
            'monetary_value': None,
        },
        'recommendations': ['Configure GEMINI_API_KEY for AI-powered analysis', 'Consult a legal professional for document review'],
        'suggested_lawyer_categories': suggested_categories,
    }


def chat_with_legal_ai(history, message, lang_code='en'):
    """
    Chat with the legal AI assistant.
    Primary: Groq with Llama 3.1 (ultra-fast, free)
    Fallback: Google Gemini
    
    Args:
        history: Conversation history
        message: User message
        lang_code: Language code (en, hi, ta, te, bn, mr, etc.)
    """
    provider = get_ai_provider()
    
    # Try Groq first (faster and free)
    if provider == 'groq':
        try:
            print(f"💬 Using Groq/Llama 3.1 for chat (lang={lang_code})...")
            result = chat_with_llama(message, history, lang_code=lang_code)
            if result and result.get('success'):
                result['ai_provider'] = 'groq-llama-3.1'
                return result
        except Exception as e:
            print(f"Groq chat failed, falling back to Gemini: {e}")
    
    # Fallback to Gemini
    client = get_gemini_model()
    
    if not client:
        return {
            'success': False,
            'error': 'No AI provider available. Please configure GROQ_API_KEY or GEMINI_API_KEY.'
        }
    
    try:
        print("💬 Using Gemini for chat...")
        # Format history for Gemini
        formatted_history = []
        for msg in history:
            role = 'user' if msg.get('role') == 'user' else 'model'
            formatted_history.append({
                'role': role,
                'parts': [{'text': msg.get('content', msg.get('parts', ''))}]
            })
        
        # Add system instruction to the first message if needed
        if not formatted_history:
            full_message = f"{CHAT_SYSTEM_INSTRUCTION}\n\nUser question: {message}"
        else:
            full_message = message
        
        # Create chat with history
        formatted_history.append({
            'role': 'user',
            'parts': [{'text': full_message}]
        })
        
        result = client.models.generate_content(
            model='models/gemini-2.0-flash',
            contents=formatted_history
        )
        response_text = result.text
        
        if not response_text or not response_text.strip():
            return {
                'success': False,
                'error': 'Received empty response from AI'
            }
        
        return {
            'success': True,
            'text': response_text.strip(),
            'ai_provider': 'gemini'
        }
    except Exception as e:
        print(f"Gemini Chat Error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def extract_text_from_file(file):
    """Extract text from uploaded file"""
    filename = file.name.lower()
    content = file.read()
    
    try:
        if filename.endswith('.txt'):
            return content.decode('utf-8', errors='ignore')
        
        elif filename.endswith('.pdf'):
            try:
                import PyPDF2
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text() or ''
                return text
            except ImportError:
                return "PDF support requires PyPDF2. Please install it."
        
        elif filename.endswith('.docx'):
            try:
                import mammoth
                import io
                result = mammoth.extract_raw_text(io.BytesIO(content))
                return result.value
            except ImportError:
                return "DOCX support requires mammoth. Please install it."
        
        else:
            # Try to decode as text
            return content.decode('utf-8', errors='ignore')
    
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""
