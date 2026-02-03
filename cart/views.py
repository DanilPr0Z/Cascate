from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Cart, CartItem
from catalog.models import Product


@login_required
def cart_view(request):
    """Страница корзины"""
    print(f"[DEBUG] cart_view called: user={request.user}")

    cart, created = Cart.objects.get_or_create(user=request.user)
    print(f"[DEBUG] Cart: id={cart.id}, created={created}")

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


@login_required
@require_POST
def add_to_cart(request, product_id):
    """AJAX: Добавить товар в корзину"""
    print(f"[DEBUG] add_to_cart called: product_id={product_id}, user={request.user}")

    product = get_object_or_404(Product, id=product_id)
    print(f"[DEBUG] Product found: {product.name}")

    cart, created = Cart.objects.get_or_create(user=request.user)
    print(f"[DEBUG] Cart: id={cart.id}, created={created}")

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


@login_required
@require_POST
def remove_from_cart(request, item_id):
    """AJAX: Удалить товар из корзины"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart = cart_item.cart
    cart_item.delete()

    return JsonResponse({
        'success': True,
        'cart_count': cart.get_total_items(),
        'total_price': float(cart.get_total_price()),
    })


@login_required
@require_POST
def update_quantity(request, item_id):
    """AJAX: Изменить количество товара"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))

    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        item_total = float(cart_item.get_total_price())
    else:
        cart_item.delete()
        item_total = 0

    cart = Cart.objects.get(user=request.user)

    return JsonResponse({
        'success': True,
        'item_total': item_total,
        'cart_count': cart.get_total_items(),
        'total_price': float(cart.get_total_price()),
    })
