from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Category, SubCategory, Product, ProductImage, FilterCategory, FilterValue, Store, ProductStock, ProductRating


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

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'category', 'subcategory', 'price'),
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
        ('QR код', {
            'fields': ('qr_code', 'qr_code_preview'),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': ('created_at', 'updated_at', 'views_count'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at', 'views_count', 'image_preview', 'qr_code_preview']

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

