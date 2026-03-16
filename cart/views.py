from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Cart, CartItem
from catalog.models import Product
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime


def get_or_create_cart(request):
    """Получить или создать корзину для текущего пользователя/сессии"""
    if request.user.is_authenticated:
        # Для авторизованных пользователей
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # Для анонимных пользователей используем сессию
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)

    return cart


def generate_order_pdf(cart, customer_info=None):
    """Генерация PDF с заказом"""
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Image
    import os

    buffer = BytesIO()

    # Создаем PDF документ
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    elements = []

    # Регистрируем шрифты с поддержкой кириллицы
    try:
        # Путь к шрифтам в проекте
        from django.conf import settings
        project_font_dir = os.path.join(settings.BASE_DIR, 'static', 'fonts')

        # Пробуем разные пути для шрифтов с поддержкой кириллицы
        font_paths = [
            (os.path.join(project_font_dir, 'DejaVuSans.ttf'), os.path.join(project_font_dir, 'DejaVuSans-Bold.ttf')),
            ('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'),
            ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf'),
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
            ('C:\\Windows\\Fonts\\arial.ttf', 'C:\\Windows\\Fonts\\arialbd.ttf'),
        ]

        font_registered = False
        for font_path, font_bold_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                    if os.path.exists(font_bold_path):
                        pdfmetrics.registerFont(TTFont('CustomFont-Bold', font_bold_path))
                    else:
                        pdfmetrics.registerFont(TTFont('CustomFont-Bold', font_path))
                    font_name = 'CustomFont'
                    font_name_bold = 'CustomFont-Bold'
                    font_registered = True
                    print(f"[INFO] Registered font: {font_path}")
                    break
                except Exception as e:
                    print(f"[WARNING] Failed to register font {font_path}: {e}")
                    continue

        if not font_registered:
            raise Exception("No suitable font found")

    except Exception as e:
        print(f"[ERROR] Could not register Unicode font: {e}")
        # В крайнем случае используем Helvetica, но кириллица не будет работать
        font_name = 'Helvetica'
        font_name_bold = 'Helvetica-Bold'

    # Создаем стили
    title_style = ParagraphStyle(
        'CustomTitle',
        fontName=font_name_bold,
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#444444'),
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        fontName=font_name_bold,
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#444444'),
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        fontName=font_name,
        fontSize=11,
        spaceAfter=6,
        alignment=TA_LEFT,
    )

    # Логотип в левом верхнем углу
    try:
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo-navbar.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=6*cm, height=1.4*cm)
            logo.hAlign = 'LEFT'
            elements.append(logo)
            elements.append(Spacer(1, 0.8*cm))
    except Exception as e:
        print(f"[WARNING] Could not add logo to PDF: {e}")

    # Заголовок
    title = Paragraph('Заказ', title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))

    # Дата заказа
    date_text = f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    elements.append(Paragraph(date_text, normal_style))
    elements.append(Spacer(1, 0.5*cm))

    # Информация о клиенте
    if customer_info:
        elements.append(Paragraph('Информация о клиенте:', heading_style))
        elements.append(Spacer(1, 0.3*cm))

        customer_text = f"Имя: {customer_info.get('first_name', '')}<br/>"
        customer_text += f"Фамилия: {customer_info.get('last_name', '')}<br/>"
        customer_text += f"Телефон: {customer_info.get('phone', '')}"
        if customer_info.get('email'):
            customer_text += f"<br/>Email: {customer_info.get('email', '')}"

        elements.append(Paragraph(customer_text, normal_style))
        elements.append(Spacer(1, 0.5*cm))

    # Таблица с товарами
    cart_items = cart.items.select_related('product').prefetch_related('product__images').all()

    # Данные таблицы
    data = [['№', 'Фото', 'Товар', 'Материалы', 'Цена', 'Кол-во', 'Итого']]

    for idx, item in enumerate(cart_items, 1):
        product_name = item.product.name[:40] if len(item.product.name) <= 40 else item.product.name[:37] + '...'

        # Материалы товара
        materials = item.product.materials if item.product.materials else '—'
        if len(materials) > 30:
            materials = materials[:27] + '...'

        # Получаем главное изображение товара
        product_image = None
        main_image = item.product.get_main_image()
        if main_image:
            try:
                image_path = os.path.join(settings.MEDIA_ROOT, str(main_image.image))
                if os.path.exists(image_path):
                    product_image = Image(image_path, width=1.5*cm, height=1.5*cm)
            except Exception as e:
                print(f"[WARNING] Could not load product image: {e}")

        # Если изображение не найдено, используем заглушку
        if not product_image:
            product_image = Paragraph('—', normal_style)

        data.append([
            str(idx),
            product_image,
            product_name,
            materials,
            f"{item.product.price:.0f} ₽",
            str(item.quantity),
            f"{item.get_total_price():.0f} ₽"
        ])

    # Итоговая строка
    total_items = cart.get_total_items()
    data.append(['', '', '', '', 'Итого:', f"{total_items} шт", f"{cart.get_total_price():.0f} ₽"])

    # Создаем таблицу
    table = Table(data, colWidths=[0.8*cm, 1.8*cm, 5*cm, 3*cm, 2*cm, 1.2*cm, 2.2*cm])

    # Стиль таблицы
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#444444')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Первая колонка (№) - по центру
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),  # Вторая колонка (Фото) - по центру
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),    # Третья колонка (Товар) - слева
        ('ALIGN', (3, 0), (3, -1), 'LEFT'),    # Четвертая колонка (Материалы) - слева
        ('ALIGN', (4, 0), (-1, -1), 'CENTER'), # Остальные - по центру
        ('FONTNAME', (0, 0), (-1, 0), font_name_bold),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F5F5F5')),
        ('FONTNAME', (0, -1), (-1, -1), font_name_bold),
        ('FONTNAME', (0, 1), (-1, -2), font_name),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 1*cm))

    # Контактная информация
    contact_text = "Контакты:<br/>"
    contact_text += "Тел: +7 800 234 01 73<br/>"
    contact_text += "Email: store@cascate.ru<br/>"
    contact_text += "г. Москва, проспект Маршала Жукова д.59"
    elements.append(Paragraph(contact_text, normal_style))

    # Функция для установки метаданных
    def set_metadata(canvas, doc):
        canvas.setTitle('Заказ Cascate Porte')
        canvas.setAuthor('Cascate Porte')
        canvas.setSubject('Заказ мебели')

    # Генерируем PDF с метаданными
    doc.build(elements, onFirstPage=set_metadata, onLaterPages=set_metadata)

    buffer.seek(0)
    return buffer


def cart_view(request):
    """Страница корзины"""
    print(f"[DEBUG] cart_view called: user={request.user}, authenticated={request.user.is_authenticated}")

    cart = get_or_create_cart(request)
    print(f"[DEBUG] Cart: id={cart.id}")

    cart_items = cart.items.select_related('product').prefetch_related('product__images').all()
    print(f"[DEBUG] Cart items count: {cart_items.count()}")
    for item in cart_items:
        print(f"[DEBUG] Item: {item.product.name} x{item.quantity}")

    # Добавляем главные изображения для каждого товара
    for item in cart_items:
        item.product.main_image = item.product.get_main_image()

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': cart.get_total_price(),
    }
    return render(request, 'cart/cart.html', context)


@require_POST
def add_to_cart(request, product_id):
    """AJAX: Добавить товар в корзину"""
    print(f"[DEBUG] add_to_cart called: product_id={product_id}, user={request.user}, authenticated={request.user.is_authenticated}")

    product = get_object_or_404(Product, id=product_id)
    print(f"[DEBUG] Product found: {product.name}")

    cart = get_or_create_cart(request)
    print(f"[DEBUG] Cart: id={cart.id}")

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    print(f"[DEBUG] CartItem: id={cart_item.id}, created={created}, quantity={cart_item.quantity}")

    if not created:
        cart_item.quantity += 1
        cart_item.save()
        print(f"[DEBUG] CartItem quantity updated to {cart_item.quantity}")

    total_items = cart.get_total_items()
    print(f"[DEBUG] Total items in cart: {total_items}")

    return JsonResponse({
        'success': True,
        'cart_count': total_items,
        'message': f'{product.name} добавлен в корзину'
    })


@require_POST
def remove_from_cart(request, item_id):
    """AJAX: Удалить товар из корзины"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()

    return JsonResponse({
        'success': True,
        'cart_count': cart.get_total_items(),
        'total_price': float(cart.get_total_price()),
    })


@require_POST
def update_quantity(request, item_id):
    """AJAX: Изменить количество товара"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    quantity = int(request.POST.get('quantity', 1))

    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        item_total = float(cart_item.get_total_price())
    else:
        cart_item.delete()
        item_total = 0

    return JsonResponse({
        'success': True,
        'item_total': item_total,
        'cart_count': cart.get_total_items(),
        'total_price': float(cart.get_total_price()),
    })


def download_order(request):
    """Скачать заказ в формате PDF"""
    from urllib.parse import quote

    cart = get_or_create_cart(request)

    # Генерируем PDF
    pdf_buffer = generate_order_pdf(cart)

    # Имя файла на русском
    filename = f'Заказ_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    filename_encoded = quote(filename)

    # Создаем HTTP ответ с PDF
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    # Используем оба формата для максимальной совместимости
    response['Content-Disposition'] = f'inline; filename="Zakaz_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"; filename*=UTF-8\'\'{filename_encoded}'

    return response


@require_POST
def submit_order(request):
    """Оформить заказ и отправить на email"""
    cart = get_or_create_cart(request)

    # Получаем данные клиента
    customer_info = {
        'first_name': request.POST.get('first_name', ''),
        'last_name': request.POST.get('last_name', ''),
        'phone': request.POST.get('phone', ''),
        'email': request.POST.get('email', ''),
    }

    # Генерируем PDF с информацией о клиенте
    pdf_buffer = generate_order_pdf(cart, customer_info)

    # Подготавливаем email
    subject = f'Новый заказ от {customer_info["first_name"]} {customer_info["last_name"]}'
    message = f"""
Получен новый заказ!

Информация о клиенте:
Имя: {customer_info['first_name']}
Фамилия: {customer_info['last_name']}
Телефон: {customer_info['phone']}
Email: {customer_info.get('email', 'Не указан')}

Детали заказа во вложении (PDF).

Общая сумма: {cart.get_total_price():.0f} ₽
Количество товаров: {cart.get_total_items()}

---
Cascate Porte
    """

    # Отправка email
    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['store@cascate.ru'],
            reply_to=[customer_info.get('email')] if customer_info.get('email') else None,
        )

        # Добавляем заголовки для надежности
        email.extra_headers = {
            'X-Mailer': 'Cascate Porte',
            'X-Priority': '3',
        }

        # Прикрепляем PDF
        email.attach(
            f'Заказ_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            pdf_buffer.getvalue(),
            'application/pdf'
        )

        email.send(fail_silently=False)

        # Очищаем корзину после успешной отправки
        cart.items.all().delete()

        return JsonResponse({
            'success': True,
            'message': 'Заказ успешно оформлен и отправлен!'
        })
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при отправке заказа: {str(e)}'
        })
