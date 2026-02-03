#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mebel.settings')
django.setup()

from catalog.models import FilterCategory, FilterValue

# Удаляем пустые и дублирующиеся категории
empty_categories = FilterCategory.objects.filter(values__isnull=True).distinct()
print(f'Удаление пустых категорий: {empty_categories.count()}')
for fc in empty_categories:
    print(f'  - {fc.name}')
    fc.delete()

# Проверяем дубликаты по slug
all_cats = FilterCategory.objects.all()
seen_slugs = set()
for fc in all_cats:
    if fc.slug in seen_slugs:
        print(f'Найден дубликат: {fc.name} ({fc.slug})')
        if fc.values.count() == 0:
            fc.delete()
            print(f'  - Удален')
    else:
        seen_slugs.add(fc.slug)

print('\n=== Финальный список фильтров ===')
for fc in FilterCategory.objects.all().order_by('order'):
    print(f'{fc.name} ({fc.values.count()} значений)')
    for fv in fc.values.all():
        print(f'  - {fv.name}')
