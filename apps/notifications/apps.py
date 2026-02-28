from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'
    verbose_name = 'Notifications'
    
    def ready(self):
        """
        Import signals when app is ready.
        
        This ensures signals are registered and listening for events.
        """
        import apps.notifications.signals  # noqa
