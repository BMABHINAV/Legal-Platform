"""
Language Service for Multilingual Support.
Handles AI responses in regional languages and voice input.
"""

from django.utils.translation import get_language
from django.conf import settings

# Language configurations
LANGUAGE_CONFIG = {
    'en': {
        'name': 'English',
        'native_name': 'English',
        'direction': 'ltr',
        'voice_code': 'en-IN',  # Indian English
        'ai_instruction': 'Respond in English.',
        'greeting': 'Hello! How can I help you today?',
    },
    'hi': {
        'name': 'Hindi',
        'native_name': 'हिन्दी',
        'direction': 'ltr',
        'voice_code': 'hi-IN',
        'ai_instruction': 'Respond in Hindi (हिन्दी). Use Devanagari script.',
        'greeting': 'नमस्ते! आज मैं आपकी कैसे मदद कर सकता हूं?',
    },
    'ta': {
        'name': 'Tamil',
        'native_name': 'தமிழ்',
        'direction': 'ltr',
        'voice_code': 'ta-IN',
        'ai_instruction': 'Respond in Tamil (தமிழ்). Use Tamil script.',
        'greeting': 'வணக்கம்! இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?',
    },
    'te': {
        'name': 'Telugu',
        'native_name': 'తెలుగు',
        'direction': 'ltr',
        'voice_code': 'te-IN',
        'ai_instruction': 'Respond in Telugu (తెలుగు). Use Telugu script.',
        'greeting': 'నమస్కారం! ఈ రోజు నేను మీకు ఎలా సహాయం చేయగలను?',
    },
    'bn': {
        'name': 'Bengali',
        'native_name': 'বাংলা',
        'direction': 'ltr',
        'voice_code': 'bn-IN',
        'ai_instruction': 'Respond in Bengali (বাংলা). Use Bengali script.',
        'greeting': 'নমস্কার! আজ আমি আপনাকে কিভাবে সাহায্য করতে পারি?',
    },
    'mr': {
        'name': 'Marathi',
        'native_name': 'मराठी',
        'direction': 'ltr',
        'voice_code': 'mr-IN',
        'ai_instruction': 'Respond in Marathi (मराठी). Use Devanagari script.',
        'greeting': 'नमस्कार! आज मी तुमची कशी मदत करू शकतो?',
    },
    'gu': {
        'name': 'Gujarati',
        'native_name': 'ગુજરાતી',
        'direction': 'ltr',
        'voice_code': 'gu-IN',
        'ai_instruction': 'Respond in Gujarati (ગુજરાતી). Use Gujarati script.',
        'greeting': 'નમસ્તે! આજે હું તમને કેવી રીતે મદદ કરી શકું?',
    },
    'kn': {
        'name': 'Kannada',
        'native_name': 'ಕನ್ನಡ',
        'direction': 'ltr',
        'voice_code': 'kn-IN',
        'ai_instruction': 'Respond in Kannada (ಕನ್ನಡ). Use Kannada script.',
        'greeting': 'ನಮಸ್ಕಾರ! ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?',
    },
    'ml': {
        'name': 'Malayalam',
        'native_name': 'മലയാളം',
        'direction': 'ltr',
        'voice_code': 'ml-IN',
        'ai_instruction': 'Respond in Malayalam (മലയാളം). Use Malayalam script.',
        'greeting': 'നമസ്കാരം! ഇന്ന് എനിക്ക് നിങ്ങളെ എങ്ങനെ സഹായിക്കാനാകും?',
    },
    'pa': {
        'name': 'Punjabi',
        'native_name': 'ਪੰਜਾਬੀ',
        'direction': 'ltr',
        'voice_code': 'pa-IN',
        'ai_instruction': 'Respond in Punjabi (ਪੰਜਾਬੀ). Use Gurmukhi script.',
        'greeting': 'ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?',
    },
}

# Common legal terms in all languages
LEGAL_TERMS = {
    'en': {
        'lawyer': 'Lawyer',
        'advocate': 'Advocate',
        'court': 'Court',
        'case': 'Case',
        'bail': 'Bail',
        'fir': 'FIR',
        'contract': 'Contract',
        'property': 'Property',
        'divorce': 'Divorce',
        'maintenance': 'Maintenance',
        'custody': 'Custody',
        'rights': 'Rights',
    },
    'hi': {
        'lawyer': 'वकील',
        'advocate': 'अधिवक्ता',
        'court': 'न्यायालय',
        'case': 'मामला',
        'bail': 'जमानत',
        'fir': 'एफआईआर',
        'contract': 'अनुबंध',
        'property': 'संपत्ति',
        'divorce': 'तलाक',
        'maintenance': 'भरण-पोषण',
        'custody': 'हिरासत',
        'rights': 'अधिकार',
    },
    'ta': {
        'lawyer': 'வழக்கறிஞர்',
        'advocate': 'வழக்குரைஞர்',
        'court': 'நீதிமன்றம்',
        'case': 'வழக்கு',
        'bail': 'ஜாமீன்',
        'fir': 'எஃப்ஐஆர்',
        'contract': 'ஒப்பந்தம்',
        'property': 'சொத்து',
        'divorce': 'விவாகரத்து',
        'maintenance': 'ஜீவனாம்சம்',
        'custody': 'காவல்',
        'rights': 'உரிமைகள்',
    },
    'te': {
        'lawyer': 'న్యాయవాది',
        'advocate': 'అడ్వకేట్',
        'court': 'న్యాయస్థానం',
        'case': 'కేసు',
        'bail': 'బెయిల్',
        'fir': 'ఎఫ్ఐఆర్',
        'contract': 'ఒప్పందం',
        'property': 'ఆస్తి',
        'divorce': 'విడాకులు',
        'maintenance': 'భరణం',
        'custody': 'కస్టడీ',
        'rights': 'హక్కులు',
    },
    'bn': {
        'lawyer': 'উকিল',
        'advocate': 'অ্যাডভোকেট',
        'court': 'আদালত',
        'case': 'মামলা',
        'bail': 'জামিন',
        'fir': 'এফআইআর',
        'contract': 'চুক্তি',
        'property': 'সম্পত্তি',
        'divorce': 'বিবাহ বিচ্ছেদ',
        'maintenance': 'ভরণপোষণ',
        'custody': 'হেফাজত',
        'rights': 'অধিকার',
    },
    'mr': {
        'lawyer': 'वकील',
        'advocate': 'अॅडव्होकेट',
        'court': 'न्यायालय',
        'case': 'खटला',
        'bail': 'जामीन',
        'fir': 'एफआयआर',
        'contract': 'करार',
        'property': 'मालमत्ता',
        'divorce': 'घटस्फोट',
        'maintenance': 'पोटगी',
        'custody': 'ताबा',
        'rights': 'हक्क',
    },
}


def get_language_config(lang_code=None):
    """Get language configuration for the current or specified language."""
    if lang_code is None:
        lang_code = get_language() or 'en'
    
    # Handle language codes like 'en-us' -> 'en'
    if '-' in lang_code:
        lang_code = lang_code.split('-')[0]
    
    return LANGUAGE_CONFIG.get(lang_code, LANGUAGE_CONFIG['en'])


def get_ai_language_instruction(lang_code=None):
    """Get AI instruction for responding in the user's language."""
    config = get_language_config(lang_code)
    return config['ai_instruction']


def get_voice_language_code(lang_code=None):
    """Get the voice recognition language code for Web Speech API."""
    config = get_language_config(lang_code)
    return config['voice_code']


def get_greeting(lang_code=None):
    """Get localized greeting message."""
    config = get_language_config(lang_code)
    return config['greeting']


def get_legal_term(term, lang_code=None):
    """Get a legal term in the specified language."""
    if lang_code is None:
        lang_code = get_language() or 'en'
    
    if '-' in lang_code:
        lang_code = lang_code.split('-')[0]
    
    lang_terms = LEGAL_TERMS.get(lang_code, LEGAL_TERMS['en'])
    return lang_terms.get(term, term)


def get_all_languages():
    """Get list of all supported languages for UI."""
    return [
        {'code': code, **config}
        for code, config in LANGUAGE_CONFIG.items()
    ]


def build_multilingual_prompt(user_message, lang_code=None):
    """Build a prompt that instructs AI to respond in the user's language."""
    lang_instruction = get_ai_language_instruction(lang_code)
    
    return f"""
{lang_instruction}
Keep your response helpful, clear, and easy to understand.
If discussing legal concepts, use common terms that regular citizens would understand.

User's question: {user_message}
"""


# UI Translation Strings (for JavaScript)
UI_STRINGS = {
    'en': {
        'loading': 'Loading...',
        'send': 'Send',
        'speak': 'Speak',
        'listening': 'Listening...',
        'stop': 'Stop',
        'error': 'An error occurred',
        'book_now': 'Book Now',
        'call_now': 'Call Now',
        'chat': 'Chat',
        'search': 'Search',
        'filter': 'Filter',
        'all': 'All',
        'verified': 'Verified',
        'available': 'Available',
    },
    'hi': {
        'loading': 'लोड हो रहा है...',
        'send': 'भेजें',
        'speak': 'बोलें',
        'listening': 'सुन रहा है...',
        'stop': 'रोकें',
        'error': 'एक त्रुटि हुई',
        'book_now': 'अभी बुक करें',
        'call_now': 'अभी कॉल करें',
        'chat': 'चैट',
        'search': 'खोजें',
        'filter': 'फ़िल्टर',
        'all': 'सभी',
        'verified': 'सत्यापित',
        'available': 'उपलब्ध',
    },
    'ta': {
        'loading': 'ஏற்றுகிறது...',
        'send': 'அனுப்பு',
        'speak': 'பேசு',
        'listening': 'கேட்கிறது...',
        'stop': 'நிறுத்து',
        'error': 'பிழை ஏற்பட்டது',
        'book_now': 'இப்போது புக் செய்',
        'call_now': 'இப்போது அழைக்கவும்',
        'chat': 'அரட்டை',
        'search': 'தேடு',
        'filter': 'வடிகட்டி',
        'all': 'அனைத்தும்',
        'verified': 'சரிபார்க்கப்பட்டது',
        'available': 'கிடைக்கும்',
    },
    'te': {
        'loading': 'లోడ్ అవుతోంది...',
        'send': 'పంపండి',
        'speak': 'మాట్లాడండి',
        'listening': 'వింటోంది...',
        'stop': 'ఆపు',
        'error': 'లోపం సంభవించింది',
        'book_now': 'ఇప్పుడు బుక్ చేయండి',
        'call_now': 'ఇప్పుడు కాల్ చేయండి',
        'chat': 'చాట్',
        'search': 'వెతకండి',
        'filter': 'ఫిల్టర్',
        'all': 'అన్నీ',
        'verified': 'ధృవీకరించబడింది',
        'available': 'అందుబాటులో ఉంది',
    },
    'bn': {
        'loading': 'লোড হচ্ছে...',
        'send': 'পাঠান',
        'speak': 'বলুন',
        'listening': 'শুনছি...',
        'stop': 'থামান',
        'error': 'একটি ত্রুটি ঘটেছে',
        'book_now': 'এখনই বুক করুন',
        'call_now': 'এখনই কল করুন',
        'chat': 'চ্যাট',
        'search': 'অনুসন্ধান',
        'filter': 'ফিল্টার',
        'all': 'সব',
        'verified': 'যাচাইকৃত',
        'available': 'উপলব্ধ',
    },
    'mr': {
        'loading': 'लोड होत आहे...',
        'send': 'पाठवा',
        'speak': 'बोला',
        'listening': 'ऐकत आहे...',
        'stop': 'थांबा',
        'error': 'एक त्रुटी आली',
        'book_now': 'आता बुक करा',
        'call_now': 'आता कॉल करा',
        'chat': 'चॅट',
        'search': 'शोधा',
        'filter': 'फिल्टर',
        'all': 'सर्व',
        'verified': 'सत्यापित',
        'available': 'उपलब्ध',
    },
}


def get_ui_strings(lang_code=None):
    """Get UI strings for the specified language."""
    if lang_code is None:
        lang_code = get_language() or 'en'
    
    if '-' in lang_code:
        lang_code = lang_code.split('-')[0]
    
    return UI_STRINGS.get(lang_code, UI_STRINGS['en'])
