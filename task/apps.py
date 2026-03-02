from django.apps import AppConfig


class TaskConfig(AppConfig):
    name = 'task'
    def ready(self):
        from .utils import init_database
        init_database()