"""
Dynamic Translation Middleware and Activation.
Patches Django's translation system to use AI-powered dynamic translations.
"""

from django.utils import translation
from django.utils.translation import trans_real
from .dynamic_translation import translate_text, STATIC_TRANSLATIONS


class DynamicTranslationMiddleware:
    """
    Middleware that ensures dynamic translation is available for each request.
    This adds the current language to the request and enables dynamic translations.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get language from various sources
        lang_code = self._get_language_from_request(request)
        
        # Activate the language
        translation.activate(lang_code)
        request.LANGUAGE_CODE = lang_code
        
        response = self.get_response(request)
        
        return response
    
    def _get_language_from_request(self, request):
        """Determine the language from request in priority order."""
        # 1. Check session
        if hasattr(request, 'session'):
            lang = request.session.get('_language')
            if lang:
                return self._normalize_lang(lang)
        
        # 2. Check cookie
        lang = request.COOKIES.get('django_language')
        if lang:
            return self._normalize_lang(lang)
        
        # 3. Check Accept-Language header
        accept_lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if accept_lang:
            # Parse first language
            first_lang = accept_lang.split(',')[0].split(';')[0].strip()
            if first_lang:
                return self._normalize_lang(first_lang)
        
        return 'en'
    
    def _normalize_lang(self, lang_code):
        """Normalize language code."""
        if not lang_code:
            return 'en'
        
        # Handle codes like 'hi-IN' -> 'hi'
        lang_code = lang_code.lower().split('-')[0]
        
        # Verify it's a supported language
        supported = ['en', 'hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa']
        if lang_code in supported:
            return lang_code
        
        return 'en'


# Monkey-patch Django's gettext to use our dynamic translations
_original_gettext = None


def dynamic_gettext(message):
    """
    Dynamic gettext replacement that uses AI translation when 
    static translations are not available.
    """
    global _original_gettext
    
    # Try original translation first
    if _original_gettext:
        translated = _original_gettext(message)
        if translated != message:
            return translated
    
    # Get current language
    lang_code = translation.get_language() or 'en'
    if lang_code == 'en':
        return message
    
    # Use our dynamic translation
    return translate_text(str(message), lang_code)


def activate_dynamic_translations():
    """
    Activate dynamic translations by patching Django's gettext.
    Call this in your AppConfig.ready() method.
    """
    global _original_gettext
    
    if _original_gettext is None:
        # Save original
        _original_gettext = trans_real.gettext
        
        # Patch with our dynamic version
        trans_real.gettext = dynamic_gettext
        
        # Also patch these for completeness
        trans_real.ugettext = dynamic_gettext


def get_ui_translations(lang_code):
    """
    Get all UI translations for JavaScript.
    Returns a dict that can be JSON-serialized.
    """
    if lang_code == 'en':
        return {}
    
    return STATIC_TRANSLATIONS.get(lang_code, {})
