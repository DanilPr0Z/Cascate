from django.core.management.base import BaseCommand
from django.utils.text import slugify
try:
    from unidecode import unidecode
except ImportError:
    def unidecode(text):
        return text

from catalog.models import SubCategory, FilterValue


def transliterate_slugify(text):
    """Транслитерирует русский текст и создает slug"""
    transliterated = unidecode(text)
    return slugify(transliterated)


class Command(BaseCommand):
    help = 'Исправляет slug для подкатегорий и значений фильтров'

    def handle(self, *args, **options):
        self.stdout.write('Исправление slug для подкатегорий...')
        
        # Исправляем slug для подкатегорий
        subcategories = SubCategory.objects.all()
        for subcat in subcategories:
            old_slug = subcat.slug
            new_slug = transliterate_slugify(subcat.name)
            if old_slug != new_slug:
                # Проверяем, нет ли конфликта
                existing = SubCategory.objects.filter(
                    category=subcat.category,
                    slug=new_slug
                ).exclude(id=subcat.id).first()
                
                if not existing:
                    subcat.slug = new_slug
                    subcat.save()
                    self.stdout.write(f'  ✓ {subcat.name}: {old_slug} -> {new_slug}')
                else:
                    self.stdout.write(f'  ⚠ Конфликт для {subcat.name}: {new_slug} уже существует')
        
        self.stdout.write('\nИсправление slug для значений фильтров...')
        
        # Исправляем slug для значений фильтров
        filter_values = FilterValue.objects.all()
        for fv in filter_values:
            old_slug = fv.slug
            new_slug = transliterate_slugify(fv.name)
            if old_slug != new_slug:
                # Проверяем, нет ли конфликта
                existing = FilterValue.objects.filter(
                    filter_category=fv.filter_category,
                    slug=new_slug
                ).exclude(id=fv.id).first()
                
                if not existing:
                    fv.slug = new_slug
                    fv.save()
                    self.stdout.write(f'  ✓ {fv.name}: {old_slug} -> {new_slug}')
                else:
                    self.stdout.write(f'  ⚠ Конфликт для {fv.name}: {new_slug} уже существует')
        
        self.stdout.write(self.style.SUCCESS('\n✅ Готово!'))

