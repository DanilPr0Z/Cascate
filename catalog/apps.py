from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'
    
    def ready(self):
        # Configure admin site
        from django.contrib import admin
        admin.site.site_header = "Cascate Porte - Администрирование"
        admin.site.site_title = "Cascate Porte"
        admin.site.index_title = "Панель управления каталогом"

        # Import signals
        import catalog.signals

