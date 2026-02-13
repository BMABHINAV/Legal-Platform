from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Legal Platform Core'

    def ready(self):
        """Initialize dynamic translations when app is ready."""
        try:
            from .translation_middleware import activate_dynamic_translations
            activate_dynamic_translations()
        except Exception as e:
            print(f"Warning: Could not activate dynamic translations: {e}")
