from django.apps import AppConfig

class InnerCircleConfig(AppConfig):
    name = 'inner_circle'

    def ready(self):
        import inner_circle.signals
