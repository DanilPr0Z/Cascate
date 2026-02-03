#!/usr/bin/env python
"""
Скрипт для исправления подкатегорий товаров
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mebel.settings')
django.setup()

from catalog.models import Product, SubCategory

# Маппинг: ключевые слова в названии -> правильная подкатегория
SUBCATEGORY_MAPPING = {
    # Бытовая техника
    'холодильник': 'kholodilniki',
    'плита': 'plity',
    'посудомойка': 'posudomoiki',
    'вытяжка': 'vytiazhki',

    # Мягкая мебель
    'диван': 'divany',
    'кресло': 'kresla',
    'пуф': 'pufy-i-banketki',
    'банкетка': 'pufy-i-banketki',
    'шезлонг': 'shezlongi',
    'кушетка': 'kushetki',

    # Столовые
    'стол': 'stoly',
    'стул': 'stulia',
    'табурет': 'taburety',
    'сервант': 'servanty',
    'буфет': 'bufety',

    # Светильники
    'люстра': 'liustry',
    'бра': 'bra',
    'лампа': 'nastolnye-lampy',
    'торшер': 'torshery',
    'подвесной': 'podvesnye',

    # Кухни
    'кухонный гарнитур': 'kukhonnye-garnitury',
    'кухонный остров': 'kukhonnye-ostrova',
    'кухонный стол': 'kukhonnye-stoly',
}

def fix_subcategories():
    """Исправляет подкатегории товаров на основе их названий"""
    fixed_count = 0
    errors = []

    for product in Product.objects.all():
        name_lower = product.name.lower()

        # Ищем подходящую подкатегорию
        correct_subcategory = None
        for keyword, subcategory_slug in SUBCATEGORY_MAPPING.items():
            if keyword in name_lower:
                try:
                    correct_subcategory = SubCategory.objects.get(slug=subcategory_slug)
                    break
                except SubCategory.DoesNotExist:
                    errors.append(f'Подкатегория {subcategory_slug} не найдена для товара {product.name}')
                    continue

        if correct_subcategory:
            # Проверяем, нужно ли обновление
            if product.subcategory != correct_subcategory:
                old_subcat = product.subcategory.name if product.subcategory else 'НЕТ'
                product.subcategory = correct_subcategory
                # Обновляем категорию на основе подкатегории
                product.category = correct_subcategory.category
                product.save()
                print(f'✓ {product.name}')
                print(f'  {old_subcat} → {correct_subcategory.name}')
                fixed_count += 1

    print(f'\n=== РЕЗУЛЬТАТ ===')
    print(f'Исправлено товаров: {fixed_count}')
    if errors:
        print(f'\nОшибки:')
        for error in errors:
            print(f'  - {error}')

if __name__ == '__main__':
    print('Начинаем исправление подкатегорий...\n')
    fix_subcategories()
    print('\nГотово!')
