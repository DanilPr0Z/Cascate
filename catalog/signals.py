import qrcode
from io import BytesIO
from django.core.files import File
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product


@receiver(post_save, sender=Product)
def generate_product_qr_code(sender, instance, created, **kwargs):
    """
    Генерирует QR код для товара при его создании.
    QR код содержит URL товара.
    """
    if created and not instance.qr_code:
        # Создаем QR код с URL товара
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Генерируем полный URL товара (можно изменить на нужный домен)
        product_url = f"https://cascateporte.ru{instance.get_absolute_url()}"
        qr.add_data(product_url)
        qr.make(fit=True)

        # Создаем изображение QR кода
        img = qr.make_image(fill_color="black", back_color="white")

        # Сохраняем в BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Сохраняем файл в модель
        filename = f'qr_{instance.slug}.png'
        instance.qr_code.save(filename, File(buffer), save=False)

        # Обновляем только поле qr_code, чтобы избежать рекурсии
        Product.objects.filter(pk=instance.pk).update(qr_code=instance.qr_code)
