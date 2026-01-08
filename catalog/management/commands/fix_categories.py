from django.core.management.base import BaseCommand
from catalog.models import Product


class Command(BaseCommand):
    help = 'Исправляет товары, у которых подкатегория не соответствует категории'

    def handle(self, *args, **options):
        # Находим товары с несоответствием
        products_to_fix = []

        for product in Product.objects.select_related('category', 'subcategory').exclude(subcategory=None):
            if product.subcategory.category != product.category:
                products_to_fix.append(product)

        if not products_to_fix:
            self.stdout.write(self.style.SUCCESS('Все товары корректны. Нечего исправлять.'))
            return

        self.stdout.write(f'Найдено {len(products_to_fix)} товаров с несоответствием категорий:')

        for product in products_to_fix:
            old_category = product.category.name
            new_category = product.subcategory.category.name

            self.stdout.write(
                f'  - "{product.name}": {old_category} -> {new_category} '
                f'(подкатегория: {product.subcategory.name})'
            )

            # Исправляем категорию
            product.category = product.subcategory.category
            product.save(update_fields=['category'])

        self.stdout.write(self.style.SUCCESS(f'Исправлено {len(products_to_fix)} товаров.'))
