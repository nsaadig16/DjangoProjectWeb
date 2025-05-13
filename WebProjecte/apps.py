from django.apps import AppConfig

class WebProjecteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'WebProjecte'

    def ready(self):
        import WebProjecte.signals
