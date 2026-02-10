from django.core.management.base import BaseCommand
from catalog.models import Category, SubCategory, Product
import requests
import csv
from io import StringIO
from decimal import Decimal


class Command(BaseCommand):
    help = 'Синхронизация данных товаров из Google Sheets (без изображений)'

    SPREADSHEET_ID = "1qamWaC8SNlvSoIJkARFDMfJPAVLZ4rlWH4O742zUebE"

    # Маппинг листов на категории
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

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 Режим DRY RUN - изменения не будут сохранены'))

        self.stdout.write('📊 Синхронизация данных из Google Sheets...\n')

        total_updated = 0
        total_created = 0
        total_errors = 0

        for gid, (category_name, subcategory_name) in self.SHEETS_MAPPING.items():
            self.stdout.write(f'\n📄 Обработка листа: {category_name} / {subcategory_name} (gid={gid})')

            try:
                # Получаем или создаем категорию
                category, _ = Category.objects.get_or_create(name=category_name)
                subcategory = None
                if subcategory_name:
                    subcategory, _ = SubCategory.objects.get_or_create(
                        category=category,
                        name=subcategory_name
                    )

                # Получаем данные из Google Sheets
                data = self.fetch_sheet_data(gid)

                if not data:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Нет данных в листе'))
                    continue

                # Обрабатываем товары
                created, updated, errors = self.process_products(
                    data, category, subcategory, dry_run
                )

                total_created += created
                total_updated += updated
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
            self.stdout.write(self.style.SUCCESS(f'✓ Синхронизация завершена:'))
        self.stdout.write(f'  Создано: {total_created}')
        self.stdout.write(f'  Обновлено: {total_updated}')
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

    def process_products(self, data, category, subcategory, dry_run):
        """Обрабатывает товары из данных листа"""
        created = 0
        updated = 0
        errors = 0

        if len(data) < 2:
            return created, updated, errors

        # Пропускаем заголовки и находим начало данных
        data_start = 0
        for idx, row in enumerate(data):
            if row and len(row) > 2:
                first_cell = str(row[0]).strip().lower()
                # Пропускаем заголовочные строки
                if first_cell in ['№ позиции в зале', 'двери', 'перегородки', 'гардеробные',
                                  'стеллажи', 'витрины', 'диваны', 'кровати', 'столы',
                                  'стеновые панели', 'полки подвесные', '']:
                    continue
                else:
                    data_start = idx
                    break

        # Обрабатываем товары
        for row in data[data_start:]:
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

                # Ищем товар по номеру или названию
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

                if dry_run:
                    if product:
                        self.stdout.write(f'  🔄 Будет обновлен: {product_number} - {name[:40]}')
                        updated += 1
                    else:
                        self.stdout.write(f'  ➕ Будет создан: {product_number} - {name[:40]}')
                        created += 1
                else:
                    # Создаем или обновляем товар
                    if product:
                        # Обновляем существующий товар (НЕ трогаем изображения!)
                        for key, value in product_data.items():
                            if key not in ['category', 'subcategory'] and value:
                                setattr(product, key, value)
                        product.save()
                        self.stdout.write(f'  ✓ Обновлен: {product_number} - {name[:40]}')
                        updated += 1
                    else:
                        # Создаем новый товар (без изображений)
                        product = Product.objects.create(**product_data)
                        self.stdout.write(f'  ✓ Создан: {product_number} - {name[:40]}')
                        created += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Ошибка обработки товара: {str(e)}'))
                errors += 1
                continue

        return created, updated, errors

    def extract_product_data(self, row):
        """Извлекает данные товара из строки CSV"""
        data = {
            'availability': 'in_stock',
        }

        # Пытаемся извлечь цену (обычно в конце)
        for idx in range(len(row) - 1, -1, -1):
            cell = str(row[idx]).strip()
            if cell and cell.replace('.', '').replace(',', '').isdigit():
                try:
                    price = float(cell.replace(',', '.'))
                    if price > 0 and price < 10000000:  # Разумная цена
                        data['price'] = Decimal(str(price))
                        break
                except:
                    pass

        # Пытаемся извлечь размеры
        for cell in row:
            cell_str = str(cell).strip()
            # Ищем паттерны размеров: 1234x5678, 1234*5678, 1234х5678
            if any(sep in cell_str for sep in ['x', '*', 'х', 'X']):
                if len(cell_str) < 200:  # Разумная длина для размеров
                    data['dimensions'] = cell_str[:200]
                    break

        # Модель/название конструкции (обычно в 4-й колонке)
        if len(row) > 3 and row[3]:
            model = str(row[3]).strip()
            if model and len(model) < 100:
                data['materials'] = model[:500]

        return data
