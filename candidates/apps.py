from django.apps import AppConfig


class CandidatesConfig(AppConfig):
    name = 'candidates'

    def ready(self):
        # Import signals to register handlers
        from . import signals  # noqa: F401
