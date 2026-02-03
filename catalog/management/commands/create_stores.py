from django.core.management.base import BaseCommand
from catalog.models import Store, Product, ProductStock
import random


class Command(BaseCommand):
    help = 'Создает тестовые магазины и добавляет товары в наличие'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых магазинов...')

        # Создаем магазины
        stores_data = [
            {
                'name': 'Салон "Cascate Porte Олимпийский"',
                'address': 'г. Москва, Олимпийский проспект, д. 16, стр. 5',
                'phone': '+7 (495) 123-45-67',
                'email': 'olimp@cascateporte.ru',
                'working_hours': 'Пн-Вс: 10:00-21:00',
            },
            {
                'name': 'Салон "Cascate Porte Цветной"',
                'address': 'г. Москва, ул. Цветной бульвар, д. 30, стр. 1',
                'phone': '+7 (495) 234-56-78',
                'email': 'cvetnoy@cascateporte.ru',
                'working_hours': 'Пн-Вс: 10:00-22:00',
            },
            {
                'name': 'Салон "Cascate Porte Тверская"',
                'address': 'г. Москва, ул. Тверская, д. 15',
                'phone': '+7 (495) 345-67-89',
                'email': 'tverskaya@cascateporte.ru',
                'working_hours': 'Пн-Вс: 09:00-21:00',
            },
        ]

        created_stores = []
        for store_data in stores_data:
            store, created = Store.objects.get_or_create(
                name=store_data['name'],
                defaults=store_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Создан магазин: {store.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'○ Магазин уже существует: {store.name}'))
            created_stores.append(store)

        # Добавляем товары в магазины
        self.stdout.write('\nДобавление товаров в магазины...')
        products = Product.objects.all()

        if not products.exists():
            self.stdout.write(self.style.WARNING('Товары не найдены. Сначала создайте товары.'))
            return

        stock_count = 0
        for product in products:
            # Случайно выбираем 1-3 магазина для каждого товара
            num_stores = random.randint(1, min(3, len(created_stores)))
            selected_stores = random.sample(created_stores, num_stores)

            for store in selected_stores:
                quantity = random.randint(1, 15)
                stock, created = ProductStock.objects.get_or_create(
                    product=product,
                    store=store,
                    defaults={'quantity': quantity}
                )
                if created:
                    stock_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n✓ Создано {len(created_stores)} магазинов'))
        self.stdout.write(self.style.SUCCESS(f'✓ Добавлено {stock_count} записей о наличии товаров'))
        self.stdout.write(self.style.SUCCESS('\nГотово!'))
