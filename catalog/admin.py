from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.middleware.csrf import get_token
from .models import Category, SubCategory, Product, ProductImage, FilterCategory, FilterValue, Store, ProductStock, ProductRating
import os


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'name', 'order', 'get_products_count', 'created_at', 'view_on_site']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_display_links = ['name']
    list_per_page = 25
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'image', 'description', 'order')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "Нет изображения"
    image_preview.short_description = "Изображение"
    
    def view_on_site(self, obj):
        url = obj.get_absolute_url()
        return format_html('<a href="{}" target="_blank">👁️ Просмотр</a>', url)
    view_on_site.short_description = "Просмотр"


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'order', 'view_on_site']
    list_filter = ['category']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'category__name']
    list_per_page = 25
    
    def view_on_site(self, obj):
        url = obj.get_absolute_url()
        return format_html('<a href="{}" target="_blank">👁️ Просмотр</a>', url)
    view_on_site.short_description = "Просмотр"


@admin.register(FilterCategory)
class FilterCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'values_count']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_per_page = 25
    
    def values_count(self, obj):
        count = obj.values.count()
        return format_html('<span style="background: #20B2AA; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{} значений</span>', count)
    values_count.short_description = "Количество значений"


@admin.register(FilterValue)
class FilterValueAdmin(admin.ModelAdmin):
    list_display = ['name', 'filter_category', 'products_count']
    list_filter = ['filter_category']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']
    list_per_page = 25
    
    def products_count(self, obj):
        count = Product.objects.filter(filter_values=obj).count()
        return count
    products_count.short_description = "Товаров"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'image_preview', 'is_main', 'order', 'alt_text']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "Нет изображения"
    image_preview.short_description = "Превью"


class ProductStockInline(admin.TabularInline):
    model = ProductStock
    extra = 1
    fields = ['store', 'quantity']
    autocomplete_fields = ['store']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'name', 'category', 'price_formatted', 'availability_badge', 'is_new_display', 'created_at', 'view_on_site']
    list_filter = ['category', 'subcategory', 'availability', 'is_new', 'is_popular', 'filter_values', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'product_number', 'description', 'slug']
    filter_horizontal = ['filter_values']
    inlines = [ProductImageInline, ProductStockInline]
    list_per_page = 25
    list_display_links = ['name']
    date_hierarchy = 'created_at'

    def changelist_view(self, request, extra_context=None):
        """Добавляем кнопки импорта в контекст"""
        extra_context = extra_context or {}
        extra_context['download_template_url'] = reverse('admin:catalog_product_download_template')
        extra_context['import_excel_url'] = reverse('admin:catalog_product_import_excel')
        return super().changelist_view(request, extra_context=extra_context)

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'category', 'subcategory', 'price', 'price_from'),
            'classes': ('wide',)
        }),
        ('Характеристики товара', {
            'fields': ('country', 'materials', 'dimensions', 'product_number'),
        }),
        ('Описание', {
            'fields': ('short_description', 'description'),
            'classes': ('wide',)
        }),
        ('Фильтры и статусы', {
            'fields': ('filter_values', 'availability', 'is_new', 'is_popular'),
        }),
        ('QR код и карточка товара', {
            'fields': ('qr_code', 'qr_code_preview', 'product_card_preview', 'generate_card_button'),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': ('created_at', 'updated_at', 'views_count'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'views_count', 'image_preview', 'qr_code_preview', 'product_card_preview', 'generate_card_button']

    def get_urls(self):
        """Добавляем URL для генерации карточки и импорта"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:product_id>/generate-card/',
                self.admin_site.admin_view(self.generate_card_view),
                name='catalog_product_generate_card',
            ),
            path(
                'download-template/',
                self.admin_site.admin_view(self.download_template_view),
                name='catalog_product_download_template',
            ),
            path(
                'import-excel/',
                self.admin_site.admin_view(self.import_excel_view),
                name='catalog_product_import_excel',
            ),
        ]
        return custom_urls + urls

    def download_template_view(self, request):
        """Скачать шаблон Excel для импорта товаров"""
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            return HttpResponse(
                'Библиотека openpyxl не установлена. Установите: pip install openpyxl',
                status=500
            )

        # Создаем книгу Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Товары"

        # Заголовки столбцов
        headers = ['Название', 'Материалы', 'Размеры', 'Магазин', 'Цена', 'Категория', 'Подкатегория']

        # Стиль заголовков
        header_fill = PatternFill(start_color="20B2AA", end_color="20B2AA", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        header_alignment = Alignment(horizontal="center", vertical="center")

        # Записываем заголовки
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment

        # Добавляем пример строки
        ws.cell(row=2, column=1, value='ОБЕДЕННЫЙ СТОЛ')
        ws.cell(row=2, column=2, value='Дерево, металл')
        ws.cell(row=2, column=3, value='120x80x75 см')
        ws.cell(row=2, column=4, value='Москва')
        ws.cell(row=2, column=5, value=15000)
        ws.cell(row=2, column=6, value='Столовые')
        ws.cell(row=2, column=7, value='Столы обеденные')

        # Инструкция на втором листе
        ws2 = wb.create_sheet("Инструкция")
        ws2.cell(row=1, column=1, value="ИНСТРУКЦИЯ ПО ЗАПОЛНЕНИЮ")
        ws2.cell(row=1, column=1).font = Font(bold=True, size=14)

        instructions = [
            "",
            "1. Название - обязательное поле, название товара",
            "2. Материалы - из чего сделан товар (опционально)",
            "3. Размеры - габариты товара (опционально)",
            "4. Магазин - название магазина где товар в наличии",
            "5. Цена - цена товара в рублях (обязательно)",
            "6. Категория - название категории (должна существовать в системе)",
            "7. Подкатегория - название подкатегории (опционально)",
            "",
            "Доступные категории и подкатегории:",
        ]

        # Добавляем список категорий с подкатегориями
        categories = Category.objects.prefetch_related('subcategories').all()
        for cat in categories:
            instructions.append(f"  {cat.name}:")
            subcats = cat.subcategories.all()
            if subcats:
                for subcat in subcats:
                    instructions.append(f"    - {subcat.name}")
            else:
                instructions.append(f"    (нет подкатегорий)")
            instructions.append("")

        instructions.extend([
            "Доступные магазины:",
        ])

        # Добавляем список магазинов
        stores = Store.objects.filter(is_active=True)
        for store in stores:
            instructions.append(f"  - {store.name}")

        for row_num, instruction in enumerate(instructions, 3):
            ws2.cell(row=row_num, column=1, value=instruction)

        # Автоширина столбцов
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            ws.column_dimensions[column_letter].width = adjusted_width

        ws2.column_dimensions['A'].width = 50

        # Создаем HTTP ответ
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=shablon_tovarov.xlsx'

        # Сохраняем в response
        wb.save(response)

        return response

    def import_excel_view(self, request):
        """Импорт товаров из Excel"""
        if request.method == 'POST':
            try:
                from openpyxl import load_workbook
            except ImportError:
                return HttpResponse(
                    'Библиотека openpyxl не установлена. Установите: pip install openpyxl',
                    status=500
                )

            excel_file = request.FILES.get('excel_file')

            if not excel_file:
                return HttpResponse('Файл не загружен', status=400)

            try:
                wb = load_workbook(excel_file)
                ws = wb.active

                created_count = 0
                errors = []

                # Пропускаем заголовок, читаем со 2-й строки
                for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
                    if not row[0]:  # Пропускаем пустые строки
                        continue

                    try:
                        name = row[0]
                        materials = row[1] if row[1] else ''
                        dimensions = row[2] if row[2] else ''
                        store_name = row[3] if row[3] else None
                        price = row[4]
                        category_name = row[5]
                        subcategory_name = row[6] if len(row) > 6 and row[6] else None

                        # Находим категорию
                        try:
                            category = Category.objects.get(name=category_name)
                        except Category.DoesNotExist:
                            errors.append(f"Строка {row_num}: Категория '{category_name}' не найдена")
                            continue

                        # Находим подкатегорию если указана
                        subcategory = None
                        if subcategory_name:
                            try:
                                subcategory = SubCategory.objects.get(name=subcategory_name, category=category)
                            except SubCategory.DoesNotExist:
                                errors.append(f"Строка {row_num}: Подкатегория '{subcategory_name}' не найдена в категории '{category_name}'")
                                # Продолжаем без подкатегории

                        # Создаем товар
                        product = Product.objects.create(
                            name=name,
                            category=category,
                            subcategory=subcategory,
                            price=price,
                            materials=materials,
                            dimensions=dimensions,
                        )

                        # Добавляем в магазин если указан
                        if store_name:
                            try:
                                store = Store.objects.get(name=store_name)
                                ProductStock.objects.create(
                                    product=product,
                                    store=store,
                                    quantity=1
                                )
                            except Store.DoesNotExist:
                                errors.append(f"Строка {row_num}: Магазин '{store_name}' не найден (товар создан без магазина)")

                        created_count += 1

                    except Exception as e:
                        errors.append(f"Строка {row_num}: {str(e)}")

                # Формируем ответ
                result = f"Успешно создано товаров: {created_count}"
                if errors:
                    result += "\n\nОшибки:\n" + "\n".join(errors)

                return HttpResponse(f"<pre>{result}</pre><br><a href='/admin/catalog/product/'>Вернуться к товарам</a>")

            except Exception as e:
                return HttpResponse(f'Ошибка при обработке файла: {str(e)}', status=500)

        # GET запрос - показываем форму
        csrf_token = get_token(request)
        template_url = reverse('admin:catalog_product_download_template')

        html = f"""
            <html>
            <head>
                <title>Импорт товаров</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                    h1 {{ color: #20B2AA; }}
                    .upload-form {{ background: #f5f5f5; padding: 30px; border-radius: 8px; }}
                    input[type="file"] {{ margin: 20px 0; }}
                    button {{ background: #20B2AA; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
                    button:hover {{ background: #1a9a92; }}
                    .back-link {{ display: inline-block; margin-top: 20px; color: #20B2AA; text-decoration: none; }}
                </style>
            </head>
            <body>
                <h1>📥 Импорт товаров из Excel</h1>
                <div class="upload-form">
                    <p><strong>Инструкция:</strong></p>
                    <ol>
                        <li>Скачайте шаблон Excel</li>
                        <li>Заполните данные о товарах</li>
                        <li>Загрузите заполненный файл</li>
                    </ol>
                    <form method="post" enctype="multipart/form-data">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                        <input type="file" name="excel_file" accept=".xlsx" required>
                        <br>
                        <button type="submit">Загрузить и импортировать</button>
                    </form>
                    <a href="{template_url}" class="back-link">📄 Скачать шаблон Excel</a>
                    <br>
                    <a href="/admin/catalog/product/" class="back-link">← Вернуться к товарам</a>
                </div>
            </body>
            </html>
        """
        return HttpResponse(html)

    def generate_card_view(self, request, product_id):
        """View для генерации карточки товара через AJAX"""
        import traceback
        try:
            product = Product.objects.get(pk=product_id)

            # Импортируем функцию генерации из команды
            try:
                from PIL import Image, ImageDraw, ImageFont
            except ImportError as e:
                return JsonResponse({'success': False, 'error': f'Pillow не установлен: {str(e)}. Установите: pip install Pillow'}, status=500)

            try:
                import qrcode
            except ImportError as e:
                return JsonResponse({'success': False, 'error': f'qrcode не установлен: {str(e)}. Установите: pip install qrcode'}, status=500)

            # Создаем директорию для карточек
            cards_dir = os.path.join(settings.MEDIA_ROOT, 'product_cards')
            os.makedirs(cards_dir, exist_ok=True)

            # Генерируем карточку
            card_path = self._generate_product_card(product, cards_dir)

            return JsonResponse({
                'success': True,
                'message': 'Карточка товара успешно создана',
                'card_url': os.path.join(settings.MEDIA_URL, 'product_cards', f'card_{product.slug}.png')
            })
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Товар не найден'}, status=404)
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"[ERROR] Failed to generate card: {error_trace}")
            return JsonResponse({'success': False, 'error': f'{str(e)}'}, status=500)

    def _generate_product_card(self, product, output_dir):
        """Генерирует карточку товара (копия логики из команды)"""
        from PIL import Image, ImageDraw, ImageFont
        import qrcode

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
        except:
            pass

        # Название товара (под логотипом, слева)
        y_offset = max(100, logo_height_final + 60)
        name_lines = self._wrap_text(product.name, font_bold, width - 60)
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
            materials_lines = self._wrap_text(product.materials, font_small, width - info_x - 30)
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

        # Сохраняем
        filename = f'card_{product.slug}.png'
        filepath = os.path.join(output_dir, filename)
        card.save(filepath, 'PNG', quality=95)

        return filepath

    def _wrap_text(self, text, font, max_width):
        """Разбивает текст на строки"""
        from PIL import Image, ImageDraw

        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Фильтрация подкатегорий по выбранной категории"""
        if db_field.name == "subcategory":
            # Получаем ID объекта из URL для редактирования
            object_id = request.resolver_match.kwargs.get('object_id')
            if object_id:
                try:
                    product = Product.objects.get(pk=object_id)
                    kwargs["queryset"] = SubCategory.objects.filter(category=product.category)
                except Product.DoesNotExist:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def image_preview(self, obj):
        main_image = obj.get_main_image()
        if main_image:
            return format_html('<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;" />', main_image.image.url)
        return "Нет изображения"
    image_preview.short_description = "Изображение"
    
    def price_formatted(self, obj):
        return format_html('<strong style="color: #20B2AA;">{:,} ₽</strong>'.format(int(obj.price)).replace(',', ' '))
    price_formatted.short_description = "Цена"
    price_formatted.admin_order_field = 'price'
    
    def availability_badge(self, obj):
        colors = {
            'in_stock': '#28a745',
            'on_the_way': '#ffc107',
            'new_2025': '#dc3545',
            'new_arrival': '#17a2b8',
            'best_offer': '#6610f2',
            'online_fitting': '#e83e8c',
        }
        color = colors.get(obj.availability, '#6c757d')
        label = dict(Product.AVAILABILITY_CHOICES).get(obj.availability, obj.availability)
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 500;">{}</span>',
            color, label
        )
    availability_badge.short_description = "Наличие"
    availability_badge.admin_order_field = 'availability'
    
    def is_new_display(self, obj):
        if obj.is_new:
            return format_html('<span style="background: #DC143C; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 500;">NEW</span>')
        return format_html('<span style="color: #999;">—</span>')
    is_new_display.short_description = "Новинка"
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" style="width: 150px; height: 150px;" />', obj.qr_code.url)
        return "QR код будет сгенерирован автоматически при сохранении"
    qr_code_preview.short_description = "Превью QR кода"

    def product_card_preview(self, obj):
        """Показывает превью карточки товара"""
        if obj.pk:
            # Путь к карточке товара
            card_path = os.path.join(settings.MEDIA_ROOT, 'product_cards', f'card_{obj.slug}.png')

            if os.path.exists(card_path):
                card_url = os.path.join(settings.MEDIA_URL, 'product_cards', f'card_{obj.slug}.png')
                return format_html(
                    '<div style="border: 1px solid #ddd; padding: 10px; display: inline-block; border-radius: 4px;">'
                    '<img src="{}" style="max-width: 400px; height: auto; display: block;" />'
                    '<a href="{}" download="card_{}.png" style="display: inline-block; margin-top: 10px; padding: 8px 16px; background: #20B2AA; color: white; text-decoration: none; border-radius: 4px;">📥 Скачать карточку</a>'
                    '</div>',
                    card_url, card_url, obj.slug
                )
            else:
                return format_html(
                    '<div style="color: #999; padding: 10px; border: 1px dashed #ddd; border-radius: 4px;">'
                    'Карточка товара не создана<br>'
                    '<small>Нажмите кнопку "Сгенерировать карточку" ниже</small>'
                    '</div>'
                )
        return "Сохраните товар для создания карточки"
    product_card_preview.short_description = "Карточка товара"

    def generate_card_button(self, obj):
        """Кнопка для генерации карточки товара"""
        if obj.pk:
            return format_html(
                '<button type="button" onclick="generateProductCard({})" '
                'style="padding: 10px 20px; background: #20B2AA; color: white; border: none; '
                'border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500;">'
                '🎴 Сгенерировать карточку товара'
                '</button>'
                '<div id="card-status-{}" style="margin-top: 10px; padding: 10px; border-radius: 4px; display: none;"></div>'
                '<script>'
                'function generateProductCard(productId) {{'
                '  const statusDiv = document.getElementById("card-status-" + productId);'
                '  statusDiv.style.display = "block";'
                '  statusDiv.style.background = "#fff3cd";'
                '  statusDiv.style.color = "#856404";'
                '  statusDiv.innerHTML = "⏳ Генерация карточки...";'
                '  '
                '  fetch("/admin/catalog/product/" + productId + "/generate-card/", {{'
                '    method: "POST",'
                '    headers: {{'
                '      "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value'
                '    }}'
                '  }})'
                '  .then(response => response.json())'
                '  .then(data => {{'
                '    if (data.success) {{'
                '      statusDiv.style.background = "#d4edda";'
                '      statusDiv.style.color = "#155724";'
                '      statusDiv.innerHTML = "✅ Карточка успешно создана! Обновите страницу для просмотра.";'
                '      setTimeout(() => window.location.reload(), 1500);'
                '    }} else {{'
                '      statusDiv.style.background = "#f8d7da";'
                '      statusDiv.style.color = "#721c24";'
                '      statusDiv.innerHTML = "❌ Ошибка: " + data.error;'
                '    }}'
                '  }})'
                '  .catch(error => {{'
                '    statusDiv.style.background = "#f8d7da";'
                '    statusDiv.style.color = "#721c24";'
                '    statusDiv.innerHTML = "❌ Ошибка сети: " + error;'
                '  }});'
                '}}'
                '</script>',
                obj.pk, obj.pk
            )
        return "Сохраните товар для генерации карточки"
    generate_card_button.short_description = "Генерация карточки"

    def view_on_site(self, obj):
        url = obj.get_absolute_url()
        return format_html('<a href="{}" target="_blank" style="color: #20B2AA; font-weight: 500;">👁️ Просмотр</a>', url)
    view_on_site.short_description = "Просмотр"

    class Media:
        css = {
            'all': ('admin/css/admin.css',)
        }


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'phone', 'is_active', 'products_count']
    list_filter = ['is_active']
    search_fields = ['name', 'address', 'phone']
    list_editable = ['is_active']
    list_per_page = 25

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'address', 'phone', 'email'),
        }),
        ('Дополнительно', {
            'fields': ('working_hours', 'is_active'),
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']

    def products_count(self, obj):
        count = obj.stock.count()
        return format_html('<span style="background: #20B2AA; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px;">{} товаров</span>', count)
    products_count.short_description = "Товаров в наличии"


@admin.register(ProductStock)
class ProductStockAdmin(admin.ModelAdmin):
    list_display = ['product', 'store', 'quantity', 'updated_at']
    list_filter = ['store']
    search_fields = ['product__name', 'store__name']
    autocomplete_fields = ['product', 'store']
    list_per_page = 50


@admin.register(ProductRating)
class ProductRatingAdmin(admin.ModelAdmin):
    list_display = ['product', 'rating', 'session_key_short', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['product__name', 'session_key']
    readonly_fields = ['created_at']
    list_per_page = 50

    def session_key_short(self, obj):
        return f"{obj.session_key[:10]}..." if len(obj.session_key) > 10 else obj.session_key
    session_key_short.short_description = "Ключ сессии"

