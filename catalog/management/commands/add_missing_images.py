from django.core.management.base import BaseCommand
from catalog.models import Product, ProductImage
from django.core.files import File
import os


class Command(BaseCommand):
    help = 'Добавление изображений для товаров без фото'

    def add_arguments(self, parser):
        parser.add_argument(
            '--images-dir',
            type=str,
            help='Директория с изображениями',
            default='missing_product_images'
        )

    def handle(self, *args, **options):
        images_dir = options['images_dir']

        # Товары без изображений
        products_without_images = [
            ('Д-36', 'Дверь распашная Nuovo'),
            ('М21', 'ВИТРИНА ВЫСОКАЯ'),
            ('М18', 'ВИТРИНА напольная узкая'),
            ('ДИВ4', 'Модульный диван Romeo'),
            ('ДИВ9', 'Модульный диван Icon'),
            ('Д13', 'Дверь распашная Fly'),
        ]

        self.stdout.write('='*70)
        self.stdout.write('Добавление изображений для товаров без фото')
        self.stdout.write('='*70)

        if not os.path.exists(images_dir):
            self.stdout.write(self.style.WARNING(f'\n📁 Создайте директорию: {images_dir}'))
            self.stdout.write(f'   И положите туда файлы изображений с именами:')
            for num, name in products_without_images:
                clean_num = num.replace('-', '_')
                self.stdout.write(f'   - {clean_num}.jpg  ({num} - {name})')
            self.stdout.write('')
            return

        added_count = 0
        skipped_count = 0

        for product_num, expected_name in products_without_images:
            # Ищем товар
            product = Product.objects.filter(product_number=product_num).first()

            if not product:
                self.stdout.write(self.style.ERROR(f'✗ {product_num} - товар не найден'))
                skipped_count += 1
                continue

            # Проверяем есть ли уже изображение
            if product.images.exists():
                self.stdout.write(f'⚠ {product_num} - уже есть изображение, пропускаем')
                skipped_count += 1
                continue

            # Ищем файл изображения
            clean_num = product_num.replace('-', '_')
            image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
            image_path = None

            for ext in image_extensions:
                potential_path = os.path.join(images_dir, f'{clean_num}{ext}')
                if os.path.exists(potential_path):
                    image_path = potential_path
                    break

            if not image_path:
                self.stdout.write(self.style.WARNING(f'⚠ {product_num} - файл не найден'))
                self.stdout.write(f'   Ожидается: {os.path.join(images_dir, clean_num)}.jpg/.png')
                skipped_count += 1
                continue

            # Добавляем изображение
            try:
                with open(image_path, 'rb') as f:
                    product_image = ProductImage(
                        product=product,
                        is_main=True,
                        order=0,
                        alt_text=product.name
                    )
                    filename = os.path.basename(image_path)
                    product_image.image.save(filename, File(f), save=True)

                self.stdout.write(self.style.SUCCESS(f'✓ {product_num} - изображение добавлено'))
                added_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ {product_num} - ошибка: {str(e)}'))
                skipped_count += 1

        self.stdout.write('')
        self.stdout.write('='*70)
        self.stdout.write(f'Добавлено: {added_count}')
        self.stdout.write(f'Пропущено: {skipped_count}')
        self.stdout.write('='*70)
