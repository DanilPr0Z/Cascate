#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mebel.settings')
django.setup()

from catalog.models import FilterCategory, FilterValue, Product

print('Категории фильтров:')
for fc in FilterCategory.objects.all():
    print(f'  {fc.name}: {fc.values.count()} значений')

print(f'\nВсего товаров: {Product.objects.count()}')
print(f'Товаров с фильтрами: {Product.objects.filter(filter_values__isnull=False).distinct().count()}')
