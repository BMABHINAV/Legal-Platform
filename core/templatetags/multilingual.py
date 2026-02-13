"""
Custom template tags for dynamic multilingual support.
No GNU gettext required!
"""

from django import template
from django.utils.safestring import mark_safe
import json

from ..dynamic_translation import translate_text, get_translations_for_template, STATIC_TRANSLATIONS

register = template.Library()


@register.simple_tag(takes_context=True)
def trans(context, text):
    """
    Translate text to the current language.
    Usage: {% trans "Hello" %}
    """
    request = context.get('request')
    if request:
        lang_code = getattr(request, 'LANGUAGE_CODE', 'en')
    else:
        lang_code = context.get('LANGUAGE_CODE', 'en')
    
    return translate_text(str(text), lang_code)


@register.simple_tag(takes_context=True)
def dtrans(context, text):
    """
    Dynamic translate - same as trans but for use in attributes.
    Usage: placeholder="{% dtrans 'Search...' %}"
    """
    return trans(context, text)


@register.simple_tag(takes_context=True)
def translations_json(context):
    """
    Output all translations as JSON for JavaScript.
    Usage: <script>const TRANSLATIONS = {% translations_json %};</script>
    """
    request = context.get('request')
    if request:
        lang_code = getattr(request, 'LANGUAGE_CODE', 'en')
    else:
        lang_code = context.get('LANGUAGE_CODE', 'en')
    
    translations = get_translations_for_template(lang_code)
    return mark_safe(json.dumps(translations, ensure_ascii=False))


@register.filter
def translate(text, lang_code):
    """
    Translate filter for use in templates.
    Usage: {{ "Hello"|translate:LANGUAGE_CODE }}
    """
    return translate_text(str(text), lang_code)


@register.inclusion_tag('core/partials/language_switcher.html', takes_context=True)
def language_switcher(context):
    """Render the language switcher dropdown."""
    from django.conf import settings
    
    request = context.get('request')
    current_lang = 'en'
    if request:
        current_lang = getattr(request, 'LANGUAGE_CODE', 'en')
    
    languages = getattr(settings, 'LANGUAGES', [('en', 'English')])
    
    return {
        'current_language': current_lang,
        'languages': languages,
        'request': request,
    }


@register.simple_tag
def get_language_name(lang_code):
    """Get the native name of a language."""
    lang_names = {
        'en': 'English',
        'hi': 'हिन्दी',
        'ta': 'தமிழ்',
        'te': 'తెలుగు',
        'bn': 'বাংলা',
        'mr': 'मराठी',
        'gu': 'ગુજરાતી',
        'kn': 'ಕನ್ನಡ',
        'ml': 'മലയാളം',
        'pa': 'ਪੰਜਾਬੀ',
    }
    return lang_names.get(lang_code, lang_code)


@register.simple_tag
def get_language_flag(lang_code):
    """Get emoji flag for language (using regional flags where appropriate)."""
    flags = {
        'en': '🇬🇧',
        'hi': '🇮🇳',
        'ta': '🇮🇳',
        'te': '🇮🇳',
        'bn': '🇮🇳',
        'mr': '🇮🇳',
        'gu': '🇮🇳',
        'kn': '🇮🇳',
        'ml': '🇮🇳',
        'pa': '🇮🇳',
    }
    return flags.get(lang_code, '🌐')
