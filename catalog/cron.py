from django_cron import CronJobBase, Schedule
from django.core.management import call_command


class SyncGoogleSheetsCronJob(CronJobBase):
    """
    Периодическая задача для синхронизации данных из Google Sheets
    Выполняется каждые 5 минут
    """
    RUN_EVERY_MINS = 5  # Каждые 5 минут

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'catalog.sync_google_sheets'  # Уникальный код задачи

    def do(self):
        """Выполнение синхронизации"""
        try:
            # Вызываем команду полной синхронизации (с изображениями и категориями)
            call_command('sync_google_sheets_full')
            return "✓ Полная синхронизация завершена успешно"
        except Exception as e:
            return f"✗ Ошибка синхронизации: {str(e)}"
