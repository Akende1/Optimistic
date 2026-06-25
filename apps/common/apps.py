from django.apps import AppConfig
from django.db.backends.signals import connection_created


def _configure_sqlite_connection(sender, connection, **kwargs):
    engine = connection.settings_dict.get('ENGINE', '')
    if 'sqlite3' not in engine:
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode=WAL;')
            cursor.execute('PRAGMA busy_timeout=20000;')
    except Exception:
        # Best-effort only; keep startup and request handling alive if PRAGMA setup fails.
        pass


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.common'
    verbose_name = 'Common Utilities'
    
    def ready(self):
        connection_created.connect(_configure_sqlite_connection, dispatch_uid='optimistic.sqlite_pragmas')
