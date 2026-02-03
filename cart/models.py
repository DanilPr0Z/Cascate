from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product


class Cart(models.Model):
    """Корзина пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', verbose_name="Пользователь")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлена")

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"Корзина {self.user.username}"

    def get_total_price(self):
        """Общая стоимость всех товаров в корзине"""
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        """Общее количество товаров"""
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    """Товар в корзине"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name="Корзина")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлен")

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"
        unique_together = ['cart', 'product']  # Один товар - одна запись

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def get_total_price(self):
        """Стоимость этой позиции"""
        return self.product.price * self.quantity
