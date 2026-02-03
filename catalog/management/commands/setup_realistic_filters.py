"""
Management команда для создания реалистичных фильтров на основе данных
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db.models import Q
from catalog.models import FilterCategory, FilterValue, Product


class Command(BaseCommand):
    help = 'Создание реалистичных фильтров и привязка их к товарам'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Настройка фильтров...'))

        # Обновляем существующие фильтры
        fc_style, _ = FilterCategory.objects.get_or_create(
            slug='po-stilyu',
            defaults={'name': 'По стилю', 'order': 1}
        )
        fc_style.name = 'По стилю'
        fc_style.save()

        fc_design, _ = FilterCategory.objects.get_or_create(
            slug='po-dizajnu',
            defaults={'name': 'По дизайну', 'order': 2}
        )
        fc_design.name = 'По дизайну'
        fc_design.save()

        fc_material, _ = FilterCategory.objects.get_or_create(
            slug='po-materialu',
            defaults={'name': 'По материалу', 'order': 3}
        )
        fc_material.name = 'По материалу'
        fc_material.save()

        fc_color, _ = FilterCategory.objects.get_or_create(
            slug='po-tsvetu',
            defaults={'name': 'По цвету', 'order': 4}
        )
        fc_color.name = 'По цвету'
        fc_color.save()

        # Автоматическое определение фильтров из описаний товаров
        self.stdout.write('Анализ товаров...')

        # Цвета из данных
        colors_mapping = {
            'Черный': ['Black', 'black'],
            'Бронза': ['Bronze', 'bronze'],
            'Шампань': ['Champagne', 'champagne'],
            'Хром': ['Chrome', 'Chrom', 'chrome'],
            'Темно-коричневый': ['Dark brown', 'Dark Brown', 'Marrone'],
            'Графит': ['Grafit', 'grafit'],
            'Палладий': ['Palladium', 'palladium'],
            'Титан': ['Titanium', 'titanium'],
            'Золото': ['Gold', 'gold'],
            'Песочный': ['sand', 'Sand'],
        }

        for color_name, keywords in colors_mapping.items():
            fv, created = FilterValue.objects.get_or_create(
                filter_category=fc_color,
                slug=slugify(color_name),
                defaults={'name': color_name}
            )
            if created:
                self.stdout.write(f'  ✓ Цвет: {color_name}')

            # Привязываем к товарам
            for keyword in keywords:
                products = Product.objects.filter(materials__icontains=keyword)
                for product in products:
                    product.filter_values.add(fv)

        # Материалы
        materials_mapping = {
            'Стекло': ['стекло', 'glass', 'Stopsol', 'Grey', 'Satin'],
            'Натуральный шпон': ['шпон', 'PK', 'PT', 'Walnut', 'Oak', 'Rovere'],
            'Композит': ['Composit', 'композит', 'Marble'],
            'Ткань': ['Ткань', 'ткань', 'Abitar', 'Generation', 'Step'],
            'Кожа': ['кожа', 'Leather'],
            'Металл': ['металл', 'Matt', 'metal'],
            'Эмаль': ['эмаль', 'Enamel'],
        }

        for material_name, keywords in materials_mapping.items():
            fv, created = FilterValue.objects.get_or_create(
                filter_category=fc_material,
                slug=slugify(material_name),
                defaults={'name': material_name}
            )
            if created:
                self.stdout.write(f'  ✓ Материал: {material_name}')

            # Привязываем к товарам
            for keyword in keywords:
                products = Product.objects.filter(
                    Q(materials__icontains=keyword) | Q(description__icontains=keyword)
                )
                for product in products[:10]:  # Ограничиваем чтобы не было слишком много связей
                    product.filter_values.add(fv)

        # Стили (на основе категорий)
        styles_data = {
            'Современный': ['Двери и перегородки', 'Системы хранения'],
            'Классический': ['Мягкая мебель'],
            'Минимализм': ['Столы', 'Декор'],
        }

        for style_name, categories in styles_data.items():
            fv, created = FilterValue.objects.get_or_create(
                filter_category=fc_style,
                slug=slugify(style_name),
                defaults={'name': style_name}
            )
            if created:
                self.stdout.write(f'  ✓ Стиль: {style_name}')

            # Привязываем к товарам из соответствующих категорий
            products = Product.objects.filter(category__name__in=categories)
            for product in products[:20]:
                product.filter_values.add(fv)

        # Дизайн (на основе подкатегорий)
        designs_data = {
            'Модульный': ['Диваны'],
            'Раздвижной': ['Двери', 'Перегородки'],
            'Распашной': ['Двери'],
        }

        for design_name, subcategories in designs_data.items():
            fv, created = FilterValue.objects.get_or_create(
                filter_category=fc_design,
                slug=slugify(design_name),
                defaults={'name': design_name}
            )
            if created:
                self.stdout.write(f'  ✓ Дизайн: {design_name}')

            # Привязываем к товарам
            products = Product.objects.filter(
                Q(subcategory__name__in=subcategories) | Q(name__icontains=design_name)
            )
            for product in products:
                product.filter_values.add(fv)

        self.stdout.write(self.style.SUCCESS('\n✅ Фильтры настроены и привязаны к товарам!'))

        # Статистика
        total_products = Product.objects.count()
        products_with_filters = Product.objects.filter(filter_values__isnull=False).distinct().count()
        self.stdout.write(f'Товаров с фильтрами: {products_with_filters}/{total_products}')
