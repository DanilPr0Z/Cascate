from django.core.management.base import BaseCommand
from catalog.models import Product
import qrcode
from io import BytesIO
from django.core.files import File


class Command(BaseCommand):
    help = 'Генерирует QR коды для всех товаров'

    def handle(self, *args, **options):
        self.stdout.write('Генерация QR кодов для товаров...')

        products = Product.objects.all()
        generated_count = 0
        skipped_count = 0

        for product in products:
            # Пропускаем если QR код уже есть
            if product.qr_code:
                self.stdout.write(self.style.WARNING(f'○ QR код уже существует: {product.name}'))
                skipped_count += 1
                continue

            # Создаем QR код
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            # Генерируем полный URL товара
            product_url = f"https://cascateporte.ru{product.get_absolute_url()}"
            qr.add_data(product_url)
            qr.make(fit=True)

            # Создаем изображение QR кода
            img = qr.make_image(fill_color="black", back_color="white")

            # Сохраняем в BytesIO
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            # Сохраняем файл в модель
            filename = f'qr_{product.slug}.png'
            product.qr_code.save(filename, File(buffer), save=True)

            self.stdout.write(self.style.SUCCESS(f'✓ Создан QR код: {product.name}'))
            generated_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n✓ Создано {generated_count} QR кодов'))
        self.stdout.write(self.style.WARNING(f'○ Пропущено {skipped_count} (уже существуют)'))
        self.stdout.write(self.style.SUCCESS('\nГотово!'))
