"""
Management команда для создания фильтров из данных Excel
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from catalog.models import FilterCategory, FilterValue


class Command(BaseCommand):
    help = 'Создание фильтров на основе данных из Excel'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Создание категорий и значений фильтров...'))

        # Категория: Цвет
        color_category, created = FilterCategory.objects.get_or_create(
            slug='color',
            defaults={'name': 'Цвет', 'order': 1}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Создана категория: Цвет'))

        colors = [
            'Black Matt', 'Bronze Matt', 'Champagne', 'Chrome Bright',
            'Dark Brown', 'Grafit', 'Marrone', 'Nomad', 'Palladium',
            'Titanium Matt', 'Black Sand', 'Gold', 'Chrome Matt'
        ]

        for color in colors:
            FilterValue.objects.get_or_create(
                filter_category=color_category,
                slug=slugify(color),
                defaults={'name': color}
            )
        self.stdout.write(f'  ✓ Создано цветов: {len(colors)}')

        # Категория: Материал
        material_category, created = FilterCategory.objects.get_or_create(
            slug='material',
            defaults={'name': 'Материал', 'order': 2}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Создана категория: Материал'))

        materials = [
            'Стекло', 'Натуральный шпон', 'Композит', 'Кожа', 'Ткань',
            'Металл', 'Дерево', 'Эмаль', 'Мрамор'
        ]

        for material in materials:
            FilterValue.objects.get_or_create(
                filter_category=material_category,
                slug=slugify(material),
                defaults={'name': material}
            )
        self.stdout.write(f'  ✓ Создано материалов: {len(materials)}')

        # Категория: Тип изделия
        type_category, created = FilterCategory.objects.get_or_create(
            slug='type',
            defaults={'name': 'Тип изделия', 'order': 3}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Создана категория: Тип изделия'))

        types = [
            'Распашная', 'Раздвижная', 'Рото', 'Гармошка',
            'Модульный', 'Угловой', 'Прямой', 'С оттоманкой'
        ]

        for item_type in types:
            FilterValue.objects.get_or_create(
                filter_category=type_category,
                slug=slugify(item_type),
                defaults={'name': item_type}
            )
        self.stdout.write(f'  ✓ Создано типов: {len(types)}')

        # Категория: Стиль
        style_category, created = FilterCategory.objects.get_or_create(
            slug='style',
            defaults={'name': 'Стиль', 'order': 4}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Создана категория: Стиль'))

        styles = [
            'Современный', 'Классический', 'Минимализм', 'Лофт',
            'Модерн', 'Арт-деко', 'Скандинавский'
        ]

        for style in styles:
            FilterValue.objects.get_or_create(
                filter_category=style_category,
                slug=slugify(style),
                defaults={'name': style}
            )
        self.stdout.write(f'  ✓ Создано стилей: {len(styles)}')

        # Категория: Страна производитель
        country_category, created = FilterCategory.objects.get_or_create(
            slug='country',
            defaults={'name': 'Страна', 'order': 5}
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Создана категория: Страна'))

        countries = ['Италия', 'Германия', 'Испания', 'Россия']

        for country in countries:
            FilterValue.objects.get_or_create(
                filter_category=country_category,
                slug=slugify(country),
                defaults={'name': country}
            )
        self.stdout.write(f'  ✓ Создано стран: {len(countries)}')

        self.stdout.write(self.style.SUCCESS('\n✅ Фильтры успешно созданы!'))
