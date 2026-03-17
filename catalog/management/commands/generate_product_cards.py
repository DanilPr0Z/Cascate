from django.core.management.base import BaseCommand
from django.conf import settings
from catalog.models import Product
from catalog.label_generator import generate_product_card
import os


class Command(BaseCommand):
    help = 'Генерирует карточки-этикетки товаров с QR-кодами'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=int,
            help='ID конкретного товара для генерации карточки',
        )

    def handle(self, *args, **options):
        product_id = options.get('product_id')

        if product_id:
            try:
                products = [Product.objects.get(id=product_id)]
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Товар с ID {product_id} не найден'))
                return
        else:
            products = Product.objects.all()
            self.stdout.write(f'Генерация карточек для {products.count()} товаров...')

        cards_dir = os.path.join(settings.MEDIA_ROOT, 'product_cards')
        os.makedirs(cards_dir, exist_ok=True)

        generated = 0
        for product in products:
            try:
                path = generate_product_card(product, cards_dir)
                self.stdout.write(self.style.SUCCESS(f'✓ {product.name}  →  {path}'))
                generated += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ {product.name}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nГотово: создано {generated} карточек'))
        self.stdout.write(f'Каталог: {cards_dir}')
