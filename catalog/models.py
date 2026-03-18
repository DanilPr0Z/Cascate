from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
try:
    from unidecode import unidecode
except ImportError:
    def unidecode(text):
        return text


def transliterate_slugify(text):
    """Транслитерирует русский текст и создает slug"""
    transliterated = unidecode(text)
    return slugify(transliterated)


class Category(models.Model):
    """Главная категория (Мягкая мебель, Столовые, Светильники и т.д.)"""
    name = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL")
    image = models.ImageField(upload_to='categories/', verbose_name="Изображение")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:category_detail', kwargs={'slug': self.slug})

    def get_products_count(self):
        return self.products.count()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = transliterate_slugify(self.name)
        super().save(*args, **kwargs)


class SubCategory(models.Model):
    """Подкатегория (Диваны, Кресла и т.д. в категории Мягкая мебель)"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories', verbose_name="Категория")
    name = models.CharField(max_length=200, verbose_name="Название")
    slug = models.SlugField(max_length=200, verbose_name="URL")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")

    class Meta:
        verbose_name = "Подкатегория"
        verbose_name_plural = "Подкатегории"
        ordering = ['order', 'name']
        unique_together = ['category', 'slug']

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    def get_absolute_url(self):
        return reverse('catalog:subcategory_detail', kwargs={
            'category_slug': self.category.slug,
            'subcategory_slug': self.slug
        })

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = transliterate_slugify(self.name)
        super().save(*args, **kwargs)


class FilterCategory(models.Model):
    """Категория фильтров (Популярные, По стилю, По дизайну и т.д.)"""
    name = models.CharField(max_length=100, verbose_name="Название")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")

    class Meta:
        verbose_name = "Категория фильтров"
        verbose_name_plural = "Категории фильтров"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class FilterValue(models.Model):
    """Значения фильтров (например: Италия, Современный, Угловой и т.д.)"""
    filter_category = models.ForeignKey(FilterCategory, on_delete=models.CASCADE, related_name='values', verbose_name="Категория фильтра")
    name = models.CharField(max_length=200, verbose_name="Значение")
    slug = models.SlugField(max_length=200, verbose_name="URL")

    class Meta:
        verbose_name = "Значение фильтра"
        verbose_name_plural = "Значения фильтров"
        ordering = ['filter_category', 'name']
        unique_together = ['filter_category', 'slug']

    def __str__(self):
        return f"{self.filter_category.name}: {self.name}"


class Product(models.Model):
    """Товар (мебель)"""
    AVAILABILITY_CHOICES = [
        ('in_stock', 'В наличии'),
        ('on_the_way', 'Товар в пути'),
        ('new_2025', 'Новинка 2025 года'),
        ('new_arrival', 'Новое поступление'),
        ('best_offer', 'Лучшее предложение'),
        ('online_fitting', 'Онлайн-примерка'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Категория")
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products', verbose_name="Подкатегория")
    name = models.CharField(max_length=500, verbose_name="Название")
    slug = models.SlugField(max_length=500, unique=True, verbose_name="URL")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена данной модели")
    price_from = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Цена от")
    discount = models.PositiveSmallIntegerField(default=0, verbose_name="Скидка (%)", help_text="От 0 до 99. При ненулевом значении цена отображается красным.")

    # Основная информация
    country = models.CharField(max_length=100, blank=True, verbose_name="Страна")
    materials = models.CharField(max_length=500, blank=True, verbose_name="Материалы")
    dimensions = models.CharField(max_length=200, blank=True, verbose_name="Размеры")
    product_number = models.CharField(max_length=100, blank=True, verbose_name="Номер товара")
    
    # Фильтры
    filter_values = models.ManyToManyField(FilterValue, blank=True, verbose_name="Фильтры")
    
    # Статусы
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, blank=True, null=True, verbose_name="Наличие")
    is_new = models.BooleanField(default=False, verbose_name="Новинка")
    is_popular = models.BooleanField(default=False, verbose_name="Популярный")
    
    # Описание
    description = models.TextField(blank=True, verbose_name="Описание")
    short_description = models.CharField(max_length=500, blank=True, verbose_name="Краткое описание")

    # 3D тур
    tour_3d_url = models.URLField(blank=True, verbose_name="Ссылка на 3D тур")

    # QR код
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True, verbose_name="QR код")

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.IntegerField(default=0, verbose_name="Количество просмотров")

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

    @property
    def discounted_price(self):
        """Цена с учётом скидки. None если скидка не задана."""
        if self.discount and self.discount > 0:
            return self.price * (100 - self.discount) / 100
        return None

    def get_main_image(self):
        """Возвращает главное изображение товара"""
        return self.images.filter(is_main=True).first() or self.images.first()

    def get_average_rating(self):
        """Возвращает средний рейтинг товара"""
        from django.db.models import Avg
        avg = self.ratings.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0

    def get_ratings_count(self):
        """Возвращает количество оценок"""
        return self.ratings.count()

    def get_user_rating(self, session_key):
        """Возвращает оценку пользователя"""
        rating = self.ratings.filter(session_key=session_key).first()
        return rating.rating if rating else 0

    def clean(self):
        """Валидация: подкатегория должна принадлежать выбранной категории"""
        if self.subcategory and self.category:
            if self.subcategory.category != self.category:
                raise ValidationError({
                    'subcategory': f'Подкатегория "{self.subcategory.name}" не принадлежит категории "{self.category.name}"'
                })

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = transliterate_slugify(self.name)
            slug = base_slug

            # Если slug уже существует, добавляем product_number или счетчик
            if Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                if self.product_number:
                    slug = f"{base_slug}-{transliterate_slugify(self.product_number)}"
                else:
                    counter = 1
                    while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1

            self.slug = slug

        # Автоматически исправляем несоответствие категории и подкатегории
        if self.subcategory and self.subcategory.category != self.category:
            self.category = self.subcategory.category
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """Изображения товара"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Товар")
    image = models.ImageField(upload_to='products/', verbose_name="Изображение")
    is_main = models.BooleanField(default=False, verbose_name="Главное изображение")
    order = models.IntegerField(default=0, verbose_name="Порядок отображения")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="Альтернативный текст")

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товаров"
        ordering = ['is_main', 'order']

    def __str__(self):
        return f"{self.product.name} - изображение {self.order}"

    def save(self, *args, **kwargs):
        # Если это главное изображение, убираем флаг главного у других
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).exclude(id=self.id).update(is_main=False)
        super().save(*args, **kwargs)


class Store(models.Model):
    """Магазин/Салон"""
    name = models.CharField(max_length=200, verbose_name="Название магазина")
    address = models.CharField(max_length=500, verbose_name="Адрес")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    working_hours = models.CharField(max_length=200, blank=True, verbose_name="Часы работы")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Магазины"
        ordering = ['name']

    def __str__(self):
        return self.address


class ProductStock(models.Model):
    """Наличие товара в магазине"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock', verbose_name="Товар")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stock', verbose_name="Магазин")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Остаток товара"
        verbose_name_plural = "Остатки товаров"
        unique_together = ['product', 'store']
        ordering = ['store', 'product']

    def __str__(self):
        return f"{self.product.name} - {self.store.name}: {self.quantity} шт."


class ProductRating(models.Model):
    """Рейтинг товара"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings', verbose_name="Товар")
    session_key = models.CharField(max_length=40, verbose_name="Ключ сессии")
    rating = models.PositiveSmallIntegerField(verbose_name="Оценка", choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Рейтинг товара"
        verbose_name_plural = "Рейтинги товаров"
        unique_together = ['product', 'session_key']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.rating} звезд"

