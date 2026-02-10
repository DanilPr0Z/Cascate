from django.core.management.base import BaseCommand
from catalog.models import Category, SubCategory, Product, ProductImage
import requests
import csv
from io import StringIO, BytesIO
from decimal import Decimal
from django.core.files.base import ContentFile
from PIL import Image as PILImage
import hashlib


class Command(BaseCommand):
    help = 'Полная синхронизация данных товаров из Google Sheets (с изображениями и категориями)'

    SPREADSHEET_ID = "1qamWaC8SNlvSoIJkARFDMfJPAVLZ4rlWH4O742zUebE"

    # Маппинг листов на категории (будет автоматически определяться)
    SHEETS_MAPPING = {
        927078023: ('Двери и перегородки', 'Двери'),
        1825319837: ('Двери и перегородки', 'Перегородки'),
        1685271117: ('Системы хранения', 'Гардеробные'),
        1714574147: ('Системы хранения', 'Стеллажи'),
        1414361071: ('Системы хранения', 'Витрины'),
        843544969: ('Столы', 'Столы'),
        1958918488: ('Мягкая мебель', 'Диваны'),
        1901123786: ('Мягкая мебель', 'Кровати'),
        2108711969: ('Декор', 'Полки'),
        1439345963: ('Декор', 'Стеновые панели'),
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет обновлено, но не обновлять',
        )
        parser.add_argument(
            '--with-images',
            action='store_true',
            help='Синхронизировать изображения (если есть URL)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        with_images = options.get('with_images', True)  # По умолчанию с изображениями

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Режим DRY RUN - изменения не будут сохранены'))

        self.stdout.write('📊 Полная синхронизация данных из Google Sheets...')
        if with_images:
            self.stdout.write('  📷 С обновлением изображений\n')

        total_updated = 0
        total_created = 0
        total_errors = 0
        total_images = 0

        for gid, (category_name, subcategory_name) in self.SHEETS_MAPPING.items():
            self.stdout.write(f'\n📄 Обработка листа: {category_name} / {subcategory_name} (gid={gid})')

            try:
                # Получаем или создаем категорию
                if not dry_run:
                    category, cat_created = Category.objects.get_or_create(name=category_name)
                    if cat_created:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Создана категория: {category_name}'))

                    subcategory = None
                    if subcategory_name:
                        subcategory, sub_created = SubCategory.objects.get_or_create(
                            category=category,
                            name=subcategory_name
                        )
                        if sub_created:
                            self.stdout.write(self.style.SUCCESS(f'  ✓ Создана подкатегория: {subcategory_name}'))
                else:
                    category = Category.objects.filter(name=category_name).first()
                    subcategory = SubCategory.objects.filter(name=subcategory_name).first() if subcategory_name else None

                # Получаем данные из Google Sheets
                data = self.fetch_sheet_data(gid)

                if not data:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Нет данных в листе'))
                    continue

                # Обрабатываем товары
                created, updated, images, errors = self.process_products(
                    data, category, subcategory, dry_run, with_images, gid
                )

                total_created += created
                total_updated += updated
                total_images += images
                total_errors += errors

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Ошибка обработки листа: {str(e)}'))
                import traceback
                traceback.print_exc()
                total_errors += 1

        # Итоговая статистика
        self.stdout.write('\n' + '='*70)
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'📊 DRY RUN завершен:'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Полная синхронизация завершена:'))
        self.stdout.write(f'  Создано товаров: {total_created}')
        self.stdout.write(f'  Обновлено товаров: {total_updated}')
        if with_images:
            self.stdout.write(f'  Обновлено изображений: {total_images}')
        self.stdout.write(f'  Ошибок: {total_errors}')
        self.stdout.write('='*70)

    def fetch_sheet_data(self, gid):
        """Получает данные листа из Google Sheets в формате CSV"""
        url = f"https://docs.google.com/spreadsheets/d/{self.SPREADSHEET_ID}/gviz/tq?tqx=out:csv&gid={gid}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Парсим CSV
            csv_data = StringIO(response.text)
            reader = csv.reader(csv_data)
            rows = list(reader)

            return rows

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Ошибка получения данных: {str(e)}'))
            return None

    def process_products(self, data, category, subcategory, dry_run, with_images, gid):
        """Обрабатывает товары из данных листа"""
        created = 0
        updated = 0
        images_updated = 0
        errors = 0

        if len(data) < 2:
            return created, updated, images_updated, errors

        # Находим начало данных (пропускаем заголовки)
        data_start = 0
        for idx, row in enumerate(data):
            if row and len(row) > 2:
                first_cell = str(row[0]).strip().lower()
                if first_cell not in ['№ позиции в зале', 'двери', 'перегородки', 'гардеробные',
                                      'стеллажи', 'витрины', 'диваны', 'кровати', 'столы',
                                      'стеновые панели', 'полки подвесные', '']:
                    data_start = idx
                    break

        # Ищем колонку с URL изображений
        image_col_idx = None
        if with_images and data_start > 0:
            header_row = data[data_start - 1] if data_start > 0 else data[0]
            for idx, cell in enumerate(header_row):
                cell_lower = str(cell).lower().strip()
                if any(keyword in cell_lower for keyword in ['фото', 'url', 'image', 'картинка', 'изображение']):
                    image_col_idx = idx
                    self.stdout.write(f'  📷 Найдена колонка с изображениями: колонка {idx+1}')
                    break

        # Обрабатываем товары
        for row_idx, row in enumerate(data[data_start:], data_start):
            if not row or len(row) < 3:
                continue

            try:
                # Извлекаем данные
                product_number = str(row[0]).strip() if row[0] else ''
                name = str(row[2]).strip() if len(row) > 2 and row[2] else ''

                if not name or len(name) < 2:
                    continue

                # Пропускаем заголовочные строки
                if name.lower() in ['наименование товара', 'двери', 'перегородки']:
                    continue

                # Ищем товар
                if product_number:
                    product = Product.objects.filter(product_number=product_number).first()
                else:
                    product = Product.objects.filter(name=name, category=category).first()

                # Извлекаем дополнительные данные
                product_data = self.extract_product_data(row)
                product_data['name'] = name
                product_data['product_number'] = product_number
                product_data['category'] = category
                product_data['subcategory'] = subcategory

                # URL изображения (если есть)
                image_url = None
                if image_col_idx and len(row) > image_col_idx:
                    img_cell = str(row[image_col_idx]).strip()
                    if img_cell and (img_cell.startswith('http') or img_cell.startswith('https')):
                        image_url = img_cell

                if dry_run:
                    if product:
                        self.stdout.write(f'  🔄 Будет обновлен: {product_number} - {name[:40]}')
                        if image_url:
                            self.stdout.write(f'     📷 С изображением: {image_url[:50]}...')
                        updated += 1
                    else:
                        self.stdout.write(f'  ➕ Будет создан: {product_number} - {name[:40]}')
                        if image_url:
                            self.stdout.write(f'     📷 С изображением: {image_url[:50]}...')
                        created += 1
                else:
                    # Создаем или обновляем товар
                    if product:
                        # Обновляем существующий товар
                        for key, value in product_data.items():
                            if key not in ['category', 'subcategory'] and value:
                                setattr(product, key, value)
                        product.save()
                        self.stdout.write(f'  ✓ Обновлен: {product_number} - {name[:40]}')
                        updated += 1
                    else:
                        # Создаем новый товар
                        product = Product.objects.create(**product_data)
                        self.stdout.write(f'  ✓ Создан: {product_number} - {name[:40]}')
                        created += 1

                    # Обновляем изображение (если есть URL)
                    if with_images and image_url:
                        if self.update_product_image(product, image_url):
                            self.stdout.write(f'     📷 Изображение обновлено')
                            images_updated += 1
                        else:
                            self.stdout.write(self.style.WARNING(f'     ⚠ Не удалось загрузить изображение'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Ошибка обработки товара: {str(e)}'))
                errors += 1
                continue

        return created, updated, images_updated, errors

    def update_product_image(self, product, image_url):
        """Загружает и обновляет изображение товара по URL"""
        try:
            # Скачиваем изображение
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Проверяем что это действительно изображение
            image = PILImage.open(BytesIO(response.content))
            image.load()

            # Конвертируем в RGB если нужно
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')

            # Сохраняем в JPEG
            output = BytesIO()
            image.save(output, format='JPEG', quality=85)
            image_content = output.getvalue()

            # Создаем хеш для проверки изменений
            image_hash = hashlib.md5(image_content).hexdigest()

            # Проверяем существующее изображение
            existing_image = product.images.filter(is_main=True).first()
            if existing_image:
                # Проверяем изменилось ли изображение
                # (простая проверка - можно улучшить сравнением хешей)
                existing_image.delete()

            # Создаем новое изображение
            product_image = ProductImage(
                product=product,
                is_main=True,
                order=0,
                alt_text=product.name
            )
            product_image.image.save(
                f'{product.product_number or product.id}_main.jpg',
                ContentFile(image_content),
                save=True
            )

            return True

        except Exception as e:
            # Логируем ошибку но не останавливаем процесс
            return False

    def extract_product_data(self, row):
        """Извлекает данные товара из строки CSV"""
        data = {
            'availability': 'in_stock',
        }

        # Пытаемся извлечь цену
        for idx in range(len(row) - 1, -1, -1):
            cell = str(row[idx]).strip()
            if cell and cell.replace('.', '').replace(',', '').isdigit():
                try:
                    price = float(cell.replace(',', '.'))
                    if price > 0 and price < 10000000:
                        data['price'] = Decimal(str(price))
                        break
                except:
                    pass

        # Извлекаем размеры
        for cell in row:
            cell_str = str(cell).strip()
            if any(sep in cell_str for sep in ['x', '*', 'х', 'X']):
                if len(cell_str) < 200:
                    data['dimensions'] = cell_str[:200]
                    break

        # Материалы/модель
        if len(row) > 3 and row[3]:
            model = str(row[3]).strip()
            if model and len(model) < 100:
                data['materials'] = model[:500]

        return data
