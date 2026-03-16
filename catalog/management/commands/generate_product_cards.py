from django.core.management.base import BaseCommand
from catalog.models import Product
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
import os
import qrcode


class Command(BaseCommand):
    help = 'Генерирует карточки товаров с QR-кодами'

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
                self.stdout.write(f'Генерация карточки для товара ID {product_id}...')
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Товар с ID {product_id} не найден'))
                return
        else:
            products = Product.objects.all()
            self.stdout.write(f'Генерация карточек для {products.count()} товаров...')

        generated_count = 0

        # Создаем директорию для карточек
        cards_dir = os.path.join(settings.MEDIA_ROOT, 'product_cards')
        os.makedirs(cards_dir, exist_ok=True)

        for product in products:
            try:
                card_path = self.generate_product_card(product, cards_dir)
                self.stdout.write(self.style.SUCCESS(f'✓ Создана карточка: {product.name}'))
                self.stdout.write(self.style.SUCCESS(f'  Файл: {card_path}'))
                generated_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Ошибка для товара {product.name}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\n✓ Создано {generated_count} карточек'))
        self.stdout.write(self.style.SUCCESS(f'Карточки сохранены в: {cards_dir}'))

    def generate_product_card(self, product, output_dir):
        """Генерирует карточку товара с QR-кодом и информацией"""

        # Размеры карточки - компактная визитка (90x50 мм при 300 DPI)
        width = 1000
        height = 700

        # Создаем белый фон
        card = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(card)

        # Загружаем шрифты
        try:
            font_paths = [
                os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans.ttf'),
                os.path.join(settings.BASE_DIR, 'static', 'fonts', 'DejaVuSans-Bold.ttf'),
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            ]

            font_regular = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font_regular = ImageFont.truetype(font_path, 24)
                        font_bold = ImageFont.truetype(font_path, 32)
                        font_medium = ImageFont.truetype(font_path, 22)
                        font_small = ImageFont.truetype(font_path, 20)
                        font_price = ImageFont.truetype(font_path, 40)
                        break
                    except:
                        continue

            if not font_regular:
                font_regular = ImageFont.load_default()
                font_bold = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
                font_price = ImageFont.load_default()

        except Exception as e:
            print(f"[WARNING] Could not load font: {e}")
            font_regular = ImageFont.load_default()
            font_bold = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
            font_price = ImageFont.load_default()

        # Добавляем логотип в верхний левый угол
        logo_height_final = 0
        try:
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo-navbar.png')
            if os.path.exists(logo_path):
                logo = Image.open(logo_path)
                logo_width = 200
                logo_height = int(logo.height * (logo_width / logo.width))
                logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
                card.paste(logo, (30, 30), logo if logo.mode == 'RGBA' else None)
                logo_height_final = logo_height
        except Exception as e:
            print(f"[WARNING] Could not add logo: {e}")

        # Название товара (под логотипом, слева)
        y_offset = max(100, logo_height_final + 60)
        name_lines = self.wrap_text(product.name, font_bold, width - 60)
        for line in name_lines[:2]:  # Максимум 2 строки
            draw.text((30, y_offset), line, fill='black', font=font_bold)
            y_offset += 40

        y_offset += 30

        # Генерируем QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=1,
        )

        # URL товара
        product_url = f"https://cascateporte.ru{product.get_absolute_url()}"
        qr.add_data(product_url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_size = 350
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

        # QR-код слева
        qr_x = 30
        qr_y = y_offset
        card.paste(qr_img, (qr_x, qr_y))

        # Информация справа от QR
        info_x = qr_x + qr_size + 40
        info_y = y_offset
        line_height = 35

        # Материалы
        if product.materials:
            draw.text((info_x, info_y), "Материалы:", fill='#666666', font=font_medium)
            info_y += line_height
            materials_lines = self.wrap_text(product.materials, font_small, width - info_x - 30)
            for line in materials_lines[:2]:  # Максимум 2 строки
                draw.text((info_x, info_y), line, fill='black', font=font_small)
                info_y += 30
            info_y += 10

        # Размеры
        if product.dimensions:
            draw.text((info_x, info_y), "Размеры:", fill='#666666', font=font_medium)
            info_y += line_height
            draw.text((info_x, info_y), product.dimensions, fill='black', font=font_small)
            info_y += line_height + 10

        # Страна
        if product.country:
            draw.text((info_x, info_y), "Страна:", fill='#666666', font=font_medium)
            info_y += line_height
            draw.text((info_x, info_y), product.country, fill='black', font=font_small)
            info_y += line_height + 20

        # Цена справа (жирным, зеленым)
        price_text = f"{int(product.price)} ₽"
        draw.text((info_x, info_y), price_text, fill='#2c5f2d', font=font_price)
        info_y += 50

        # Цена от (если указана)
        if product.price_from:
            price_from_text = f"Цена от {int(product.price_from)} ₽"
            draw.text((info_x, info_y), price_from_text, fill='#666666', font=font_small)

        # Сохраняем карточку
        filename = f'card_{product.slug}.png'
        filepath = os.path.join(output_dir, filename)
        card.save(filepath, 'PNG', quality=95)

        return filepath

    def wrap_text(self, text, font, max_width):
        """Разбивает текст на строки по ширине"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            # Создаем временный объект для измерения
            temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
            bbox = temp_draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else [text]
